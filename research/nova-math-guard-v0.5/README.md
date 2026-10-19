# NOVA Math Guard v0.5 — verified consequences of polynomial equalities

**Status:** Open research prototype; no claim of a new theorem or a solution to any longstanding open problem. Cost to run: £0. Python 3 standard library only, with optional SymPy differential tests.

## What changed since v0.4?

**Certified Gröbner-basis completion.** Version 0.5 adds a bounded Buchberger
algorithm that constructs new polynomial relations by S-polynomials. Every
basis element carries an exact **lift back to the original hypotheses**.
When a goal reduces to zero, NOVA emits the same v0.4 conditional certificate,
which the original independent verifier checks without trusting the Gröbner code.

A case that v0.4 conservatively reported UNKNOWN now succeeds:

```sh
python3 conditional_prover.py --given 'x*y=1' --given 'y**2=1' --goal 'x=y' -o /tmp/nova-grb.json
python3 independent_verifier.py /tmp/nova-grb.json
```

The classical identity behind it is `x-y = y*(x*y-1)-x*(y**2-1)`.
Neither the identity nor the algorithm is a novel mathematical theorem.

The Groebner search has strict basis/pair/reduction limits, and produces
`UNKNOWN` rather than inventing a proof on resource exhaustion. Even an
unbounded ideal-membership decision is not a complete test of logical
implication over rational or real solutions (see `CERTIFICATE_THEORY.md`).

## Earlier v0.4 functionality


**Conditional algebra proofs.** Given polynomial equations, the program can now produce machine-readable witnesses for some algebraic consequences. A certificate consists of polynomial multipliers `Q_i` such that

`(goal_left - goal_right) = sum_i Q_i * (hypothesis_i_left - hypothesis_i_right)`.

The mathematically independent verifier reconstructs the left and right sides from the original hypotheses and goal, then checks the equation *exactly* over `Q[x1,...,xn]` using rational arithmetic. It imports neither the certificate generator nor the main algebra engine. All claims are about this formal, limited polynomial domain.

The prover attempts rational linear combinations, ordered polynomial division, and finally bounded Gröbner-basis completion. If every attempt fails, it reports `UNKNOWN` rather than incorrectly declaring the goal disproved.

## Reproducible examples

```sh
cd nova-math-guard-v0.4
python3 conditional_prover.py --given 'x=y' --goal 'x**2=y**2' -o square.json
python3 independent_verifier.py square.json

python3 conditional_prover.py --given 'x+y=3' --given 'x-y=1' --goal 'x=2' -o eliminate.json
python3 independent_verifier.py eliminate.json

python3 conditional_prover.py --given 'x*y=0' --given 'x*(y-1)=0' --goal 'x=0' -o zero_factor.json
python3 independent_verifier.py zero_factor.json
```

Three bundled examples are also available in `certificates/conditional_*.json`.

The proofs are recognizable exact identities:

- If `x=y`, then `x²−y²=(x+y)(x−y)=0`.
- If `x+y=3` and `x−y=1`, then `x−2=½(x+y−3)+½(x−y−1)`.
- If `xy=0` and `x(y−1)=0`, then `x=(xy)−(xy−x)=0`.

## Other supported features

Retained from v0.3: exact rational calculations, polynomial identities, concrete rational counterexamples to false identities, verified one-variable rational linear equations, and portable JSON certificates. Both the original `NOVA-MATH-GUARD-CERT-1` and the new `NOVA-MATH-GUARD-CONDITIONAL-CERT-1` certificate schemas are accepted by the standalone verifier.

```sh
python3 nova_math_guard.py selftest
python3 -m unittest -q test_math_guard test_certificates test_conditional test_groebner
python3 research_experiment.py
python3 run_all.py
```

The release contains a strict SHA-256 source-and-certificate file manifest. `run_all.py` verifies the manifest **before** running the tests; it also verifies the bundled certificate examples. Do not change files or rebuild `RESEARCH_RESULTS.json` without regenerating the manifest. Generated temporary certificates (`square.json`, etc.) should go outside the project directory (or you can remove them before running `run_all.py`).

## Honest limitations

- This is not Lean 4, Coq, or a formally verified kernel. Ordinary code could contain bugs, and an independent Python verifier cannot promise perfect soundness.
- The system proves only polynomial consequences expressible as a finite linear combination of the supplied equalities with polynomial coefficients; even when such a witness exists, configured computational limits may prevent the algorithm finding it.
- All proofs are conditional. For inconsistent assumptions, *any* conclusion is vacuously true, which the certificate correctly reflects but does not establish that the assumptions can be satisfied.
- A `UNKNOWN` does not imply the conclusion is false; there might be a proof with another algorithm, including a Gröbner basis or radical membership method.
- Degree, term count, AST-size, witness-size, file-size, and step limits are designed to prevent accidental unbounded work, not to make the CLI safe to expose directly to hostile public inputs without an OS sandbox.
- No novelty or historic mathematical breakthrough is claimed. The examples illustrate established algebraic principles.

## Files

- `conditional_prover.py`: generates polynomial-ideal membership witnesses by exact linear combination or polynomial division.
- `independent_verifier.py`: independently checks both old and new certificates.
- `test_conditional.py`: positive and negative regression tests, deliberate mutations, and 300 randomized generated consequences.
- `CERTIFICATE_THEORY.md`: precise soundness argument and limits.
- `certificates/conditional_*.json`: examples of machine-checkable conditional consequences.
- `SHA256SUMS`, `run_all.py`: integrity verification and one-command test suite.
- All v0.4 files retained for backward compatibility.
- `groebner_prover.py`: bounded Buchberger search with certified lifts.
- `test_groebner.py`: new prover regression tests, known hard cases and 250 seeded witness reconstructions.
- `certificates/conditional_groebner_elimination.json`: independently verifiable Gröbner-derived proof.

Upgraded October 19, 2026. This is incremental open-source mathematical infrastructure, not the solution to an open mathematical conjecture.
