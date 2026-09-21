# Nova Native Tokenizer

A deterministic, UTF-8-safe tokenizer boundary for Nova AI.

The current implementation uses byte fallback plus versioned special tokens.
It is deliberately independent from the existing Nova checkpoint until the
checkpoint vocabulary and embedding/output dimensions are verified.

Important separation: tokenizer token IDs are technical model units. They are
not the NOVA economic/crypto token.

Future vocabulary training can introduce BPE or SentencePiece merges through a
new explicit tokenizer version rather than silently changing token semantics.
