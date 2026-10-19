# NOVA Math Guard v0.5 — reproducibility record

Date: 2026-10-19. Independent proof checker unchanged from v0.4.

- `python3 run_all.py` checks file integrity, the exact-arithmetic self-test,
  40 unittest methods, every bundled certificate and the 24-case classical
  experiment. It optionally performs 3,000 SymPy comparisons if installed.
- 250 seeded, synthetically constructed goal polynomials were decomposed
  using Gröbner-lifted witnesses into original ideal generators.
- The previously unsupported `x*y=1` and `y**2=1` => `x=y` example now
  produces a certificate independently verified against exact polynomial
  arithmetic. It is a known classical identity, not a mathematical discovery.
- Failure/exhaustion is UNKNOWN; proving all mathematics and error-free
  computation are not claimed.

To reproduce from the archive, extract it, enter the extracted directory,
and run `python3 run_all.py` (no API keys or paid services required).
