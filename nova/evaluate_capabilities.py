import argparse, json, re
from pathlib import Path
import torch
from nova_ai.model import NovaLM, NovaConfig
from nova_ai.tokenizer import BPETokenizer

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--checkpoint',required=True); ap.add_argument('--data',default='data/reasoning.jsonl'); a=ap.parse_args()
    ck=torch.load(a.checkpoint,map_location='cpu'); cfg=dict(ck['config']); cfg.setdefault('n_kv_head',min(4,int(cfg.get('n_head',8)))); C=NovaConfig(**cfg); model=NovaLM(C); model.load_state_dict(ck['model']); tok=BPETokenizer.load(ck['tokenizer']); model.eval()
    rows=[json.loads(x) for x in Path(a.data).read_text(encoding='utf-8').splitlines() if x.strip()]; exact=0
    for r in rows:
        prompt='User: '+r['prompt']+'\nAssistant:'; ids=torch.tensor(tok.encode(prompt),dtype=torch.long)[None,:]
        out=model.generate(ids,min(48,max(8,model.block_size-len(ids[0]))),temperature=0.0,top_k=1)
        decoded=tok.decode(out[0].tolist()); text=decoded.split('Assistant:',1)[-1].strip() if 'Assistant:' in decoded else decoded.strip(); ok=re.sub(r'[^a-z0-9]+',' ',text.lower()).strip().startswith(re.sub(r'[^a-z0-9]+',' ',r['answer'].lower()).strip())
        exact += int(ok); print(r['category'], 'PASS' if ok else 'MISS', '=>', repr(text[:120]))
    print(f'accuracy={exact}/{len(rows)}={exact/len(rows):.1%}')
if __name__=='__main__': main()
