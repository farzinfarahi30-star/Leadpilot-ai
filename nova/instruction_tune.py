import argparse,json,random,os
from pathlib import Path
import torch
from nova_ai.model import NovaLM,NovaConfig
from nova_ai.tokenizer import BPETokenizer

def rows(p):
 out=[]
 for line in open(p,encoding='utf-8'):
  r=json.loads(line); i=str(r.get('instruction','')).strip(); o=str(r.get('response','')).strip()
  if i and o: out.append((i,o))
 if not out: raise ValueError('No valid instruction rows')
 return out

def save_atomic(path,payload):
 path=Path(path); path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix(path.suffix+'.tmp'); torch.save(payload,tmp); os.replace(tmp,path)

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--checkpoint',required=True); ap.add_argument('--data',required=True); ap.add_argument('--steps',type=int,default=1500); ap.add_argument('--lr',type=float,default=1e-5); ap.add_argument('--out',default='checkpoints/nova-instruct.pt'); ap.add_argument('--checkpoint-every',type=int,default=100); a=ap.parse_args()
 base=torch.load(a.checkpoint,map_location='cpu'); cfg=dict(base['config']); cfg.setdefault('n_kv_head',min(4,int(cfg.get('n_head',8)))); C=NovaConfig(**cfg); tok=BPETokenizer.load(base['tokenizer']); data=rows(a.data); dev=torch.device('cuda' if torch.cuda.is_available() else 'cpu')
 src=int(base.get('step',0)); out=Path(a.out); ck=torch.load(out,map_location='cpu') if out.exists() else None; start=0
 if ck and ck.get('base_step')==src:
  model=NovaLM(C); model.load_state_dict(ck['model']); start=int(ck.get('step',0))
  if start>=a.steps: print(f'already complete {a.out}'); return
 else: model=NovaLM(C); model.load_state_dict(base['model'])
 model.to(dev); opt=torch.optim.AdamW(model.parameters(),lr=a.lr,betas=(.9,.95),weight_decay=.01)
 if ck and ck.get('base_step')==src and 'optimizer' in ck: opt.load_state_dict(ck['optimizer'])
 model.train()
 for step in range(start+1,a.steps+1):
  ins,res=random.choice(data); p=tok.encode(f'User: {ins}\nAssistant:'); r=tok.encode(' '+res); keep_r=min(len(r),max(2,model.block_size-2)); keep_p=min(len(p),max(1,model.block_size-keep_r-1)); ids=p[-keep_p:]+r[:keep_r]; x=torch.tensor(ids[:-1],dtype=torch.long,device=dev)[None,:]; y=torch.tensor(ids[1:],dtype=torch.long,device=dev)[None,:]; y[:,:max(0,keep_p-1)]=-100
  _,loss=model(x,y); opt.zero_grad(set_to_none=True); loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(),1.0); opt.step()
  if step==1 or step%100==0 or step==a.steps: print(f'SFT step={step}/{a.steps} loss={loss.item():.4f}',flush=True)
  if step%a.checkpoint_every==0 or step==a.steps: save_atomic(out,{'model':model.state_dict(),'config':dict(C.__dict__),'tokenizer':base['tokenizer'],'step':step,'base_step':src,'optimizer':opt.state_dict()})
if __name__=='__main__': main()
