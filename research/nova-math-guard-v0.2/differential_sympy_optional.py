#!/usr/bin/env python3
"""Optional independent differential tests (requires sympy)."""
import random
import sympy as s
import nova_math_guard as g
rng = random.Random(631919)
vars = s.symbols('x y z')
names = ['x','y','z']
def random_p():
    texts=[]
    sym=s.Integer(0)
    for _ in range(rng.randrange(1,5)):
        c=rng.randrange(-9,10)
        d=rng.randrange(1,10)
        exps=[rng.randrange(0,5) for _ in range(3)]
        term = s.Rational(c,d)
        t=f'({c}/{d})'
        for name,var,e in zip(names,vars,exps):
            if e:
                t+=f'*{name}**{e}'
                term*=var**e
        texts.append('('+t+')')
        sym+=term
    return '+'.join(texts),s.expand(sym)
for i in range(3000):
    a,sa=random_p()
    b,sb=random_p()
    atext=a if i%2 else f'({a})+({b})-({b})'
    if len(atext)>490 or len(atext)+len(b)+1>500:
        continue
    gg=g.parse(atext)
    ours=g.evaluate(gg,{'x':s.Rational(2,3),'y':s.Rational(-1,2),'z':s.Rational(5,7)})
    expected=sa.subs(dict(zip(vars,[s.Rational(2,3),s.Rational(-1,2),s.Rational(5,7)])))
    assert s.Rational(ours.numerator,ours.denominator)==expected,(i,a,b,ours,expected)
    mode=g.check_identity(atext+'='+b)
    equal=s.expand(sa-sb)==0
    assert mode.startswith('PROVED:')==equal,(i,mode,a,b)
print('PASS: 3,000 independently cross-checked rational-polynomial comparisons with SymPy')
