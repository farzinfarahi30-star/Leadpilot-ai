"""Independent CLI regression/negative-case checks for paper's explicit map."""
import itertools
from collections import Counter
from diagonal_bijection import encode, decode, compositions, semi_weight, valid_target, diagonal_fibers

def run():
    assert encode((3,)) == (0,0,1)
    assert encode((2,1)) == (0,0,2)
    assert encode((1,3)) == (0,1,1,2)
    assert encode((1,1,1)) == (0,1,2)
    for bad in [(),(2,), (1,0,1), (1,-1,1), ('x',1)]:
        try: encode(bad)
        except ValueError: pass
        else: raise AssertionError(('accepted invalid composition',bad))
    for bad in [(0,0,1,2),(0,0,2,1), (0,1,1,3,3),(0,1,0), (0,0,0), (0,0), ()]:
        try: decode(bad)
        except ValueError: pass
        else: raise AssertionError(('accepted nonimage',bad))
    for n in range(2,10):
        full = {v for v in itertools.product(*(range(i) for i in range(1,n+1))) if valid_target(v)}
        image = {encode(c) for c in compositions(n) if c[-1]%2}
        assert image <= full
        assert len(image) == len(set(image))
        assert Counter(len(set(s)) for s in image) == diagonal_fibers(n)
        if n == 4:
            assert full - image == {(0,0,1,2), (0,0,2,1)}
    print('PASS: negative tests; independent full inversion-sequence enumeration n=2..9; n=4 missing cases certified')
if __name__ == '__main__': run()
