import argparse,json,random,os
from pathlib import Path
import torch
import torch.nn.functional as F
from nova_ai.model import NovaLM,NovaConfig
from nova_ai.tokenizer import BPETokenizer

def rows(path):
 out=[]
 for line in Path(path).read_text(encoding='utf-8').splitlines():
  if not line.strip(): continue
  r=json.loads(line); p=str(r.get('prompt','')).strip(); c=str(r.get('chosen','')).strip(); x=str(r.get('rejected','')).strip()
  if p and c and x: out.append((p,c,x))
 if not out: raise ValueError('No valid preference rows')
 return out

def score(model,tok,prompt,response):
 p=tok.encode(prompt); r=tok.encode(' '+response); kr=min(len(r),max(2,model.block_size-2)); kp=min(len(p),max(1,model.block_size-kr-1)); ids=p[-kp:]+r[:kr]
 x=torch.tensor(ids[:-1],dtype=torch.long,device=next(model.parameters()).device)[None,:]; y=torch.tensor(ids[1:],dtype=torch.long,device=x.device)[None,:]; logits,_=model(x); lp=F.log_softmax(logits,-1).gather(-1,y[...,None]).squeeze(-1); tail=lp[:,max(0,min(kp-1,lp.size(1))):]
 return tail.mean() if tail.numel() else lp.mean()

def save(path,payload):
 path=Path(path); path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix('.pt.tmp'); torch.save(payload,tmp); os.replace(tmp,path)

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--checkpoint',required=True); ap.add_argument('--data',required=True); ap.add_argument('--steps',type=int,default=400); ap.add_argument('--lr',type=float,default=5e-6); ap.add_argument('--beta',type=float,default=.1); ap.add_argument('--out',default='checkpoints/nova-preference.pt'); ap.add_argument('--checkpoint-every',type=int,default=50); a=ap.parse_args()
 base=torch.load(a.checkpoint,map_location='cpu'); cfg=dict(base['config']); cfg.setdefault('n_kv_head',min(4,int(cfg.get('n_head',8)))); C=NovaConfig(**cfg); tok=BPETokenizer.load(base['tokenizer']); data=rows(a.data); dev=torch.device('cuda' if torch.cuda.is_available() else 'cpu'); src=int(base.get('step',0)); out=Path(a.out); ck=torch.load(out,map_location='cpu') if out.exists() else None; start=0
 if ck and ck.get('base_step')==src:
  model=NovaLM(C); model.load_state_dict(ck['model']); start=int(ck.get('step',0));
  if start>=a.steps: print(f'already complete {a.out}'); return
 else: model=NovaLM(C); model.load_state_dict(base['model'])
 model.to(dev); opt=torch.optim.AdamW(model.parameters(),lr=a.lr,betas=(.9,.95),weight_decay=.01)
 if ck and ck.get('base_step')==src and 'optimizer' in ck: opt.load_state_dict(ck['optimizer'])
 model.train()
 for step in range(start+1,a.steps+1):
  p,c,r=random.choice(data); sc,sr=score(model,tok,p,c),score(model,tok,p,r); loss=-F.logsigmoid(a.beta*(sc-sr)); opt.zero_grad(set_to_none=True); loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(),1.0); opt.step()
  if step==1 or step%100==0 or step==a.steps: print(f'PREF step={step}/{a.steps} loss={loss.item():.4f}',flush=True)
  if step%a.checkpoint_every==0 or step==a.steps: save(out,{'model':model.state_dict(),'config':dict(C.__dict__),'tokenizer':base['tokenizer'],'step':step,'base_step':src,'optimizer':opt.state_dict(),'preference_beta':a.beta})
if __name__=='__main__': main()
