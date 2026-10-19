# Polynomial proof certificate semantics and trust boundary

## Existing equality-ideal certificates (v0.4–v0.5)

Given polynomial equalities `h_i(X)=0`, a conditional certificate proves that the goal difference `t(X)` is an exact polynomial combination `sum q_i(X)*h_i(X)`. It therefore vanishes at every common zero in every commutative `Q`-algebra, assuming the verifier is correct. The v0.5 Groebner search lifts the new relations to the original hypotheses, and the verifier checks only that final identity.

## New radical-power certificates (v0.6)

A radical certificate instead proves `t(X)**k=sum q_i(X)*h_i(X)` for an **integer exponent `2 <= k <= 4`**. This is enough to conclude `t=0` at each common zero over fields containing Q (and over reduced commutative Q-algebras). It is **not** a sound conclusion over arbitrary non-reduced Q-algebras. The verifier reconstructs the polynomial difference of the original goal and all hypothesis differences, computes the exact power by its separate exponent-vector engine, and compares it with the combination from the claimed exact multipliers. It rejects noncanonical normal forms, extra JSON fields, and invalid exponent types/values.

The accepted schema is `NOVA-MATH-GUARD-RADICAL-CERT-1`, the certificate kind is `radical`, the domain label is `Q-polynomial`, and evidence consists exactly of `{ "power": <int>, "multipliers_normal_forms": [...] }`.

### Example

For `x**2=0`, goal `x=0`, the certificate's `power` is 2 and multiplier is the constant polynomial 1. For the mixed example `x**2=0`, `y**3=0`, goal `x+y=0`, the exponent is 4 and multipliers are `x**2 + 4*x*y + 6*y**2` and `4*x + y`.

### Domain-specific caution

Over the reals, the hypothesis `x**2+y**2=0` implies `x=0`, but over complexes, `x=i` and `y=1` satisfy the hypothesis without the goal. Because the new certificates imply consequences in every field of characteristic zero containing Q, they cannot prove this real-only fact, and the system correctly returns `UNKNOWN`. An `UNKNOWN` verdict is not a counterexample or disproof.

## Independent verification vs proof-search

The verifier intentionally does not import the generator modules. It parses expressions independently and represents monomials as integer exponent vectors. Proof-search algorithms, heuristics, and optional SymPy comparisons are not part of the trusted checking path. The verifier remains ordinary Python code, **not a formally checked kernel**. Exact arithmetic and rigorous unit/property tests reduce risk but do not imply zero bugs.

An integrity manifest protects reproducibility **against accidental changes**. There is no cryptographic publisher signature or trusted reproducible-build attestation. These facts limit the confidence that can be claimed about third-party binaries and future releases.
