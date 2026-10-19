"""Independent exhaustive small-n source validator / coverage (no package dependencies)."""
from itertools import product
from diagonal_bijection import compositions


def source_words(n):
    """Returns canonical (col tuple, row tuple) for original improper-minus matrices."""
    matrices={}
    for comp in compositions(n):
        d=len(comp)
        cols=tuple(j for j,size in enumerate(comp,1) for _ in range(size))
        for rows in product(*(range(1,j+1) for j in cols)):
            if set(rows)!=set(range(1,d+1)):
                continue
            starts={j:cols.index(j) for j in range(1,d+1)}
            if any(rows[i]!=rows[i+1] and (i-starts[cols[i]])%2==0 for i in range(n-1) if cols[i]==cols[i+1]):
                continue
            if sum(rows[i]==rows[-1] and cols[i]==cols[-1] for i in range(n))%2!=1:
                continue
            grade=sum((size+1)//2 for size in comp)
            matrices[(cols,rows)]=grade
    return matrices


def diagonal_matrix(comp):
    cols=tuple(j for j,size in enumerate(comp,1) for _ in range(size))
    return cols,cols
