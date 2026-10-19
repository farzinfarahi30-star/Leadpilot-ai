# NOVA Math Guard v0.2

**Status:** Early-stage, dependency-free mathematical checker. This is **not** a discovery of a new theorem, a solution to an open problem, or a replacement for a formal proof assistant.

This Python 3 command-line program handles exact rational arithmetic, rational-coefficient multivariate polynomial identities, and one-variable linear equations over the rationals. It deliberately returns `UNKNOWN/UNSUPPORTED` outside its supported fragment.

## What's new in v0.2

- **Constructive counterexamples.** If two polynomial normal forms differ, the program produces an exact integer assignment and checks the resulting different left- and right-hand values. A deterministic variable-by-variable root-counting argument guarantees an assignment for any nonzero polynomial the program can process.
- **Resource limits.** Adds maximum polynomial degree, syntax-tree size, and multiplication limits to the existing expansion and input-length limits.
- **Ambiguous arithmetic.** Refuses `0**0` instead of silently choosing a convention. Polynomial expressions are interpreted formally over `Q[x, y, ...]`, not as unrestricted real-valued functions.
- **Expanded tests.** Ships independent regression tests with deterministic randomized polynomial witnesses.

## Run (Python 3; no third-party packages)

```bash
python3 nova_math_guard.py selftest
python3 -m unittest -v test_math_guard.py
python3 nova_math_guard.py calc '1/3 + 2/7'
python3 nova_math_guard.py prove '(x+y)**2=x**2+2*x*y+y**2'
python3 nova_math_guard.py prove 'x**2=x'
python3 nova_math_guard.py solve '3*x+7=22'
```

The `prove` mode checks polynomial identities **over rational coefficients**; a `PROVED` result refers only to that precise algebraic claim. `DISPROVED` returns a verifiable counterexample. The `solve` mode supports rational linear equations only. This program does not run Lean 4 or check arbitrary mathematical proofs.

## Why counterexamples are guaranteed

For a nonzero polynomial `p` in `Q[x1,...,xn]`, take the first variable with degree `d`. Evaluating that variable at `0,1,...,d` cannot yield the zero polynomial every time: a nonzero univariate polynomial over the integral domain of polynomials in the remaining variables cannot have more than `d` distinct roots. Keep the first specialization that remains a nonzero polynomial and repeat for each remaining variable. The final value is a nonzero rational number. This constructs a correct integer witness without probabilistic guessing.

## Limitations

- Not a sandbox: for untrusted, high-volume input, isolate the process and apply CPU and memory limits.
- Complexity caps can reject mathematically valid inputs as unsupported.
- Tests do not prove a program is bug-free.
- No scientific novelty or mathematical breakthrough is claimed.

**Historical release:** v0.1 is retained separately in this repository for reproducibility.