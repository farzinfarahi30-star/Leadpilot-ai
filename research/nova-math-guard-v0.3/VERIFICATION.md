# NOVA Math Guard v0.3 — observed verification

Date: 2026-10-19. Environment: Python 3.13, SymPy 1.14.0.

Executed from the v0.3 directory:

Use `python3 run_all.py` to rerun the checksum check and all bundled tests from one command.

| Command | Observed result |
|---|---|
| `python3 nova_math_guard.py selftest` | PASS: 12 exact cases + 8 refusal tests |
| `python3 -m unittest -q test_math_guard test_certificates` | PASS: 17 test methods, including 1,200 deterministic randomized certificate cases and 500 random linear-equation cases |
| `python3 differential_sympy_optional.py` | PASS: 3,000 independent SymPy polynomial comparisons |
| `python3 research_experiment.py` | PASS: 24 independently replayed certificates (12 known identities, 12 altered near-misses) |
| `python3 independent_verifier.py certificates/binomial_identity.json` | VERIFIED PROVED |
| `python3 independent_verifier.py certificates/nonidentity_counterexample.json` | VERIFIED DISPROVED |
| `python3 independent_verifier.py certificates/linear_unique_solution.json` | VERIFIED UNIQUE, x=5 |
| `python3 independent_verifier.py certificates/cancelled_variable_counterexample.json` | VERIFIED DISPROVED |

The tests exercise a **limited fragment** of algebra. They do not prove
correctness of arbitrary expressions, guarantee absence of implementation bugs,
or establish a new mathematical theorem. A verifier is independent of the
certificate generator but is still ordinary Python, not Lean or Coq.

No paid tool, API, service, or subscription was required for these checks.
