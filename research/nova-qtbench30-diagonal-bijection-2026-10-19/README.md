# NOVA — Chern–Fu Question 5.5, diagonal-subfamily partial result

**Status:** a rigorously established, grade-preserving, explicitly invertible injection on one exponentially growing subfamily; **not** a solution of the full open problem; **not** a claim of worldwide originality.

## Main result

A diagonal improper partition matrix with positive contiguous column sizes `(a1,...,ad)`, final size odd, maps to a Chern–Fu restricted inversion sequence by using pairs of adjacent equal labels inside each column. Every new column starts with a fresh label equal to its first (one-based) sequence index minus one; additional pairs in a column use the smallest previously unused label.

The map is injective and invertible on its image, preserving the semi-weight/number-of-distinct-values statistic.

Number of matches for size `n`: `(2**n - (-1)**n) // 3`. Graded generating function: `z*x/(1-z*x-2*z*x*x)`.

**See [PROOF.md](PROOF.md) for complete definitions, theorem, proof, references, and exact limitation.**

## Verification

```bash
python3 diagonal_bijection.py
python3 independent_source_enum.py
python3 verify.py
sha256sum -c SHA256SUMS
```

`diagonal_bijection.py`: all compositions for `n=2..12`, validity/grade/injectivity/inverse checks and separate target-family graded counts. `independent_source_enum.py`: independently generates full improper-minus source matrices `n=3..8` and compares exact graded distributions against qtBench. `verify.py`: additional negative/edge-case checks. These checks support, but do not replace, the general paper proof.

**Open obstacle:** no map for the non-diagonal remainder (already 2 cases at n=4; 16,166 cases at n=10). **Originality unverified.**
