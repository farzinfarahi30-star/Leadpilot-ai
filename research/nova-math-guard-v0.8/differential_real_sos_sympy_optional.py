#!/usr/bin/env python3
"""Optional exact SymPy checks of 300 random rational quadratic SOS decompositions."""
import random
from fractions import Fraction
import sympy as sp
import nova_math_guard as g
from real_sos_prover import quadratic_sos

rng = random.Random(20261019)
x, y, z = sp.symbols('x y z')

def sympy_poly(p):
    s = sp.Integer(0)
    for monomial, coefficient in p.items():
        term = sp.Rational(coefficient.numerator, coefficient.denominator)
        for var, degree in monomial:
            term *= {'x': x, 'y': y, 'z': z}[var] ** degree
        s += term
    return sp.expand(s)

for trial in range(300):
    sos = {}
    for _ in range(rng.randint(1, 4)):
        linear = {}
        for name in 'xyz':
            c = Fraction(rng.randint(-4, 4), rng.randint(1, 5))
            if c:
                linear[((name, 1),)] = c
        constant = Fraction(rng.randint(-4, 4), rng.randint(1, 5))
        if constant:
            linear[()] = constant
        weight = Fraction(rng.randint(1, 4), rng.randint(1, 5))
        sos = g.add(sos, g.scale(g.mul(linear, linear), weight))
    pieces = quadratic_sos(sos)
    assert pieces is not None
    actual = sp.Integer(0)
    for weight, polynomial in pieces:
        actual += sp.Rational(weight.numerator, weight.denominator) * sympy_poly(polynomial) ** 2
    assert sp.expand(actual - sympy_poly(sos)) == 0, (trial, actual, sos)
print('PASS: 300 randomized rational SOS identities checked independently with SymPy')
