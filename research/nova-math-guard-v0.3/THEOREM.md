# Mathematical guarantee and its limits

## Proven scope

For a polynomial expression in finitely many named variables over the rational
numbers, the normal form algorithm is intended to expand additions,
multiplications, integer nonnegative powers, and division by nonzero rational
constants into a finite sparse map from monomials to rational coefficients.
In this scope, two expressions are identical in `Q[x1,...,xn]` **if and only if**
their normal forms coincide. This follows from the standard uniqueness of
coefficients in a polynomial ring.

If a normal-form difference is not zero, a rational counterexample is guaranteed
by a finite root bound, with an explicit deterministic construction:

- Choose a variable x of degree d in the current nonzero polynomial p.
- At least one of the d+1 substitutions x=0,1,...,d leaves a nonzero polynomial
  in the remaining variables: otherwise p would have more than d roots over
  their integral-domain coefficient ring.
- Retain the first nonzero specialization and repeat with remaining variables.
- The final value is a nonzero rational number, refuting the identity.

This is a **classical known argument**, not a novel theorem discovered here.

## Certificates and independent replay

The certificate generator uses the `nova_math_guard.py` symbolic engine. The
independent verifier reconstructs all algebraic operations separately, using a
different monomial representation (fixed exponent vectors) and no import from
the generator or main engine. It independently computes canonical polynomial
normal forms, checks claimed identity verdicts, recomputes counterexample
substitutions, or checks the coefficients and solutions of rational linear
equations.

A certificate only checks against this software implementation of the stated
mathematical semantics. It is not a Lean 4/Coq proof and is not a formal proof
of the verifier software itself. Independent software implementations can still
share mathematical or implementation errors; external expert review remains
appropriate for research claims.

## Deliberate unknowns

General nonlinear equation solving, inequalities, limits, irrational constants,
domain-sensitive rational functions, quantum mechanics, P vs NP, and the Riemann
hypothesis are outside this tool's coverage. Resource caps also cause some
valid inputs to be rejected. Any open-problem claim would need a separate,
complete, mathematically rigorous proof and independent scrutiny.
