# NOVA / Chern–Fu Question 5.5 — extended, restricted partial bijection

**Research milestone, not a historic mathematical discovery.**

This package *strictly extends* NOVA's earlier explicit diagonal-subfamily injection to a new infinite off-diagonal subfamily of Chern–Fu's improper-minus partition matrices.

**New addition for each `n≥4`:** exactly `2(n-3)` off-diagonal source objects, mapped bijectively to an explicitly recognized set of `2(n-3)` previously uncovered target inversion sequences, preserving the grade `n-1`. Both directions are constructive. The enlarged image has generating function

```
z*x / (1-z*x-2*z*x*x) + 2*z*z*z*x*x*x*x / (1-z*x)**2
```

At `n=4`, the added family fills the two missing objects, producing a **complete correspondence for this fixed size only**. At `n=5`, six target objects remain unmatched. **The general open problem remains unsolved, and mathematical originality has not been established.**

## Run (Python 3, no paid services)

```
python -m unittest -v test_extended.py
python extended_bijection.py
```

The theorem and proof are in `PROOF.md`; critique and literature-search limitations are in `PRIOR_ART_AND_REVIEW.md`. All code, including the older diagonal implementation, is bundled locally. `sympy` is needed for only one optional test method (`test_generating_function`), not for the new construction itself.

## For research evaluation

- This is **not** a full submission to qtBench Problem 30.
- The proof is a mathematical argument, not formally kernel-checked in Lean.
- The closest prior work is the published Chern–Fu paper and the Claesson–Dukes–Kubitzke partition-matrix bijection. The targeted prior-art search cannot establish global priority.
- Tests are supporting evidence; refer to `PROOF.md` for the all-`n` argument.

Source paper: https://shanechern.github.io/publications/preprints/106.pdf . Benchmark: https://github.com/SwagCai/qtBench/tree/main/problems/exchanging_bijection/improper_partition_matrix_inversion_sequence_bijection .
