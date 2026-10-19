# NOVA Math Guard v0.6 validation record

All checks are reproducible without paid services. The source archive bundles `SHA256SUMS`; the baseline `python3 run_all.py` checks that manifest before executing tests and verifying all example certificates.

Local commands (2026-10-19):

```sh
python3 run_all.py
python3 -m unittest -q test_radical
python3 differential_radical_sympy_optional.py  # optional, requires SymPy
```

The tests check both successful proofs and correctly conservative `UNKNOWN` results. In particular, the tampering suite alters powers, multipliers, goal statements, and schema fields, and demands rejection.

Independent proof checker: `independent_verifier.py`, separate from the search engine. Tests are not a formal proof of the source code's correctness. This project reports *no original mathematical discovery*.
