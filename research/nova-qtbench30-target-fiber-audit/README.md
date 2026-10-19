# NOVA Research Experiment — qtBench Problem 30

**2026-10-19. Status: baseline reproduced, ORIGINAL OPEN PROBLEM STILL UNSOLVED.**

This is an independent, dependency-free checker of the *target-side* grading distribution of qtBench #30 (Chern–Fu's open Question 5.5). The open problem asks for a natural grading-preserving bijection from improper partition matrices to a restricted class of inversion sequences. **This package does not provide such a bijection.**

Source: [qtBench problem statement](https://github.com/SwagCai/qtBench/blob/main/problems/exchanging_bijection/improper_partition_matrix_inversion_sequence_bijection/problem.md). Primary research paper: Shane Chern and Shishuo Fu, *Signed counting of partition matrices*, JCTA 223 (2026), 106213.

## Zero-cost reproducibility

```
python3 fiber_counter.py --check
python3 fiber_counter.py --max-n 12
```

No external dependencies, credentials, or subscriptions.

## Derivation

For an inversion sequence `e_1,...,e_n` with `0 <= e_i < i`, impose:
- Every value occurs once or twice in consecutive positions, never elsewhere.
- The last two entries differ (the "minus" restriction).

Let `a[n,d]` count length-`n` sequences with `d` distinct entries **ending in a newly introduced value**, and `b[n,d]` count those **ending in the second copy of an adjacent pair**. At the next position, exactly `n+1-d` values have not yet occurred in `{0,...,n}`, independently of the labels used. A new value transitions either state to `a`, while repeating the last value (only allowed from the `a` state) transitions to `b`:

```
a[n+1,d+1] = (n+1-d) * (a[n,d]+b[n,d])
b[n+1,d]   = a[n,d]
```

Initial conditions: `a[1,1] = 1` and all other terms 0. The target polynomial is `P_n(z)=sum_d a[n,d]*z^d`, because the minus restriction forbids a repeated final entry. The top coefficients satisfy `a[n,n]=1` and `a[n,n-1]=2^(n-1)-2` for `n>=3`, by induction from the recurrence.

This type of distributional recurrence is *not claimed novel*: Martinez and Savage previously studied the `dist` statistic on pattern-restricted inversion sequences; the Chern–Fu paper cites their work and related formulas. The task of finding an explicit bijection remains open.

## Independent checks

- All seven published fibers for `n=3..9` match, with combined 4,983 objects.
- A separate exhaustive enumeration of all `n!` inversion sequences for `n=2..9` agrees with the dynamic program.
- Structural coefficients are checked for `n=3..24`.
- Passing these tests is not a mathematical proof of a bijection or worldwide originality.

## Next discriminating research experiment

Construct an **object-level map** `forward(matrix)` and `inverse(sequence)` that is natural and uniform in `n`; preserve the exact semi-weight/distinct-entry grade; test with qtBench's independent evaluator and its anti-tautology checks. Failure on any fiber disproves that candidate. Without such a map, the central problem is unanswered.

## Held-out n=10 prediction and validation

The DP predicts the following polynomial at n=10 (not included in the qtBench public n=3..9 table):

`P_10(z) = 1800 z^6 + 8400 z^7 + 5796 z^8 + 510 z^9 + z^10`, total 16,507.

Independently checked using `verify_n10.cpp`, which actually enumerates **all 10! = 3,628,800** inversion sequences and filters without using the DP recurrence. The checks matched. This extends a finite computational baseline, *not* a new general theorem.

Run with `g++ -std=c++17 -O2 verify_n10.cpp -o verify_n10 && ./verify_n10`.
