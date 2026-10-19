# A strictly larger explicit partial correspondence for Chern–Fu Question 5.5

**19 October 2026 · Scope: infinite, restricted domain only. Not the requested full bijection.**

## Definitions and previous result

An *improper partition matrix* over `[n]` is an upper-triangular `d×d` matrix of disjoint subsets partitioning `[n]`, every row and column nonempty, with labels increasing across columns. Within a column, an adjacent pair `i,i+1` whose smaller index has the parity of that column's least label must occupy the same row; the other adjacent pair may switch row. In the *minus* class, the **cell** containing `n` has odd cardinality. Define `v(M) = sum_j ceil(column_size_j/2)`.

The target consists of inversion sequences `0≤e_i<i` such that each value appears once or exactly twice in adjacent positions, and `e_{n-1}≠e_n` for `n≥2`. Define `dist(e)` to be the number of distinct entries.

The prior NOVA partial construction sends the *diagonal* matrix with consecutive-column lengths given by an ordered composition of `n` whose last part is odd into a valid inversion sequence, preserving `v=dist`. Its encoded words are identified by the inverse algorithm in `diagonal_bijection.py`. Its graded generating function is

`F_diag(x,z) = z*x/(1-z*x-2*z*x^2)`.

The prior diagonal construction is included unchanged so that this package is independently executable.

## Theorem — a new disjoint infinite source subfamily and explicit injection

For every integer `n≥4`, the preceding partial correspondence extends to a *strictly larger* grade-preserving injection. Precisely, the added source family `T_n` consists of `2(n-3)` **off-diagonal** improper-minus matrices as follows.

Let `d=n-2`, and choose `r` with `1≤r≤d-1=n-3`. For each column `j<d`, place the single label `j` in cell `(j,j)`; the final column `d` consists of the labels `d,d+1,d+2=n`. Choose one of two types:

- **Type A_r**: labels `d,d+1` occupy row `d`, and label `d+2` occupies row `r`.
- **Type B_r**: labels `d,d+1` occupy row `r`, and label `d+2` occupies row `d`.

Every other cell is empty.

The new target words are `e=(0,0,s)` where `s` is a permutation of `1,2,...,n-2` made as follows (0-based positions in `s`):

- **A_r**: start with `s=(2,3,...,n-2)` and insert `1` at index `r` (thus `1` occupies index `r`, with `1≤r≤n-3`).
- **B_1**: `s=(1,2,...,n-2)` unchanged.
- **B_r**, `2≤r≤n-3`: start with `s=(1,2,...,n-2)` and swap entries at 0-based indices `r-1` and `r`.

These `2(n-3)` words are valid target inversion sequences of grade `n-1`, all different, and **none** is an image of the prior diagonal construction. The inverse is given explicitly by the first symbol of `s` and the position of `1` (type A), or the unique adjacent inversion relative to the sorted suffix (type B). Consequently, the union with the diagonal family defines an explicit grade-preserving injection on `C_n^odd ⊔ T_n` for all `n≥4`.

### Proof 1 — source conditions

The columns, by construction, partition the consecutive labels into lengths `1,...,1,3`, each nonempty, and all single-label columns precede the last one. The row labels `1,...,d-1` are occupied by singleton diagonal cells; row `d` is occupied by one or two labels in the last column. Thus every row and column is nonempty and all nonempty cells satisfy `row≤column`. The first two labels in the final column are adjacent and have the parity of the least label of that column; they are in the **same** row in either type, so the improperness condition holds. There are no other constrained distinct-row adjacent pairs in one column. The label `n=d+2` lies in a singleton cell because its row differs from the row of `d,d+1`, and therefore the last cell has odd size. Finally, `v=(d-1)+ceil(3/2)=(n-3)+2=n-1`. The matrices are off-diagonal because at least one label of the last column occupies an earlier row `r<d`. Changing the type or `r` changes the matrix, giving exactly `2(n-3)` source objects.

### Proof 2 — target constraints

The first two entries of every new word are `0,0`; every remaining entry is a permutation of `1,...,n-2`. Therefore the only repeated value is the **adjacent** pair of zeroes, and the final entry differs from the penultimate (both lie in a permutation of distinct integers). There are `n-1` distinct values.

