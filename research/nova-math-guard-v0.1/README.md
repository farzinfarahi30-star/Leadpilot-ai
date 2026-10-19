# NOVA Math Guard v0.1

**Status:** Early-stage mathematical checking software prototype (not a new mathematical theorem or solution to an open problem).

NOVA Math Guard is a dependency-free Python 3 command-line tool for exact rational arithmetic, polynomial identity checks, and single-variable linear equations over rational numbers. It uses Python's `fractions.Fraction` rather than floating-point approximations. Unsupported cases are reported as `UNKNOWN/UNSUPPORTED` instead of being guessed.

## Quick start

```bash
python3 nova_math_guard.py selftest
python3 nova_math_guard.py calc '1/3 + 2/7'
python3 nova_math_guard.py prove '(x+y)**2=x**2+2*x*y+y**2'
python3 nova_math_guard.py solve '3*x+7=22'
```

## Scope

- Exact operations involving integers, rational numbers, and polynomials.
- Identity checking by expansion into rational-coefficient polynomial normal form.
- Unique, none, and infinitely many rational solutions for one-variable linear equations.
- Explicit `UNKNOWN/UNSUPPORTED` answers for inputs outside the supported fragment.

## Important limitations

- This prototype is **not an independent proof assistant** such as Lean 4 and does **not** provide machine-checked formal proofs in a foundational logic.
- The implementation, dependencies, and supported syntax must be trusted and audited; passing tests is not a mathematical guarantee that there are no bugs.
- It does **not** solve famous open conjectures, and no original mathematical discovery is claimed.
- It is not a general symbolic mathematics system.

## Reproducibility

The bundled CLI self-test currently checks 12 positive and 6 refusal cases (18 total). Run it on your own system to verify these results.

## Publication and licensing

**No license has been chosen yet.** Please choose and add a license before publishing for reuse; do not assume the code is open-source merely because it is public.

## Citation

Suggested descriptive title: *NOVA Math Guard v0.1: An Exact-Arithmetic and Polynomial-Checking Prototype*.

Version: 0.1; date: 2026-10-19.