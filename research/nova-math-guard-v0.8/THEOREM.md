# Soundness claim for radical-power witnesses (known elementary theorem)

**Theorem.** Let `F` be a field containing `Q`, and let `h_1, ..., h_m, t` be elements of the polynomial ring `Q[X]`. If there exist `k >= 1` and polynomial multipliers `q_1,...,q_m in Q[X]` such that

    t**k = q_1*h_1 + ... + q_m*h_m,

then every assignment `a in F^X` satisfying `h_i(a)=0` for all `i` also satisfies `t(a)=0`.

**Proof.** Evaluation at `a` is a ring homomorphism, so

    t(a)**k = sum_i q_i(a)*h_i(a) = 0.

Because `F` is a field, `t(a)**k=0` implies `t(a)=0`. Thus the conclusion follows. `QED`.

This elementary result and Buchberger's algorithm predate NOVA; **neither is claimed as a new mathematical discovery.** We use it to justify the meaning of independently verified `NOVA-MATH-GUARD-RADICAL-CERT-1` files. The same argument holds over any *reduced* commutative `Q`-algebra, but not an arbitrary `Q`-algebra with nonzero nilpotents.

## Checkable example

Given `x**2=0` and `y**3=0`, conclude `x+y=0` over `F`.

    (x+y)**4 = (x**2)*(x**2+4*x*y+6*y**2) + (y**3)*(4*x+y)

An independently verified certificate for this identity appears in `certificates/radical_mixed_nilpotents.json`. When the two hypotheses hold, `(x+y)**4=0`, hence `x+y=0` over a field.

## Limitations

The implemented search tests `k=2,3,4` only, after first attempting ideal membership (`k=1`). A failure to find a certificate is a bounded search failure and proves nothing about the falsity of a claim.

Over **all complex points**, radical ideal membership is connected to Hilbert's Nullstellensatz, but this tool is deliberately not represented as a complete solver. Over rational or real solutions, some valid consequences cannot be certified with this power-ideal method; e.g., `x**2+y**2=0` implies `x=0` over reals but fails over complexes.

The verifier's Python implementation is not a formally proven implementation in Lean or Coq. This file is a paper-and-pencil soundness argument about the algebraic certificate *if* exact checking is implemented correctly.

## v0.7: exact rational falsification certificates

For polynomials h_1,...,h_m,t over Q, a rational point a satisfying
h_i(a)=0 for all i but t(a) != 0 refutes the implication
`(forall i h_i=0) => t=0` over Q and any extension field containing Q.
The independent verifier reconstructs the original equations and verifies
both sides at the exact assignment. This statement is elementary, standard
mathematics; no originality claim is made. See `COUNTERMODEL_THEORY.md`.
