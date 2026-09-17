import math
from dataclasses import dataclass
import torch
import torch.nn as nn
import torch.nn.functional as F

@dataclass
class NovaConfig:
    vocab_size: int = 8192
    block_size: int = 1024
    n_layer: int = 8
    n_head: int = 8
    n_kv_head: int = 4
    n_embd: int = 512
    dropout: float = 0.0
    bias: bool = False
    rope_base: float = 10000.0

class RMSNorm(nn.Module):
    def __init__(self, dim, eps=1e-6):
        super().__init__(); self.weight=nn.Parameter(torch.ones(dim)); self.eps=eps
    def forward(self,x): return self.weight * (x * torch.rsqrt(x.float().pow(2).mean(-1,keepdim=True)+self.eps)).type_as(x)

def rotate_half(x):
    x1,x2=x.chunk(2,dim=-1); return torch.cat((-x2,x1),dim=-1)

def apply_rope(q,k,cos,sin):
    q=(q*cos)+(rotate_half(q)*sin); k=(k*cos)+(rotate_half(k)*sin); return q,k

class CausalSelfAttention(nn.Module):
    def __init__(self,cfg):
        super().__init__(); kv_heads=min(cfg.n_kv_head,cfg.n_head); assert cfg.n_embd%cfg.n_head==0 and cfg.n_head%kv_heads==0 and (cfg.n_embd//cfg.n_head)%2==0
        self.n_head=cfg.n_head; self.n_kv_head=kv_heads; self.head_dim=cfg.n_embd//cfg.n_head
        qdim=cfg.n_head*self.head_dim; kvdim=self.n_kv_head*self.head_dim
        self.q_proj=nn.Linear(cfg.n_embd,qdim,bias=cfg.bias); self.k_proj=nn.Linear(cfg.n_embd,kvdim,bias=cfg.bias); self.v_proj=nn.Linear(cfg.n_embd,kvdim,bias=cfg.bias)
        self.proj=nn.Linear(cfg.n_embd,cfg.n_embd,bias=cfg.bias); self.drop=nn.Dropout(cfg.dropout); self.rope_base=cfg.rope_base
        inv_freq=1.0/(cfg.rope_base**(torch.arange(0,self.head_dim,2).float()/self.head_dim))
        self.register_buffer('inv_freq',inv_freq,persistent=False)
    def forward(self,x):
        b,t,c=x.shape
        q=self.q_proj(x).view(b,t,self.n_head,self.head_dim).transpose(1,2)
        k=self.k_proj(x).view(b,t,self.n_kv_head,self.head_dim).transpose(1,2)
        v=self.v_proj(x).view(b,t,self.n_kv_head,self.head_dim).transpose(1,2)
        pos=torch.arange(t,device=x.device,dtype=self.inv_freq.dtype)
        freqs=torch.outer(pos,self.inv_freq)
        emb=torch.cat((freqs,freqs),dim=-1)[None,None,:,:]
        cos,sin=emb.cos().to(x.dtype),emb.sin().to(x.dtype)
        q,k=apply_rope(q,k,cos,sin)
        dropout_p = self.drop.p if self.training else 0.0
        if self.n_kv_head != self.n_head:
            try:
                y = F.scaled_dot_product_attention(q, k, v, is_causal=True, dropout_p=dropout_p, enable_gqa=True)
            except (TypeError, RuntimeError):
                repeat = self.n_head // self.n_kv_head
                k = k.repeat_interleave(repeat, dim=1)
                v = v.repeat_interleave(repeat, dim=1)
                y = F.scaled_dot_product_attention(q, k, v, is_causal=True, dropout_p=dropout_p)
        else:
            y = F.scaled_dot_product_attention(q, k, v, is_causal=True, dropout_p=dropout_p)
        y=y.transpose(1,2).contiguous().view(b,t,c); return self.drop(self.proj(y))

class SwiGLU(nn.Module):
    def __init__(self,dim,bias=False,dropout=0.0):
        super().__init__(); hidden=64*math.ceil(((8*dim)//3)/64)
        self.w1=nn.Linear(dim,hidden,bias=bias); self.w2=nn.Linear(dim,hidden,bias=bias); self.w3=nn.Linear(hidden,dim,bias=bias); self.drop=nn.Dropout(dropout)
    def forward(self,x): return self.drop(self.w3(F.silu(self.w1(x))*self.w2(x)))

class Block(nn.Module):
    def __init__(self,cfg):
        super().__init__(); self.n1=RMSNorm(cfg.n_embd); self.attn=CausalSelfAttention(cfg); self.n2=RMSNorm(cfg.n_embd); self.mlp=SwiGLU(cfg.n_embd,cfg.bias,cfg.dropout)
    def forward(self,x): x=x+self.attn(self.n1(x)); return x+self.mlp(self.n2(x))

class NovaLM(nn.Module):
    def __init__(self,cfg=None,**kwargs):
        super().__init__(); self.cfg=cfg or NovaConfig(**kwargs); c=self.cfg; self.block_size=c.block_size; self.use_gradient_checkpointing=False
        self.token_emb=nn.Embedding(c.vocab_size,c.n_embd); self.blocks=nn.ModuleList([Block(c) for _ in range(c.n_layer)]); self.ln_f=RMSNorm(c.n_embd); self.lm_head=nn.Linear(c.n_embd,c.vocab_size,bias=False); self.lm_head.weight=self.token_emb.weight
        self.drop=nn.Dropout(c.dropout); self.apply(self._init)
        for n,p in self.named_parameters():
            if n.endswith('proj.weight'): nn.init.normal_(p,0.0,0.02/math.sqrt(2*c.n_layer))
    def _init(self,m):
        if isinstance(m,(nn.Linear,nn.Embedding)):
            nn.init.normal_(m.weight,0.0,0.02)
            if getattr(m,'bias',None) is not None: nn.init.zeros_(m.bias)
    def num_parameters(self): return sum(p.numel() for p in self.parameters())
    def forward(self,idx,targets=None):
        b,t=idx.shape
        if t>self.block_size: raise ValueError(f'sequence length {t} > block size {self.block_size}')
        x=self.drop(self.token_emb(idx))
        for block in self.blocks:
            if self.training and self.use_gradient_checkpointing:
                x = torch.utils.checkpoint.checkpoint(block, x, use_reentrant=False)
            else:
                x = block(x)
        logits=self.lm_head(self.ln_f(x)); loss=None
        if targets is not None: loss=F.cross_entropy(logits.reshape(-1,logits.size(-1)),targets.reshape(-1))
        return logits,loss
    @torch.no_grad()
    def generate(self,idx,max_new_tokens,temperature=0.8,top_k=50):
        self.eval()
        for _ in range(max_new_tokens):
            logits,_=self(idx[:,-self.block_size:]); logits=logits[:,-1,:]/max(float(temperature),1e-5)
            if top_k:
                v,_=torch.topk(logits,min(top_k,logits.size(-1))); logits[logits<v[:,-1,None]]=-float('inf')
            idx=torch.cat((idx,torch.multinomial(F.softmax(logits,dim=-1),1)),dim=1)
        return idx
