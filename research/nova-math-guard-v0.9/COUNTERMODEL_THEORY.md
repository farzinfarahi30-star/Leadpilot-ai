# Conditional countermodel soundness and limits (v0.7)

Let `h_1,...,h_m,t` be polynomials in `Q[X_1,...,X_n]`. A conditional
countermodel certificate includes a rational tuple `a` such that

1. for each `i`, `h_i(a) = 0` (every premise equation holds), and
2. `t(a) != 0` (the proposed conclusion equation is false).

The verifier independently parses the **original equation text** and computes
both sides of every equation in exact rational arithmetic; it verifies the
reported rational assignment and all reported values. Therefore the certificate
refutes the universally quantified implication

    For all a, (h_1(a)=0 and ... and h_m(a)=0) -> t(a)=0.

It refutes the implication over Q. Since Q injects into every characteristic-zero
field containing Q, the same assignment refutes the implication over each
such field. The verifier accepts no unverified AI reasoning; no search output
is trusted unless the certificate reconstructs.

## Deliberately incomplete search

`conditional_counterexample.py` searches finitely many candidate rational
assignments (default <=20,000) over at most six distinct variable names. **No
witness found means UNKNOWN, never PROVED.** Even a mathematically false
implication might have no counterexample in Q (e.g., a counterexample might
require complex values), or a rational witness may lie outside the finite
grid. Lack of a countermodel is not evidence that the theorem is true.

The positive proof path is also bounded and incomplete. For sound proofs,
`radical_prover.py` constructs polynomial certificates that
`independent_verifier.py` checks. Conditional certificates imply the goal
under the stated hypotheses in characteristic-zero fields, radical certificates
additionally use absence of nonzero nilpotents.

## Precise distinctions

- `x*y=1 -> x=y` is **false over Q**: witness x=2, y=1/2.
- `x*y=0 -> x=0` is **false over Q**: witness x=1, y=0.
- `x**2=0 -> x=0` is **true in fields**: radical certificate; not valid for
  an arbitrary nonreduced ring (nilpotents can exist).
- `x**2+y**2=0 -> x=0` is **true over R/Q** but **false over C**: x=i,
  y=1 witnesses failure in C. No rational counterexample exists, so the
  bounded rational countermodel search must not mark it DISPROVED.

These are classical facts, not new theorems. This software is not a
formal-kernel-verified proof assistant, and external audit is still needed
before trusting it for high-stakes mathematics.
