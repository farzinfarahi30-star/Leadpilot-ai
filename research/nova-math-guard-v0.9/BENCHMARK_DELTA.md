# Measured before/after benchmark — NOVA 0.8 versus 0.9

**Date:** 2026-10-19 · **Status:** software benchmark, **not** a new theorem.

We reran 12 selected *known mathematics* cases in isolated Python processes
against the unchanged v0.8 release and the v0.9 code. A result counted as
PROVED or DISPROVED only when its complete certificate passed the independent
verifier. `UNKNOWN` means the bounded search did not find a witness.

| Verdict | v0.8 | v0.9 |
| --- | ---: | ---: |
| Independently verified PROVED | 5 | 9 |
| Independently verified DISPROVED | 2 | 2 |
| UNKNOWN | 5 | 1 |

Four previously unknown-to-v0.8 cases now have checked, known, elementary
real-SOS certificates: quartic (`x^4+y^4=0`), sextic (`x^6+y^6=0`),
octic (`x^8+y^8=0`), and mixed positive quartic
(`x^4+2*x^2*y^2+y^4=0`), each with goal `x=0`. The known implication
`x^10+y^10=0 => x=0` remains `UNKNOWN` under the new power bound.
An invalid signed quartic is still `DISPROVED` by a rational countermodel.

**Selection caveat:** examples were deliberately selected to reveal the
new mechanism; 9/12 is not a general mathematical success rate, and this
sample is not a blind independent benchmark. All cases are classical facts.

The exact inputs and outputs are recorded in `BENCHMARK_DELTA.json`.
To reproduce, run the two public source releases' `real_sos_prover.decide`
under their own Python search paths and apply their
`independent_verifier.verify_certificate` to every positive or negative
certificate. GitHub folder names:

- `research/nova-math-guard-v0.8`
- `research/nova-math-guard-v0.9`

Nothing here asserts discovery of a new theorem, formal proof-checker
implementation correctness, or completeness of SOS proof search.
