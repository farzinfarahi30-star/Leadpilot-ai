# Evidence-first research decision (2026-10-19)

## Target outcome
An independently reproducible proof or counterexample of a previously
unresolved mathematical statement, supported by a documented prior-art review.

## Work backward
1. Define the exact domain and unambiguous mathematical claim.
2. Choose a checker that is independent of the search and preferably a formal
   kernel (Lean 4). Our current checker is independent Python, not Lean.
3. Establish known positive and negative benchmarks before proposing novelty.
4. Search for certificates and record bounded UNKNOWN outcomes honestly.
5. Check relevant literature, search for existing proofs, invite review by
   mathematical specialists, and only then discuss publication as a discovery.

## What today's experiments actually show
The upgraded exact verification fragment covers several degree-4, -6 and -8
real-algebra examples not covered in v0.8. It does not prove anything about
famous open problems, complexity classes, number theory, or all mathematics.

## Highest-value next technical milestone
Rather than automatic version increments, integrate kernel-checkable Lean
proofs for our existing certificates, then benchmark general polynomial
inequalities against established tools. The public `leanprover/sos` project
already supports stronger nonlinear inequality machinery, including
non-SOS Motzkin examples via Positivstellensatz powers. Any new result must
be measured against that prior art.

## Scientific status
Novel mathematical theorem: NOT VERIFIED.
Open-problem solution: NOT VERIFIED.
Engineering improvement with exact certificates: VERIFIED by included tests.
