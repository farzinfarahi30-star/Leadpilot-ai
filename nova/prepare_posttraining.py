import argparse,json
from pathlib import Path

def load_stream(name,split='train',config=None):
 from datasets import load_dataset
 kw={'split':split,'streaming':True}
 if config: kw['name']=config
 return load_dataset(name,**kw)

def write_row(f,instruction,response):
 if instruction and response:
  f.write(json.dumps({'instruction':instruction.strip(),'response':response.strip()},ensure_ascii=False)+'\n'); return 1
 return 0

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--out-dir',default='data'); ap.add_argument('--oasst-limit',type=int,default=50000); ap.add_argument('--math-limit',type=int,default=30000); ap.add_argument('--code-limit',type=int,default=20000); ap.add_argument('--pref-limit',type=int,default=20000); a=ap.parse_args(); out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
 ds=load_stream('OpenAssistant/oasst1'); messages={}; children={}
 for row in ds:
  mid=row.get('message_id'); pid=row.get('parent_id')
  if not mid or row.get('deleted') or row.get('review_result') is False: continue
  text=str(row.get('text') or '').strip()
  if not text: continue
  messages[mid]=row
  if pid: children.setdefault(pid,[]).append(mid)
 inst=out/'instructions_hf.jsonl'; pref=out/'preferences_hf.jsonl'
 with inst.open('w',encoding='utf-8') as fi,pref.open('w',encoding='utf-8') as fp:
  count=0
  for mid,row in messages.items():
   if count>=a.oasst_limit: break
   if row.get('role')!='assistant' or not row.get('parent_id'): continue
   parent=messages.get(row['parent_id'])
   if parent and parent.get('role')=='prompter': count+=write_row(fi,f"User: {parent['text']}",row['text'])
  pcount=0
  for pid,kids in children.items():
   if pcount>=a.pref_limit: break
   parent=messages.get(pid)
   if not parent or parent.get('role')!='prompter': continue
   ranked=[messages[k] for k in kids if k in messages and messages[k].get('role')=='assistant' and messages[k].get('rank') is not None]; ranked.sort(key=lambda r:int(r.get('rank',999999)))
   if len(ranked)>=2 and ranked[0]['text']!=ranked[-1]['text']:
    fp.write(json.dumps({'prompt':parent['text'],'chosen':ranked[0]['text'],'rejected':ranked[-1]['text']},ensure_ascii=False)+'\n'); pcount+=1
 math_out=out/'math_instructions.jsonl'; m=0; ds=load_stream('nvidia/OpenMathInstruct-2',split='train_1M')
 with math_out.open('w',encoding='utf-8') as f:
  for row in ds:
   if m>=a.math_limit: break
   m+=write_row(f,'Solve this math problem carefully and give the final answer.\n'+str(row.get('problem') or ''),str(row.get('generated_solution') or ''))
 code_out=out/'code_reasoning.jsonl'; c=0; ds=load_stream('open-r1/codeforces-cots')
 with code_out.open('w',encoding='utf-8') as f:
  for row in ds:
   if c>=a.code_limit: break
   c+=write_row(f,'Solve this competitive-programming problem. Explain the algorithm, correctness, complexity, and implementation.\n'+str(row.get('prompt') or ''),str(row.get('generation') or ''))
 merged=out/'instructions_all.jsonl'; total=0
 with merged.open('w',encoding='utf-8') as dst:
  for source in [inst,math_out,code_out,out/'instructions.jsonl']:
   if source.exists():
    for line in source.open(encoding='utf-8'): dst.write(line); total+=1
 print(json.dumps({'oasst_instruction':count,'oasst_preference':pcount,'math':m,'code_reasoning':c,'merged_rows':total}))
if __name__=='__main__': main()
