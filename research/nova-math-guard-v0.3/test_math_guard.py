#!/usr/bin/env python3
"""Dependency-free regression tests for NOVA Math Guard v0.2."""
import random
import unittest
from fractions import Fraction

import nova_math_guard as guard


class GuardTests(unittest.TestCase):
    def test_selftest(self):
        guard.selftest()

    def test_exact_fraction(self):
        self.assertEqual(guard.calculate('1/3 + 2/7'), 'EXACT: 13/21')
        self.assertEqual(guard.calculate('(-2)**(-3)'), 'EXACT: -1/8')

    def test_known_identity(self):
        self.assertTrue(guard.check_identity('(x+y)**2=x*x+2*x*y+y*y').startswith('PROVED:'))
        self.assertTrue(guard.check_identity('x-x=0').startswith('PROVED:'))

    def test_constant_false_identity(self):
        result = guard.check_identity('2=3')
        self.assertIn('DISPROVED:', result)
        self.assertIn('left=2; right=3', result)

    def test_exact_witness_multiple_roots(self):
        polynomial = guard.parse('x*(x-1)*(x-2)*(x-3)*(x-4)')
        assignment = guard.find_counterexample(polynomial)
        self.assertEqual(assignment, {'x': Fraction(5)})
        self.assertNotEqual(guard.evaluate(polynomial, assignment), 0)

    def test_multivariate_witness(self):
        polynomial = guard.parse('x*(x-1)*y*(y-1)*(y-2)')
        assignment = guard.find_counterexample(polynomial)
        self.assertEqual(assignment, {'x': Fraction(2), 'y': Fraction(3)})
        self.assertNotEqual(guard.evaluate(polynomial, assignment), 0)

    def test_cancelled_variables_receive_defaults(self):
        result = guard.check_identity('x+z=x+z+1')
        self.assertIn('DISPROVED:', result)
        self.assertIn('x=0, z=0', result)

    def test_linear_and_degenerate(self):
        self.assertIn('x = -9/2', guard.solve_linear('x/3+2=1/2'))
        self.assertIn('NO SOLUTION', guard.solve_linear('x-x=2'))
        self.assertIn('ALL RATIONAL VALUES', guard.solve_linear('x-x=0'))

    def test_reject_unsafe_and_unsupported(self):
        for text in ['0**0', '2**100', 'x**129', '1/0', '0.1', 'x**(1/2)',
                     '__import__("os")', '(x+1)**(-1)', 'x^3']:
            with self.subTest(text=text), self.assertRaises(guard.Unsupported):
                guard.parse(text)

    def test_deterministic_polynomial_witnesses(self):
        randomizer = random.Random(20261019)
        variables = ['x', 'y', 'z']
        for _ in range(500):
            terms = []
            for _ in range(randomizer.randint(1, 7)):
                coefficient = randomizer.randint(-6, 6)
                powers = [randomizer.randint(0, 3) for _ in variables]
                terms.append((coefficient, powers))
            fragments = []
            for coefficient, powers in terms:
                factors = [str(coefficient)]
                factors += [f'{variable}**{power}' for variable, power in zip(variables, powers) if power]
                fragments.append('*'.join(factors))
            expression = ' + '.join(f'({piece})' for piece in fragments)
            polynomial = guard.parse(expression)
            if not polynomial:
                continue
            assignment = guard.find_counterexample(polynomial)
            for variable in guard.variable_names(polynomial):
                self.assertIn(variable, assignment)
            self.assertNotEqual(guard.evaluate(polynomial, assignment), Fraction(0))


if __name__ == '__main__':
    unittest.main()
