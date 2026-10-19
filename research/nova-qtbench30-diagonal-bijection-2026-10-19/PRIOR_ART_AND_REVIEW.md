# Prior-art search, attempts at falsification, and next research gate

**Search date:** 2026-10-19. Not an exhaustive literature search. Does **not** establish global priority.

## Target and nearest known results

- Chern & Fu's published article (2026), especially **Theorem 3.3** (graded equidistribution) and **Question 5.5** (asks for direct grade-preserving bijection between *all* improper-minus partition matrices and restricted inversion sequences). Their Sections 2–4 introduce definitions, an analytic proof, and combinatorial refinements for other subfamilies. Original source: https://shanechern.github.io/publications/preprints/106.pdf ; DOI:10.1016/j.jcta.2026.106213.
- The public qtBench #30 mathematical benchmark, under 'partition-matrix-inversion', specifies a *full* forward/inverse algorithm for all source and target objects, for all n, with grading, canonicality, and scalability requirements. Public cases n=3..9 alone do not prove a global bijection: https://github.com/SwagCai/qtBench/tree/main/problems/exchanging_bijection/improper_partition_matrix_inversion_sequence_bijection
- Claesson, Dukes & Kubitzke's previously published partition-matrix to *unrestricted* inversion-sequence bijection is a different map with a different domain; restricting it does not trivially solve Chern–Fu's Question 5.5.
- Related 2025/2026 literature on **inversion-sequence pattern avoidance**, including *Completing the Enumeration of Inversion Sequences* and results on smallest-unused-value encodings of inversion sequences into set partitions, shows that simple local coding tricks can overlap established research: https://www.combinatorics.org/ojs/index.php/eljc/article/download/v32i4p46/pdf/ and https://dergipark.org.tr/en/download/article-file/5729273 .

## Targeted queries checked

"improper partition matrices diagonal composition inversion sequences bijection"; "improper partition matrices" + "diagonal"; "inversion sequence" + "smallest unused" + "compositions"; "inversion sequences" + "pairs" + "composition"; "qtBench problem 30 bijection question 5.5 solution". Absence of a directly matching result in these results is **not** evidence that the claim is new.

## Actual constructive result

Theorem A in `PROOF.md`: an explicit grade-preserving injection for *diagonal-only matrices* with odd final column cardinality, i.e., **only a subfamily** of the source. Theorem B: an elementary rational generating function counting this subfamily by grade. Both have fully spelled-out short mathematical proofs.

The general proof is **human-readable but not formalized in Lean**. Separate NOVA's Lean kernel demonstration concerning squares modulo four does not formally validate this new injection. Independent computer checks cannot substitute for proof, although they found no contradictions in the tested range.

## Falsification / boundary probes

1. **Smallest failure of surjectivity:** n=4. Source and target each have 7 objects, while the explicit map covers 5. Two missing target sequences: `0,0,1,2` and `0,0,2,1`. Accordingly, the map cannot be represented as answering Question 5.5.
2. **Off-diagonal witness:** the improper-minus partition matrix with consecutive column sizes `(1,3)` and row assignments `(1,1,1,2)` is excluded from the diagonal family. This specific matrix has valid semi-weight `3` and demonstrates the boundary of the method.
3. **Exhaustive finite checks:** compositions n=2..12, grading, inversion bound, no nonadjacent repetition, terminal inequality, injectivity, and inverse; independently enumerated target classes n=2..9; independently enumerated all source matrices n=3..8 and checked graded counts against qtBench; SymPy rational series coefficients n=1..13.
4. **No rank-table workaround:** neither algorithm queries stored benchmark objects or maps one side to the other using sorted indices. Formula uses just the structure of the input composition and previously assigned labels.

## External review standard / future steps

Before public claims of originality, seek a specialist in enumeration and inversion-sequence pattern avoidance to determine whether this particular restricted bijection has a known name or elementary equivalent; locate all cites to Chern–Fu Question 5.5; compare construction to existing combinatorial encodings involving compositions and adjacent pairs. Do *not* solicit a review claiming full solution.

The meaningful next research advance is an extension that handles **off-diagonal row choices** from Chern–Fu's definition, with an invertible local rule preserving the semi-weight. Full benchmark success and a proof valid for all n are needed before saying the main problem is solved.
