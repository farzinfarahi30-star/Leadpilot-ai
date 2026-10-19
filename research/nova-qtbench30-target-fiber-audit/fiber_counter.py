#!/usr/bin/env python3
"""Exact grading counter for qtBench 30 restricted inversion sequences.

Independent of qtBench implementation. No web/network, no paid APIs.
Only the TARGET class is counted; this DOES NOT construct the demanded bijection.
"""
from collections import defaultdict
import json
import argparse

# Public count targets for n=3..9 transcribed and separately checked from
# SwagCai/qtBench/problems/exchanging_bijection/
# improper_partition_matrix_inversion_sequence_bijection/data/polynomials.json
PUBLIC_TARGET = {
    3: {2: 2, 3: 1},
    4: {3: 6, 4: 1},
    5: {3: 6, 4: 14, 5: 1},
    6: {4: 36, 5: 30, 6: 1},
    7: {4: 24, 5: 150, 6: 62, 7: 1},
    8: {5: 240, 6: 540, 7: 126, 8: 1},
    9: {5: 120, 6: 1560, 7: 1806, 8: 254, 9: 1},
}


def count_fibers(max_n=20):
    """Return distributions of minus class by length n.

    a_n[d] counts valid e_1...e_n with d distinct values and final value new.
    b_n[d] counts valid e_1...e_n with d distinct values and final value the
    second entry in an adjacent equal pair. No value may appear otherwise.
    For n+1, there are (n+1-d) unused values in range [0,n].
    """
    if not 1 <= max_n <= 300:
        raise ValueError('max_n must be from 1 to 300')
    a, b = {1: 1}, {}
    result = {}
    for n in range(1, max_n + 1):
        result[n] = dict(sorted(a.items()))
        nxt_a, nxt_b = defaultdict(int), defaultdict(int)
        for d, ways in a.items():
            nxt_a[d+1] += (n+1-d)*ways
            nxt_b[d] += ways
        for d, ways in b.items():
            nxt_a[d+1] += (n+1-d)*ways
        a, b = dict(nxt_a), dict(nxt_b)
    return result


def independent_brute(n):
    """Enumerate all n! inversion sequences and filter independently.

    This implementation intentionally does not use the A/B recurrence.
    """
    from itertools import product
    if not 1 <= n <= 9:
        raise ValueError('brute-force range is 1..9')
    result = defaultdict(int)
    for entries in product(*(range(i) for i in range(1,n+1))):
        if any(entries[i] == entries[k]
               for i in range(n) for k in range(i+2, n)):
            continue
        if n >= 2 and entries[-1] == entries[-2]:
            continue
        result[len(set(entries))] += 1
    return dict(sorted(result.items()))


def check():
    dp = count_fibers(24)
    for n, expected in PUBLIC_TARGET.items():
        assert dp[n] == expected, (n, dp[n], expected)
    assert sum(sum(x.values()) for x in PUBLIC_TARGET.values()) == 4983
    for n in range(2, 10):
        assert dp[n] == independent_brute(n), (n, dp[n], independent_brute(n))
    for n in range(3, 25):
        assert dp[n][n] == 1
        assert dp[n][n-1] == 2**(n-1)-2
    return True


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--max-n',type=int,default=15)
    p.add_argument('--check',action='store_true')
    p.add_argument('--json',action='store_true')
    args=p.parse_args()
    if args.check:
        check()
        print('PASS: 7 public target fibers, 8 independent exhaustive brute-force cases, and top-grading identities n=3..24.')
        return
    result=count_fibers(args.max_n)
    if args.json:
        print(json.dumps({str(n): {str(k): v for k,v in row.items()} for n,row in result.items()},indent=2))
    else:
        for n,row in result.items():
            print(f'n={n:<3} minus-total={sum(row.values()):<15} fiber={row}')

if __name__=='__main__':
    main()
