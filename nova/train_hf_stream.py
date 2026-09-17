import argparse, math, os, random, signal, time
from pathlib import Path
import torch
import torch.distributed as dist
from nova_ai.model import NovaLM, NovaConfig
from nova_ai.tokenizer import BPETokenizer

def load_stream(name, split, config=None):
    from datasets import load_dataset
    kw={"split":split,"streaming":True}
    if config: kw["name"]=config
    return load_dataset(name,**kw)

def init_dist():
    world=int(os.environ.get("WORLD_SIZE","1"))
    if world>1 and not dist.is_initialized(): dist.init_process_group("nccl" if torch.cuda.is_available() else "gloo")
    return (dist.get_rank() if dist.is_initialized() else 0),world

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--dataset',default='HuggingFaceFW/fineweb_100BT'); ap.add_argument('--split',default='train'); ap.add_argument('--config',default=None); ap.add_argument('--tokenizer-samples',type=int,default=50000); ap.add_argument('--steps',type=int,default=1526); ap.add_argument('--block-size',type=int,default=1024); ap.add_argument('--layers',type=int,default=8); ap.add_argument('--heads',type=int,default=8); ap.add_argument('--kv-heads',type=int,default=4); ap.add_argument('--embd',type=int,default=512); ap.add_argument('--vocab-size',type=int,default=8192); ap.add_argument('--batch-size',type=int,default=2); ap.add_argument('--grad-accum',type=int,default=16); ap.add_argument('--lr',type=float,default=3e-4); ap.add_argument('--weight-decay',type=float,default=0.1); ap.add_argument('--warmup-steps',type=int,default=200); ap.add_argument('--min-lr-ratio',type=float,default=.1); ap.add_argument('--checkpoint-every',type=int,default=50); ap.add_argument('--max-seconds',type=int,default=39000); ap.add_argument('--tokenizer-chars',type=int,default=5000000); ap.add_argument('--out',default='checkpoints/nova-stream.pt'); ap.add_argument('--resume',default=''); ap.add_argument('--seed',type=int,default=1337); ap.add_argument('--grad-checkpoint',action='store_true'); a=ap.parse_args()
    rank,world=init_dist(); local_rank=int(os.environ.get('LOCAL_RANK','0')); dev=torch.device(f'cuda:{local_rank}' if torch.cuda.is_available() else 'cpu')
    if dev.type=='cuda': torch.cuda.set_device(local_rank); torch.backends.cuda.matmul.allow_tf32=True; torch.backends.cudnn.benchmark=True
    random.seed(a.seed+rank); torch.manual_seed(a.seed+rank); out=Path(a.out); tok_path=out.with_suffix('.tokenizer.json'); resume=torch.load(a.resume,map_location='cpu') if a.resume else None
    if resume and resume.get('tokenizer') and Path(resume['tokenizer']).exists(): tok_path=Path(resume['tokenizer'])
    if tok_path.exists(): tok=BPETokenizer.load(tok_path)
    else:
        texts=[]; chars=0
        if rank==0:
            ds=load_stream(a.dataset,a.split,a.config)
            for row in ds:
                t=str(row.get('text') or row.get('content') or '').strip()
                if len(t)<32: continue
                remain=max(0,a.tokenizer_chars-chars)
                if remain<=0: break
                texts.append(t[:remain]); chars+=min(len(t),remain)
                if chars>=a.tokenizer_chars: break
            tok=BPETokenizer(a.vocab_size).train('\n\n'.join(texts)); tok.save(tok_path); print(f'tokenizer trained: {chars:,} chars',flush=True)
        if dist.is_initialized(): dist.barrier()
        tok=BPETokenizer.load(tok_path)
    cfg=NovaConfig(vocab_size=tok.size,block_size=a.block_size,n_layer=a.layers,n_head=a.heads,n_kv_head=min(a.kv_heads,a.heads),n_embd=a.embd); model=NovaLM(cfg).to(dev)
    if world>1: model=torch.nn.parallel.DistributedDataParallel(model,device_ids=[local_rank] if dev.type=='cuda' else None)
    raw=model.module if hasattr(model,'module') else model; raw.use_gradient_checkpointing=a.grad_checkpoint; kw=dict(lr=a.lr,betas=(.9,.95),weight_decay=a.weight_decay)
    try: opt=torch.optim.AdamW(raw.parameters(),fused=True,**kw) if dev.type=='cuda' else torch.optim.AdamW(raw.parameters(),**kw)
    except Exception: opt=torch.optim.AdamW(raw.parameters(),**kw)
    scaler=torch.amp.GradScaler('cuda',enabled=dev.type=='cuda'); start=0; seen=0
    if resume: raw.load_state_dict(resume['model']); opt.load_state_dict(resume['optimizer']); start=int(resume.get('step',0)); seen=int(resume.get('samples_seen',0)); print(f'resumed step={start}',flush=True)
    def stream(start_idx):
        ds=load_stream(a.dataset,a.split,a.config); idx=0
        for row in ds:
            t=str(row.get('text') or row.get('content') or '').strip()
            if len(t)<32: continue
            if idx<start_idx: idx+=1; continue
            if idx%world==rank: yield t
            idx+=1
    documents=stream(seen); started=time.time(); stop=False
    def stopit(*_):
        nonlocal stop; stop=True
    signal.signal(signal.SIGTERM,stopit); signal.signal(signal.SIGINT,stopit)
    def nextdoc():
        nonlocal documents
        while True:
            try: t=next(documents)
            except StopIteration: documents=stream(seen); t=next(documents)
            ids=tok.encode(t,add_eos=True)
            if len(ids)>=a.block_size+1: return torch.tensor(ids,dtype=torch.long)
    def batch():
        xs=[]; ys=[]
        while len(xs)<a.batch_size:
            ids=nextdoc(); st=random.randint(0,len(ids)-a.block_size-1); xs.append(ids[st:st+a.block_size]); ys.append(ids[st+1:st+a.block_size+1])
        return torch.stack(xs),torch.stack(ys)
    def lr(step):
        if step<=a.warmup_steps: return a.lr*step/max(1,a.warmup_steps)
        p=(step-a.warmup_steps)/max(1,a.steps-a.warmup_steps); c=.5*(1+math.cos(math.pi*min(1,max(0,p)))); return a.lr*(a.min_lr_ratio+(1-a.min_lr_ratio)*c)
    def save(step,loss):
        nonlocal seen
        if rank!=0: return
        out.parent.mkdir(parents=True,exist_ok=True); tmp=out.with_suffix('.pt.tmp'); torch.save({'model':raw.state_dict(),'config':dict(cfg.__dict__),'tokenizer':str(tok_path),'step':step,'optimizer':opt.state_dict(),'train_loss':loss,'samples_seen':seen,'dataset':a.dataset,'split':a.split,'world_size':world},tmp); os.replace(tmp,out); print(f'checkpoint saved step={step} samples_seen={seen}',flush=True)
    raw.train()
    for step in range(start+1,a.steps+1):
        if time.time()-started>=a.max_seconds: break
        xlr=lr(step)
        for pg in opt.param_groups: pg['lr']=xlr
        opt.zero_grad(set_to_none=True); total=0.0
        for _ in range(a.grad_accum):
            x,y=batch(); x=x.to(dev,non_blocking=True); y=y.to(dev,non_blocking=True)
            with torch.autocast(device_type=dev.type,dtype=torch.float16,enabled=dev.type=='cuda'):
                _,loss=model(x,y); loss=loss/a.grad_accum
            scaler.scale(loss).backward(); total+=loss.item()
        scaler.unscale_(opt); torch.nn.utils.clip_grad_norm_(raw.parameters(),1.0); scaler.step(opt); scaler.update(); seen+=a.batch_size*a.grad_accum*world
        if step==1 or step%a.checkpoint_every==0 or step==a.steps: save(step,total); print(f'step={step}/{a.steps} loss={total:.4f} device={dev}',flush=True)
        if stop or time.time()-started>=a.max_seconds: save(step,total); break
    if dist.is_initialized(): dist.barrier(); dist.destroy_process_group()
if __name__=='__main__': main()
