"""Independent exhaustive source-side check of the Chern--Fu properness rule.

Warning: exponential exhaustive enumeration; n<=8 in intended use.
"""
from collections import Counter
from itertools import product
from diagonal_bijection import compositions, diagonal_fibers


def source_fibers(n):
    counts=Counter(); matrix_count=0; witnesses=[]
    for comp in compositions(n):
        d=len(comp)
        col_of=[]; ranges=[]; start=0
        for j,a in enumerate(comp,1):
            ranges.append(range(start,start+a)); col_of.extend([j]*a); start+=a
        for rowblocks in product(*(product(range(1,j+1), repeat=a) for j,a in enumerate(comp,1))):
            rows=sum((list(x) for x in rowblocks), [])
            if len(set(rows))!=d: continue
            if any(rows[i]!=rows[i+1] and (i - next(r.start for r in ranges if i in r))%2==0
                   for i in range(n-1) if col_of[i]==col_of[i+1]):
                continue
            # The cell containing label n must have odd cardinality.
            last_row=rows[-1];last_col=col_of[-1]
            if sum(rows[i]==last_row and col_of[i]==last_col for i in range(n))%2 !=1:
                continue
            matrix_count+=1
            counts[sum((a+1)//2 for a in comp)]+=1
            if any(rows[i]!=col_of[i] for i in range(n)) and len(witnesses)<2:
                witnesses.append({'composition':comp,'rows':tuple(rows),'grading':sum((a+1)//2 for a in comp)})
    return counts,witnesses

if __name__=='__main__':
    expected={3:{2:2,3:1},4:{3:6,4:1},5:{3:6,4:14,5:1},6:{4:36,5:30,6:1},7:{4:24,5:150,6:62,7:1},8:{5:240,6:540,7:126,8:1}}
    for n in range(3,9):
        actual,w=source_fibers(n)
        assert dict(actual)==expected[n],(n,actual,expected[n])
        dc=diagonal_fibers(n)
        print(n,'source=',sum(actual.values()),'diagonal=',sum(dc.values()),'remainder=',sum(actual.values())-sum(dc.values()),'first_offdiagonal=',w[:1])
    print('PASS independent source-side count and grading n=3..8')
