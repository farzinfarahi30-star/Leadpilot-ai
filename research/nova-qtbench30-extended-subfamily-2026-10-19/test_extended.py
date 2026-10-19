"""Independent checks of all conditions and exhaustive small-size target tests."""
import sys, unittest, itertools, math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from extended_bijection import *
from collections import Counter


def independent_matrix_valid(m):
    """Validate actual row/col indices without using encode or constructor's assertions."""
    cols,rows=m.matrix()
    n=m.n; d=max(cols)
    assert len(cols)==len(rows)==n
    assert set(cols)==set(range(1,d+1))
    assert set(rows)==set(range(1,d+1))
    assert all(1<=row<=col<=d for row,col in zip(rows,cols))
    assert all(cols[i]<=cols[i+1] for i in range(n-1))
    for i in range(n-1):
        if cols[i]!=cols[i+1]:continue
        start=next(j for j in range(n) if cols[j]==cols[i])
        if (i-start)%2==0:
            assert rows[i]==rows[i+1],('proper step occurred',m,rows)
    assert sum(rows[j]==rows[-1] and cols[j]==cols[-1] for j in range(n))%2==1
    grade=sum((cols.count(c)+1)//2 for c in range(1,d+1))
    assert grade==n-1


class ExtendedProofTest(unittest.TestCase):
    def test_new_source_membership(self):
        for n in range(4,40):
            for m in all_offdiagonal(n):
                with self.subTest(m=m):independent_matrix_valid(m)

    def test_target_and_inverse_large(self):
        for n in range(4,81):
            sources=list(all_offdiagonal(n)); images=[offdiag_encode(x) for x in sources]
            self.assertEqual(len(images),2*(n-3))
            self.assertEqual(len(set(images)),len(images))
            for obj,image in zip(sources,images):
                self.assertTrue(valid_target(image))
                self.assertEqual(n-1,len(set(image)))
                self.assertEqual(obj,offdiag_decode(image))
                self.assertEqual(obj,extended_decode(image))

    def test_disjoint_diagonal_and_new(self):
        for n in range(4,14):
            old={encode(c) for c in compositions(n) if c[-1]%2}
            new={offdiag_encode(obj) for obj in all_offdiagonal(n)}
            self.assertFalse(old & new)
            self.assertTrue(all(extended_decode(e) in list(all_offdiagonal(n)) for e in new))
            self.assertEqual(extended_count(n),len(old)+len(new))

    def test_small_exhaustive_target(self):
        for n in range(4,9):
            target={e for e in itertools.product(*(range(i) for i in range(1,n+1))) if valid_target(e)}
            old={encode(c) for c in compositions(n) if c[-1]%2}
            new={offdiag_encode(obj) for obj in all_offdiagonal(n)}
            self.assertTrue(old|new<=target)
            self.assertFalse(old & new)
            if n==4:
                self.assertEqual(old|new,target)
            else:
                self.assertLess(len(old|new),len(target))

    def test_negative_decoder(self):
        cases=[(),(0,0,1),(0,0,1,1),(0,0,3,1), (0,0,2,2),
               (0,0,1,2,2),(0,0,1,3,4),(0,0,2,3,4)]
        for e in cases:
            with self.subTest(e=e),self.assertRaises(ValueError):offdiag_decode(e)

    def test_original_diagonal_unmodified(self):
        for n in range(2,13):
            for c in compositions(n):
                if c[-1]%2:
                    e=extended_encode(c)
                    self.assertEqual(extended_decode(e),c)
                    self.assertEqual(len(set(e)),semi_weight(c))

    def test_generating_function(self):
        from sympy import symbols, series, expand
        x,z=symbols('x z')
        F=(z*x/(1-z*x-2*z*x*x))+(2*z**3*x**4/((1-z*x)**2))
        S=series(F,x,0,13).removeO().expand()
        for n in range(1,13):
            expected=Counter(semi_weight(c) for c in compositions(n) if c[-1]%2)
            if n>=4:expected[n-1]+=2*(n-3)
            self.assertEqual(expand(S.coeff(x,n)-sum(count*z**grade for grade,count in expected.items())),0)


# Source-side enumeration is independent of the construction.
class SourceCoverage(unittest.TestCase):
    def test_small_source_membership_and_full_n4(self):
        from independent_source import source_words,diagonal_matrix
        published={4:{3:6,4:1},5:{3:6,4:14,5:1},6:{4:36,5:30,6:1},7:{4:24,5:150,6:62,7:1}}
        for n in range(4,8):
            allsource=source_words(n)
            diag={diagonal_matrix(c) for c in compositions(n) if c[-1]%2}
            off={o.matrix() for o in all_offdiagonal(n)}
            self.assertFalse(diag&off)
            self.assertTrue(diag|off<=set(allsource))
            self.assertEqual(dict(sorted(Counter(allsource.values()).items())),published[n])
            if n==4:
                self.assertEqual(diag|off,set(allsource))


if __name__=="__main__":
    unittest.main(verbosity=2)
