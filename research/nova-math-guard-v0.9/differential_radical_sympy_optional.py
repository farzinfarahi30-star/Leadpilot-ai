#!/usr/bin/env python3
"""Optional independent SymPy expansion checks of 300 random power certificates."""
import random

import sympy as sp

from radical_prover import certify
from independent_verifier import verify_certificate


def sympy_form(form, symbols):
    total = sp.Integer(0)
    for monomial in form:
        term = sp.Rational(monomial['coefficient'])
        for name, exponent in monomial['monomial']:
            term *= symbols[name] ** exponent
        total += term
    return sp.expand(total)


def main():
    rng = random.Random(261019)
    symbols = {name: sp.Symbol(name) for name in 'xyz'}
    x, y, z = symbols.values()
    for i in range(300):
        coefficients = [rng.randrange(-5, 6) for _ in range(3)]
        if not any(coefficients):
            coefficients[0] = 1
        p = '+'.join(f'({c})*{name}' for c, name in zip(coefficients, 'xyz'))
        k = 2 if i % 3 else 3
        hypotheses = [f'({p})**{k}=0']
        certificate = certify(hypotheses, f'({p})=0', max_power=3)
        assert certificate['kind'] == 'radical'
        assert certificate['evidence']['power'] == k
        assert verify_certificate(certificate).startswith('VERIFIED PROVED')
        f = sum(c * symbols[name] for c, name in zip(coefficients, 'xyz'))
        target = f ** k
        reconstruction = sympy_form(certificate['evidence']['multipliers_normal_forms'][0], symbols) * target
        assert sp.expand(target-reconstruction) == 0, i
    print('PASS: 300 randomized radical witnesses independently expanded by SymPy')


if __name__ == '__main__':
    main()
