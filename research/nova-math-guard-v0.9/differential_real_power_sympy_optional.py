#!/usr/bin/env python3
"""External polynomial identity checks for 300 generated even-power real-SOS witnesses.

Requires SymPy 1.x. This verifies exact polynomial equalities independently
from NOVA's algebra representation; it cannot prove program soundness.
"""
import random
import sympy as s

from independent_verifier import verify_certificate
from real_sos_prover import certify

x, y = s.symbols('x y')


def from_normal_form(entries):
    result = s.Integer(0)
    for term in entries:
        coeff = s.Rational(term['coefficient'])
        for name, power in term['monomial']:
            coeff *= {'x': x, 'y': y}[name]**power
        result += coeff
    return s.expand(result)


def independent_check(cert):
    hpoly = []
    for eq in cert['hypotheses']:
        lhs, rhs = eq.split('=')
        hpoly.append(s.sympify(lhs, locals={'x': x, 'y': y}) - s.sympify(rhs, locals={'x': x, 'y': y}))
    lhs, rhs = cert['goal'].split('=')
    target = s.sympify(lhs, locals={'x': x, 'y': y}) - s.sympify(rhs, locals={'x': x, 'y': y})
    ev = cert['evidence']
    difference = s.expand(target ** ev['goal_even_power'])
    for sq in ev['weighted_squares']:
        difference += s.Rational(sq['weight']) * from_normal_form(sq['polynomial_normal_form'])**2
    for hypothesis, multiplier in zip(hpoly, ev['multipliers_normal_forms']):
        difference -= hypothesis * from_normal_form(multiplier)
    return s.Poly(s.expand(difference), x, y).is_zero


def run():
    rng = random.Random(190926)
    for i in range(300):
        power = rng.choice((2, 4, 6, 8))
        a, b = rng.randint(1, 5), rng.randint(1, 5)
        equation = f'{a}*x**{power}+{b}*y**{power}=0'
        cert = certify([equation], 'x=0')
        assert 'VERIFIED PROVED:' in verify_certificate(cert), f'failed certificate {i}'
        assert independent_check(cert), f'SymPy found nonzero polynomial difference in test {i}'
    print('PASS: 300 exact even-power SOS certificates cross-checked against SymPy')


if __name__ == '__main__':
    run()
