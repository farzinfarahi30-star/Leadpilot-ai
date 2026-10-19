# Prior art, falsification, and external review gate

Date: 2026-10-19. **Not an originality certificate.**

## Closest established result

Chern and Fu, *Signed counting of partition matrices* (JCTA 223, 106213), ask in Question 5.5 for a **direct, grade-preserving bijection on the entire improper-minus class**. Their own Lemma 5.4 relates plus/minus classes by adjoining/removing a terminal repeated label. The earlier work of Claesson, Dukes and Kubitzke gives a different bijection from **all** partition matrices to inversion sequences, but Chern and Fu explicitly explain why restricting it does not answer their question.

Our prior NOVA construction covered diagonal-only matrices. The current theorem explicitly adds two families of **genuinely off-diagonal** matrices for every `n≥4`. It is a rigorous *relative extension*, not a resolution of Question 5.5.

## Source checks

- The published Chern–Fu PDF contains Question 5.5 (last pages), which is stated for all `n≥1`, not merely `n≤9`.
- The qtBench Problem 30 test requires full explicit forward/inverse maps and disallows finite sorted-fiber lookup as a scalable solution. Our code does not claim to pass that full evaluator.
- Targeted queries checked October 19, 2026: `"improper partition matrices" "diagonal" "bijection" inversion sequence`, `"Signed counting of partition matrices" "direct bijection" "solution"`, `"inversion sequences" "adjacent equal" "last" bijection compositions`, and references in the published Chern–Fu article.
- We found relevant background and the source question, but no exact matching *finite extra family* in the results inspected. This **does not** demonstrate novelty.

Primary-source links: https://www.sciencedirect.com/science/article/pii/S0097316526000567 ; https://arxiv.org/abs/2508.21318 ; https://shanechern.github.io/publications/preprints/106.pdf ; https://github.com/SwagCai/qtBench/ .

## Attempts to falsify

- Every generated source object from the new family was independently checked against upper triangularity, nonempty rows/columns, column order, improperness, odd terminal cell, and grade, up to `n=39`.
- Every new target object was independently checked against inversion bounds, repetition restrictions and target grade, and decoded back to the original source, up to `n=80`.
- The complete diagonal and added images were compared for overlap up to `n=13`; there was none, as proved in PROOF.md.
- The union was compared against an independently enumerated complete target class for `n=4..8` and against an independent complete source enumerator for `n=4..7`.
- Independently expanded the proposed rational generating function in SymPy and compared coefficients with direct combinatorial enumeration through `n=12`.
- Positive stress-testing of a special case is not a proof for the whole problem; the unhandled targets from `n=5` upward explicitly demonstrate the gap.

## Next review standard

For an originality claim, perform a specialty literature survey around **restricted inversion sequences with one adjacent repeat**, **composition-to-inversion-sequence encodings**, **upper-triangular partition matrices**, and **Chern–Fu's parity-fixed improper subfamilies**, including related work in other terminologies. Obtain feedback from the paper's authors or a qualified independent specialist. Identify the exact mathematical contribution not implied by known correspondences. Formalize both the source validity predicate and the partial mapping in Lean, not merely a toy modular arithmetic lemma. Any future solution of Question 5.5 must map all valid objects for each `n`, prove grade-preservation, and give a true inverse.

## Contact/outreach policy

No unsolicited emails to the paper's authors have been sent as part of this release. Do not make claims of a historic discovery or request a rushed endorsement.
