# Partial construction for Chern–Fu Question 5.5

**Status: fully proved elementary subcase; no claim of new mathematical knowledge, no solution of the full open question.**

## Precise definitions and scope

Let \(C_n^{\mathrm{odd}}\) be the set of ordered compositions \(a=(a_1,\ldots,a_d)\) of \(n\) with \(a_d\) odd. A composition specifies a **diagonal partition matrix** of dimension \(d\): the \(j\)-th nonempty cell is \((j,j)\) and contains the consecutive labels in the \(j\)-th part. Every other cell is empty.

Such a matrix has no ascents or descents inside any column (all labels in one column have one row), hence is an **improper partition matrix**. The last cell (containing \(n\)) has odd cardinality precisely when \(a_d\) is odd; thus it belongs to the **minus** subfamily posed in Chern–Fu, Question 5.5.

Its semi-weight is

\[v(a)=\sum_{j=1}^d\left\lceil a_j/2\right\rceil.\]

Let \(I_n^-\) denote inversion sequences \(e=(e_1,\ldots,e_n)\) satisfying \(0\leq e_i<i\), without nonconsecutive repeated values (each distinct value occurs once or as a **single adjacent pair**), with \(e_{n-1}\neq e_n\) for \(n\ge 2\). Their grade \(\operatorname{dist}(e)\) is the number of distinct values. This is the target class of Question 5.5.

## Theorem A (explicit grade-preserving injection)

For every \(n\geq 2\), there exists an explicitly computable injection

\[\Phi_n:C_n^{\mathrm{odd}}\hookrightarrow I_n^-\]

such that \(\operatorname{dist}(\Phi_n(a))=v(a)\). The inverse on the image is constructive.

### Construction

Process composition parts left to right. Within each part, tile its positions by blocks of length two, followed by a terminal block of length one if the part is odd. Give every tile a distinct integer label; both positions of a length-two tile receive the same label. If a tile starts at position \(j\) (positions are one-based):

- For the **first tile of a part**, assign label \(j-1\).
- For each **subsequent tile within the same part**, assign the smallest nonnegative integer not assigned to an earlier tile.

The resulting sequence of labels is \(\Phi_n(a)\).

### Proof of well-definedness

Let a tile begin at position \(j\). Every earlier tile began at some position \(i<j\) and received label strictly less than \(i\), hence less than \(j-1\); so a first tile's label \(j-1\) has not been used.

For a subsequent tile, its part already contains an earlier *length-two* tile (because the first tile has length two whenever the part needs more than one tile). Thus, among the \(j-1\) preceding sequence positions there are strictly fewer than \(j-1\) preceding tiles, and all their distinct labels belong to \(\{0,\ldots,j-2\}\). Therefore at least one unused label exists in that set; the smallest unused is \(\le j-2\), so the inversion-sequence bound \(e_j<j\) holds. The optional second position of a length-two tile also respects its inversion bound.

Every label occurs in exactly one tile; hence it cannot occur twice at nonadjacent positions. The last composition part is odd, so its last tile has length one. Because each tile has a new label, \(e_n\neq e_{n-1}\). Thus \(\Phi_n(a)\in I_n^-\).

There is one distinct label per tile, and a part of length \(a_j\) contains exactly \(\lceil a_j/2\rceil\) tiles. Hence \(\operatorname{dist}(\Phi_n(a))=v(a)\).

### Proof of injectivity

Any output can be uniquely split into its maximal runs of equal labels; these are precisely the length-one or length-two tiles, since each tile label occurs nowhere else. At the start \(j\) of a run, the run starts a **new part if and only if** its label equals \(j-1\): that holds by construction for first tiles, whereas later tiles receive the smallest unused label, which, by the counting argument above, is at most \(j-2\). Therefore the output uniquely determines all part starts and hence the original composition. The decoding function in `diagonal_bijection.py` implements this inverse and rejects words outside the image. QED.

## Theorem B (graded image generating function)

Let

\[D_n(z)=\sum_{a\in C_n^{\mathrm{odd}}} z^{v(a)}.\]

Then, as an identity of formal power series,

\[\boxed{\sum_{n\ge1}D_n(z)x^n=\frac{zx}{1-zx-2zx^2}.}\]

Consequently \(D_1=z,\ D_2=z^2\) and

\[D_n(z)=zD_{n-1}(z)+2zD_{n-2}(z)\quad (n\ge 3).\]

In particular, the total number of explicitly matched pairs is

\[\boxed{D_n(1)=\frac{2^n-(-1)^n}{3}}.\]

### Proof

Let \(A(x,z)\) count an arbitrary positive part of size \(a\) with weight \(z^{\lceil a/2\rceil}\), and let \(O(x,z)\) count an *odd* positive final part. Then

\[A=zx(1+x)\sum_{m\ge0}(zx^2)^m=\frac{zx(1+x)}{1-zx^2},\qquad O=zx\sum_{m\ge0}(zx^2)^m=\frac{zx}{1-zx^2}.\]

A composition in \(C_n^{\mathrm{odd}}\) consists uniquely of any sequence of ordinary positive parts followed by one odd final part, so its generating function is \(O/(1-A)\). Substitution and simplification gives \(zx/(1-zx-2zx^2)\). At \(z=1\), partial fractions of \(x/((1-2x)(1+x))\) yield \((2^n-(-1)^n)/3\). QED.

## Explicit limitation / unsuccessful generalization

The injection only covers diagonal matrices. It is not the sought bijection on all improper partition matrices: at \(n=4\) it matches exactly **5 of 7** objects. The inversion sequences \((0,0,1,2)\) and \((0,0,2,1)\) are in the target class but not its image. On the source side, for example, the matrix encoded by column sizes \((1,3)\) and row assignments \((1,1,1,2)\) is an improper minus matrix **not** of diagonal form, with semi-weight 3.

The real unsolved step is to extend the map to such off-diagonal matrices while preserving the grading, keeping both directions explicit, and proving validity uniformly for all \(n\), rather than relying on fiber-ranking or finitely many test cases.

## Originality and attribution

This elementary injection and rational generating function are rigorous statements **within this package**, but their priority/originality has **not** been established. The domain is a simple subclass of objects that Chern and Fu already study, and similar encodings may exist under different terms. This is **not** a publishable breakthrough without stronger novelty evidence or an extension.

Primary references:

1. S. Chern and S. Fu, *Signed counting of partition matrices*, J. Combinatorial Theory A 223 (2026), Paper 106213, DOI:10.1016/j.jcta.2026.106213; author PDF https://shanechern.github.io/publications/preprints/106.pdf, Section 2 Definitions 2.1, 3.1 and Section 5 Question 5.5.
2. qtBench, problem `improper_partition_matrix_inversion_sequence_bijection`, https://github.com/SwagCai/qtBench/tree/main/problems/exchanging_bijection/improper_partition_matrix_inversion_sequence_bijection (benchmark validation cases, not a research proof).
3. Claesson, Dukes and Kubitzke, *Partition and composition matrices*, foundational bijection from partition matrices to inversion sequences, as cited by Chern–Fu.
