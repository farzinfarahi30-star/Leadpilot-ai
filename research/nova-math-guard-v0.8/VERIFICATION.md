# NOVA Math Guard v0.8 — reproducible validation

Run from the extracted directory:

```sh
python3 run_all.py
python3 -m unittest -q test_countermodels
python3 conditional_counterexample.py --given 'x*y=1' --goal 'x=y'
python3 conditional_counterexample.py --given 'x**2=0' --goal 'x=0'
```

`run_all.py` checks SHA-256 hashes of every published source, document, and
certificate, runs the earlier v0.6 tests and new countermodel tests, and checks
every JSON certificate in `certificates/` with `independent_verifier.py`.
It optionally runs independent differential tests using SymPy if installed.

The new `test_countermodels.py` includes 14 test methods, including 400
seeded rational counterexample trials, deliberate certificate alterations,
correctly UNKNOWN cases, and cross-checks of proof versus disproof.

**Interpretation:** reproducible local software tests do not constitute
formal verification of the Python implementation, a new theorem, or a solution
to a mathematical open problem. GitHub publication does not itself confer
independent peer review.

## New v0.8 tests

`python3 -m unittest -q test_real_sos` checks new exact real-SOS certificate
search and verification, malformed weights, tampering, complex-domain labels,
negative controls, and 250 seeded positive-semidefinite quadratic expansions.
`python3 research_backchain.py` produces a small known-mathematics audit.
Neither these tests nor GitHub publication constitute a new mathematical theorem.
