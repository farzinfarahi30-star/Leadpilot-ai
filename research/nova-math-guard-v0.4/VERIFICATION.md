# NOVA Math Guard v0.4 — reproducibility record

Date: 2026-10-19. Environment: Python 3.13.5, optional SymPy 1.14.0.

- `python3 nova_math_guard.py selftest`: 12 exact cases and 8 unsupported-input refusals passed.
- `python3 -m unittest -q test_math_guard test_certificates test_conditional`: 30 test methods passed, including the v0.3 seeded regressions (1,200 certificate and 500 linear-equation cases), 300 more randomized conditional consequences, adversarial certificate mutations, and independent process rejection.
- `python3 differential_sympy_optional.py`: 3,000 exact algebra comparisons passed against SymPy 1.14.0.
- `python3 research_experiment.py`: 24 replayed certificates, consisting of 12 known binomial identities and 12 modified near-miss refutations.
- `python3 independent_verifier.py certificates/conditional_square.json`, `conditional_linear_combo.json`, `conditional_elimination.json`: separately verified new conditional certificates.
- `python3 run_all.py`: source integrity and the full tests passed when release manifest was generated.

The previous v0.3 working directory was found to have a **stale SHA256SUMS entry for README.md** when checked during this upgrade. v0.4 regenerates and enforces its file manifest after all release files are finalized.

These tests do not establish the absence of mistakes, complete mathematical decidability, an accepted original theorem, or formal verification of the verifier.
