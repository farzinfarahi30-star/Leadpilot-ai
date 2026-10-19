# NOVA Math Guard v0.3 — independently replayable certificates

**Public research prototype.** NOVA Math Guard handles a small, precisely
defined class of mathematics: exact rational arithmetic, identities of
multivariate polynomials with rational coefficients, and linear equations in
one variable over the rationals. It is **not** a solution to a famous open
problem, does not solve arbitrary mathematics, and does not run Lean/Coq.

## New in v0.3

- **Portable JSON certificates** for polynomial identities, counterexamples,
  and rational linear equations, with a strict versioned schema.
- **Separate verifier** (`independent_verifier.py`) that reconstructs polynomial
  arithmetic from scratch using a different monomial representation; it does
  not import the main engine or certificate generator. It rejects forged
  solutions, mismatched normal forms, and altered counterexamples.
- **Independent checking** with the Python standard library only; no paid API,
  cloud service, or user account is required.
- **Reproducible research demonstration:** degrees 1–12 of the classical
  binomial theorem are proved, and 12 deliberately modified expressions
  receive concrete counterexamples. See `RESEARCH_RESULTS.json`.
- **Adversarial, randomized and regression tests**, plus an optional comparison
  with SymPy 1.14.0. See `VERIFICATION.md` for the observed local results.

## Quickstart (Python 3, no third-party packages)

From this folder, run everything with one command (SymPy is optional):

```sh
python3 run_all.py
```

Individual checks:

```sh
python3 nova_math_guard.py selftest
python3 -m unittest -q test_math_guard test_certificates
python3 nova_certificates.py identity '(x+y)**2=x*x+2*x*y+y*y' -o sample.json
python3 independent_verifier.py sample.json
python3 nova_certificates.py identity 'x**2=x' -o refutation.json
python3 independent_verifier.py refutation.json
python3 nova_certificates.py linear '3*x+7=22' -o linear.json
python3 independent_verifier.py linear.json
python3 research_experiment.py
```

Optional (if SymPy is already installed):

```sh
python3 differential_sympy_optional.py
```

Four ready-to-verify examples are included in `certificates/`.

## Interpretation

- `PROVED` for an identity means exact equality of two polynomials in
  `Q[x1,...,xn]`, *not* an arbitrary mathematical proof.
- `DISPROVED` means a rational assignment makes the left and right sides
  unequal; the certificate records an exact counterexample and both values.
- `UNIQUE`, `NONE`, and `ALL` describe the rational solution set of a supported
  linear equation. Nonlinear problems and unsupported expressions are rejected.
- The independent verifier checks the statement and evidence. Do **not** trust
  a certificate merely because it says `PROVED`; run the verifier.

## Security and scientific limitations

This is research software, not a sandbox or a production security boundary.
The parser has size and complexity limits, but untrusted and high-volume inputs
should be evaluated in an isolated process with memory/CPU limits. A verified
certificate is only as reliable as the semantics and correctness of the
independent verifier. No proof assistant has formally certified this code.
Tests and independent replay materially improve confidence but cannot promise
zero mistakes. The mathematical argument in `THEOREM.md` is classical, not a
new mathematical discovery. No historic breakthrough is claimed.

## Project files

| File | Purpose |
|---|---|
| `run_all.py` | One-command checksum, test, certificate, and research checks |
| `nova_math_guard.py` | Rational arithmetic, polynomial checking, deterministic witnesses |
| `nova_certificates.py` | Generate JSON proofs and refutations |
| `independent_verifier.py` | Independent replay of certificate semantics |
| `test_math_guard.py` | Algebra and witness regression tests |
| `test_certificates.py` | Certificate, mutation, and randomized tests |
| `differential_sympy_optional.py` | Optional cross-check against SymPy |
| `research_experiment.py` | Reproducible finite binomial exploration |
| `certificates/` | Three illustrative, replayable certificates |
| `RESEARCH_RESULTS.json` | Experiment results (not new research findings) |
| `THEOREM.md` | Short rigorous description of mathematical scope |
| `VERIFICATION.md` | What was actually run |

**Release:** 2026-10-19. v0.1 and v0.2 remain separately available as historic snapshots.
