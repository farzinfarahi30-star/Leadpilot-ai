from collections import Counter
import json
from pathlib import Path

class BPETokenizer:
    """Byte-level BPE tokenizer with optional fast Rust backend."""
    def __init__(self, vocab_size=8192, merges=None, specials=None, backend="auto"):
        self.base=256; self.vocab_size=int(vocab_size); self.merges=merges or []
        self.specials=specials or {"<pad>":0,"<bos>":1,"<eos>":2,"<unk>":3}
        self.ranks={tuple(x):i for i,x in enumerate(self.merges)}; self._backend="python"; self._hf=None; self._special_ids={}
        if backend=="auto":
            try:
                import tokenizers  # noqa: F401
                self._backend="hf"
            except Exception: pass
        elif backend in {"hf","python"}: self._backend=backend
    @property
    def size(self):
        return len(self._hf.get_vocab()) if self._backend=="hf" and self._hf is not None else self.base+len(self.merges)+len(self.specials)
    def _train_python(self,text,min_frequency=2):
        seqs=[list(s.encode("utf-8")) for s in text.splitlines(True) if s]; limit=max(0,self.vocab_size-self.base-len(self.specials))
        for _ in range(limit):
            c=Counter();
            for s in seqs: c.update(zip(s,s[1:]))
            if not c: break
            pair,freq=c.most_common(1)[0]
            if freq<min_frequency: break
            self.merges.append([int(pair[0]),int(pair[1])]); nid=self.base+len(self.merges)-1
            for j,s in enumerate(seqs):
                o=[]; i=0
                while i<len(s):
                    if i+1<len(s) and (s[i],s[i+1])==pair: o.append(nid); i+=2
                    else: o.append(s[i]); i+=1
                seqs[j]=o
        self.ranks={tuple(x):i for i,x in enumerate(self.merges)}; self._backend="python"; return self
    def _train_hf(self,texts,min_frequency=2):
        from tokenizers import Tokenizer,decoders,models,pre_tokenizers,trainers
        tok=Tokenizer(models.BPE(unk_token="<unk>")); tok.pre_tokenizer=pre_tokenizers.ByteLevel(add_prefix_space=False); tok.decoder=decoders.ByteLevel()
        trainer=trainers.BpeTrainer(vocab_size=self.vocab_size,min_frequency=min_frequency,special_tokens=["<pad>","<bos>","<eos>","<unk>"],initial_alphabet=pre_tokenizers.ByteLevel.alphabet(),show_progress=False)
        tok.train_from_iterator(texts,trainer=trainer); self._hf=tok; self._special_ids={n:int(tok.token_to_id(n)) for n in self.specials if tok.token_to_id(n) is not None}; self._backend="hf"; return self
    def train(self,text,min_frequency=2):
        if self._backend=="hf":
            try: return self._train_hf((s for s in text.splitlines(True) if s),min_frequency)
            except Exception: self._hf=None; self._backend="python"
        return self._train_python(text,min_frequency)
    def encode(self,text,add_bos=False,add_eos=False):
        if self._backend=="hf" and self._hf is not None:
            ids=list(self._hf.encode(text,add_special_tokens=False).ids)
            if add_bos and self._special_ids.get("<bos>") is not None: ids.insert(0,self._special_ids["<bos>"])
            if add_eos and self._special_ids.get("<eos>") is not None: ids.append(self._special_ids["<eos>"])
            return ids
        ids=list(text.encode("utf-8"))
        for mi,(a,b) in enumerate(self.merges):
            nid=self.base+mi; out=[]; i=0
            while i<len(ids):
                if i+1<len(ids) and (ids[i],ids[i+1])==(a,b): out.append(nid); i+=2
                else: out.append(ids[i]); i+=1
            ids=out
        off=self.base+len(self.merges)
        if add_bos: ids=[off+self.specials["<bos>"]]+ids
        if add_eos: ids=ids+[off+self.specials["<eos>"]]
        return ids
    def _expand(self,x):
        if isinstance(x,int): return [x] if x<self.base else self._expand(self.merges[x-self.base])
        a,b=x; return self._expand(a)+self._expand(b)
    def decode(self,ids):
        if self._backend=="hf" and self._hf is not None:
            skip=set(self._special_ids.values()); return self._hf.decode([int(i) for i in ids if int(i) not in skip],skip_special_tokens=True)
        off=self.base+len(self.merges); raw=[]
        for i in ids:
            if i>=off: continue
            raw.extend(self._expand(int(i)))
        return bytes(raw).decode("utf-8",errors="replace")
    def save(self,p):
        path=Path(p); path.parent.mkdir(parents=True,exist_ok=True)
        if self._backend=="hf" and self._hf is not None:
            payload={"engine":"huggingface-tokenizers","vocab_size":self.vocab_size,"specials":self.specials,"special_ids":self._special_ids,"tokenizer_json":self._hf.to_str()}
        else: payload={"engine":"python-byte-bpe","vocab_size":self.vocab_size,"merges":self.merges,"specials":self.specials}
        path.write_text(json.dumps(payload,ensure_ascii=False),encoding="utf-8")
    @classmethod
    def load(cls,p):
        d=json.loads(Path(p).read_text(encoding="utf-8")); engine=d.get("engine","python-byte-bpe")
        if engine=="huggingface-tokenizers":
            obj=cls(d["vocab_size"],specials=d.get("specials"),backend="python")
            try:
                from tokenizers import Tokenizer
                obj._hf=Tokenizer.from_str(d["tokenizer_json"]); obj._backend="hf"; obj._special_ids={k:int(v) for k,v in d.get("special_ids",{}).items()}; return obj
            except Exception as exc: raise RuntimeError("Install tokenizers>=0.21 to load this tokenizer") from exc
        return cls(d["vocab_size"],d.get("merges",[]),d.get("specials"),backend="python")
