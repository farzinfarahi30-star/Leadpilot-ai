"""Explicit grade-preserving injection from diagonal improper partition matrices.

Each composition of n with odd final part encodes a diagonal partition
matrix (each column has only one nonempty diagonal cell).
Every diagonal partition matrix is 'improper' in the Chern--Fu sense.
"""
from __future__ import annotations
from collections import Counter
from functools import lru_cache


def compositions(n: int):
    if n < 1: raise ValueError("n must be positive")
    for mask in range(1 << (n - 1)):
        parts, k = [], 1
        for p in range(n - 1):
            if mask & (1 << p):
                parts.append(k); k = 1
            else: k += 1
        parts.append(k)
        yield tuple(parts)


def encode(parts: tuple[int, ...]) -> tuple[int, ...]:
    """Map a composition with odd last part to an inversion sequence.

    For each part, tile 2,2,...,2,(1 if odd). Each tile is labeled either
    its starting position minus one (new part) or the smallest unused
    nonnegative integer (continuation within the same part).
    """
    if not parts or any(type(k) is not int or k < 1 for k in parts) or parts[-1] % 2 != 1:
        raise ValueError("requires a positive composition ending in an odd part")
    seq, used = [], set()
    for a in parts:
        remaining, first = a, True
        while remaining:
            group_size = 2 if remaining >= 2 else 1
            j = len(seq) + 1
            if first:
                val = j-1
            else:
                val = next(i for i in range(j) if i not in used)
                assert val < j-1, 'interior tile has a previous doubled position'
            assert val not in used
            used.add(val)
            seq.extend([val]*group_size)
            remaining -= group_size
            first = False
    return tuple(seq)


def decode(seq: tuple[int, ...]) -> tuple[int, ...]:
    """Inverse on the image. Reject words outside the explicit image."""
    n = len(seq)
    if n == 0 or any(type(v) is not int or v < 0 or v >= i for i,v in enumerate(seq, 1)):
        raise ValueError("not an inversion sequence")
    starts, j, used = [], 1, set()
    while j <= n:
        value = seq[j-1]
        if value in used:
            raise ValueError('non-adjacent repetition')
        if value == j-1:
            starts.append(j-1)
        else:
            unused = next((i for i in range(j) if i not in used), None)
            if not starts or unused is None or value != unused:
                raise ValueError('not a permitted interior group')
        used.add(value)
        step = 2 if j < n and seq[j] == value else 1
        j += step
    if not starts: raise ValueError('missing initial block')
    parts = tuple((starts[i+1] if i+1 < len(starts) else n) - k for i,k in enumerate(starts))
    if parts[-1] % 2 != 1 or encode(parts) != seq:
        raise ValueError('not a canonical image word')
    return parts


def semi_weight(parts: tuple[int,...]) -> int:
    return sum((a+1)//2 for a in parts)


def valid_target(seq: tuple[int,...]) -> bool:
    if not seq or any(v<0 or v>=i for i,v in enumerate(seq,1)): return False
    if len(seq)>1 and seq[-1] == seq[-2]: return False
    positions = {}
    for i,v in enumerate(seq):
        positions.setdefault(v,[]).append(i)
    return all(len(v)==1 or len(v)==2 and v[1]==v[0]+1 for v in positions.values())


def target_fibers(n: int):
    """Standalone exhaustive recursion for target inversion-sequence class."""
    if n < 1: raise ValueError(n)
    # State = (values used so far, previous symbol, grading).
    # No symbol can reappear except to complete one immediate adjacent pair.
    @lru_cache(None)
    def visit(i, used, last, was_repeat, distinct):
        if i > n:
            return Counter({distinct: 1})
        sums = Counter()
        for v in range(i):
            if v in used:
                if v != last or was_repeat or i == n:
                    continue
                next_grading, rep, new_used = distinct, True, used
            else:
                next_grading, rep, new_used = distinct+1, False, used | {v}
            if i == n and v == last:
                continue
            sums.update(visit(i+1, new_used, v, rep, next_grading))
        return sums
    # For i=1 only 0 is available, and no pair can end at n=1 (minus convention).
    return visit(2, frozenset({0}), 0, False, 1) if n>=2 else Counter({1: 1})


def diagonal_fibers(n: int):
    return Counter(semi_weight(c) for c in compositions(n) if c[-1]%2 == 1)


if __name__ == '__main__':
    for n in range(2, 13):
        pairs = [(c, encode(c)) for c in compositions(n) if c[-1]%2 == 1]
        assert len({w for _,w in pairs}) == len(pairs)
        for c,w in pairs:
            assert valid_target(w), (c,w)
            assert decode(w) == c, (c,w,decode(w))
            assert len(set(w)) == semi_weight(c), (c,w)
        counts = diagonal_fibers(n)
        assert sum(counts.values()) == (2**n - (-1)**n)//3
        target_counts = target_fibers(n)
        assert all(counts[k] <= target_counts[k] for k in counts), (n,counts,target_counts)
        print('n=', n, 'injected=', sum(counts.values()), 'target=', sum(target_counts.values()),
              'grades=', dict(sorted(counts.items())))
    print('PASS: all image validity, grade, uniqueness, inverse, and target subset checks n=2..12')