The inversion bounds hold at the first two positions. For a suffix entry at 0-based suffix index `k` (its 1-based position in `e` is `k+3`):

- In A, before the inserted `1`, the entry is `k+2`, and afterward it is `k+1`; the inserted entry is `1`. Thus every suffix entry is at most `k+2 < k+3`.
- In B, without a swap the entry is `k+1`. At the earlier of the two swapped indices `k=r-1`, the new entry becomes `k+2`, while at the later index it becomes `k`; both still lie below `k+3`. Thus every bound holds.

So every new word is a valid target of grade `n-1`.

### Proof 3 — injectivity and explicit inverse

Type A words have third overall entry `2`; type B words have third entry `1`, so their images cannot overlap. Within A, the unique position of `1` in the suffix recovers `r`. Within B, the identity permutation denotes `r=1`; otherwise there is exactly one adjacent swap, and its location recovers `r`. Therefore A and B have disjoint injective images and an explicit inverse. The file `extended_bijection.py` rejects words that do not match either canonical form.

### Proof 4 — disjointness from the old diagonal image

Suppose a word in the old diagonal image begins `0,0` and has `n-1` distinct entries. Exactly one of its tiles has length two: the initial tile; no other tile may be repeated. The original diagonal composition therefore begins with a part of size `2` or `3`, after which **every** part has size one. (An initial part of size four or more contains at least two length-two tiles.) Since `n≥4`, the last part has size one, so its unique tile begins at global position `n` and by the old construction receives label `n-1`. Thus every diagonal image with this prefix and grade ends in `n-1`.

By contrast, all the new words end in a member of `{1,...,n-2}`, since their suffix is a permutation of that set. Hence no new word lies in the old image. The inverse on the union is obtained by trying the diagonal inverse first and, if it rejects, the new inverse. This establishes the theorem. □

## Corollary — exact graded enumeration of the enlarged image

Write `H_n(z)` for the weight enumerator of the enlarged source family, with exponent equal to `v`, including the old diagonal family. The new family contributes exactly `2(n-3)z^(n-1)` for each `n≥4`, so

`SUM_{n≥1} H_n(z)*x^n = z*x/(1-z*x-2*z*x^2) + 2*z^3*x^4/(1-z*x)^2`.

For `n≥4`, setting `z=1` gives the total covered count

`H_n(1) = (2^n - (-1)^n)/3 + 2(n-3)`.

The formula follows directly from summing the geometric-derivative series and the previously proved diagonal generating function. No claim is made that the total full source size follows this formula.

## Exact boundary and limitations

- **n=4**: the old diagonal image covers `5` of `7` valid target words, and the new types cover the other two, `(0,0,2,1)` and `(0,0,1,2)`. An independent exhaustive source enumeration confirms that the source union also covers all seven **for that one size**. This is not a proof for all `n`.
- **n=5**: the extended injection covers `15` of `21` target objects. Among the six explicitly unhandled objects are `(0,0,1,1,3)` and `(0,1,1,2,3)`.
- **n=6**: only `27` of `67` target objects are covered.
- In general the image grows roughly like `2^n/3`, while the full source/target class grows considerably faster. The full Chern–Fu Question 5.5 therefore remains unsolved.
- The proof uses mathematical elementary arguments and independent finite tests, but has **not** been formalized in Lean; the prior NOVA Lean demonstration concerns a different proposition.
- No worldwide originality or research significance has been established. The construction may be a simple special case of prior combinatorial encodings.

## Citations

1. S. Chern & S. Fu, *Signed counting of partition matrices*, JCTA **223** (October 2026), 106213, DOI: 10.1016/j.jcta.2026.106213; original author PDF: https://shanechern.github.io/publications/preprints/106.pdf ; especially Section 2, Definition 3.1, Question 5.5.
2. Claesson, Dukes & Kubitzke, *Partition and composition matrices*, JCTA **118** (2011), 1624–1637, cited in Chern–Fu (an existing full factorial-class bijection, not the sought restricted one).
3. qtBench authors, open Problem 30 registry, https://github.com/SwagCai/qtBench/tree/main/problems/exchanging_bijection/improper_partition_matrix_inversion_sequence_bijection .
