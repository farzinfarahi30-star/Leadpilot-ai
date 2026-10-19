"""NOVA qtBench30: infinite, grade-preserving partial bijection beyond the diagonal.

No claims of full solution or of worldwide mathematical originality.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

from diagonal_bijection import encode, decode, valid_target, compositions, semi_weight


@dataclass(frozen=True)
class OffDiagonal:
    n: int
    row: int
    kind: Literal['A', 'B']

    def validate(self) -> None:
        if type(self.n) is not int or self.n < 4:
            raise ValueError('requires n >= 4')
        if type(self.row) is not int or not 1 <= self.row <= self.n-3:
            raise ValueError('row outside 1..n-3')
        if self.kind not in ('A','B'):
            raise ValueError('kind must be A or B')

    def matrix(self) -> tuple[tuple[int,...],tuple[int,...]]:
        """The column and row indices of labels 1...n, respectively."""
        self.validate()
        d=self.n-2
        columns=tuple(range(1,d))+ (d,d,d)
        rows=tuple(range(1,d)) + ((d,d,self.row) if self.kind=='A' else (self.row,self.row,d))
        assert len(rows)==self.n and len(columns)==self.n
        return columns,rows


def offdiag_encode(m: OffDiagonal) -> tuple[int,...]:
    """Map the terminal three-label-column source family to unused target words."""
    m.validate()
    n,r=m.n,m.row
    if m.kind=='A':
        tail=list(range(2,n-1))  # 2,...,n-2
        tail.insert(r,1)         # position r in zero-based tail
    else:
        tail=list(range(1,n-1))  # 1,...,n-2
        if r >= 2:
            tail[r-1],tail[r]=tail[r],tail[r-1]
    return tuple([0,0]+tail)


def offdiag_decode(seq: tuple[int,...]) -> OffDiagonal:
    """Exact inverse on *only* the newly added target family."""
    n=len(seq)
    if n<4 or seq[:2]!=(0,0):
        raise ValueError('not an extended-family word')
    tail=seq[2:]
    if tuple(sorted(tail))!=tuple(range(1,n-1)):
        raise ValueError('suffix must be a permutation of 1..n-2')
    if tail[0]==2:
        r=tail.index(1)
        if r<1 or r>n-3:
            raise ValueError('invalid A-row')
        obj=OffDiagonal(n,r,'A')
    elif tail[0]==1:
        base=list(range(1,n-1))
        if tail==tuple(base):
            obj=OffDiagonal(n,1,'B')
        else:
            matches=[]
            for r in range(2,n-2):
                t=base.copy()
                t[r-1],t[r]=t[r],t[r-1]
                if tuple(t)==tail:
                    matches.append(r)
            if len(matches)!=1: raise ValueError('not a canonical B-word')
            obj=OffDiagonal(n,matches[0],'B')
    else:
        raise ValueError('invalid first suffix value')
    if offdiag_encode(obj)!=seq:
        raise ValueError('noncanonical word')
    return obj


def extended_encode(source):
    """Disjoint union: original diagonal compositions and tagged off-diagonal subfamily."""
    if isinstance(source, OffDiagonal): return offdiag_encode(source)
    if isinstance(source,tuple): return encode(source)
    raise ValueError('unrecognized source')


def extended_decode(seq:tuple[int,...]):
    try: return decode(seq)
    except ValueError: return offdiag_decode(seq)


def offdiag_grade(m:OffDiagonal)->int:
    m.validate()
    return m.n-1


def extra_count(n:int)->int:
    return max(0,2*(n-3)) if n>=4 else 0


def extended_count(n:int)->int:
    return (2**n-(-1)**n)//3 + extra_count(n)


def all_offdiagonal(n:int):
    if n<4:return
    for r in range(1,n-2):
        for kind in ('A','B'):
            yield OffDiagonal(n,r,kind)


if __name__=='__main__':
    for n in range(4,13):
        objs=list(all_offdiagonal(n))
        words=[offdiag_encode(m) for m in objs]
        assert len(set(words))==len(words)==2*(n-3)
        assert all(valid_target(e) and len(set(e))==n-1 for e in words)
        assert all(offdiag_decode(w)==m for m,w in zip(objs,words))
        print(n,len(words),extended_count(n))
