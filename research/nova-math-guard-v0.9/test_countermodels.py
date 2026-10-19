#!/usr/bin/env python3
"""Exact and adversarial checks for v0.7 proof-or-counterexample results."""
import copy
from fractions import Fraction
import random
import unittest

import conditional_counterexample as cm
import nova_math_guard as g
from independent_verifier import VerificationError, verify_certificate


class CountermodelTests(unittest.TestCase):
    def test_nontrivial_inverse_countermodel(self):
        c = cm.counterexample(['x*y=1'], 'x=y')
        self.assertEqual(c['evidence']['assignment'], {'x': '2', 'y': '1/2'})
        self.assertIn('VERIFIED DISPROVED', verify_certificate(c))

    def test_two_hypotheses_and_exact_fractions(self):
        c = cm.counterexample(['x*y=1', 'y=1/2'], 'x=3')
        self.assertEqual(c['evidence']['assignment'], {'x': '2', 'y': '1/2'})
        self.assertEqual(c['evidence']['goal_values'], {'lhs': '2', 'rhs': '3'})
        verify_certificate(c)

    def test_false_implication_no_variables(self):
        c = cm.counterexample(['2=2'], '0=1')
        self.assertEqual(c['evidence']['assignment'], {})
        verify_certificate(c)

    def test_no_counterexample_to_true_implication(self):
        with self.assertRaisesRegex(g.Unsupported, 'UNKNOWN:'):
            cm.counterexample(['x**2=0'], 'x=0', max_points=200)

    def test_inconsistent_assumptions_not_refuted(self):
        with self.assertRaisesRegex(g.Unsupported, 'UNKNOWN:'):
            cm.counterexample(['1=0'], 'x=2', max_points=200)

    def test_real_only_implication_not_overclaimed(self):
        with self.assertRaisesRegex(g.Unsupported, 'UNKNOWN:'):
            cm.counterexample(['x**2+y**2=0'], 'x=0', max_points=100)

    def test_unknown_under_bounded_grid(self):
        with self.assertRaisesRegex(g.Unsupported, 'UNKNOWN:'):
            cm.counterexample(['x=31'], 'x=0', max_points=3)

    def test_decide_proves_radical_consequence(self):
        c = cm.decide(['x**2=0'], 'x=0')
        self.assertEqual(c['verdict'], 'PROVED')
        verify_certificate(c)

    def test_decide_refutes_invalid_consequence(self):
        c = cm.decide(['x*y=1'], 'x=y')
        self.assertEqual(c['verdict'], 'DISPROVED')
        verify_certificate(c)

    def test_exact_fraction_input_and_no_floats(self):
        c = cm.counterexample(['x=1/3'], 'x=0', grid_values=['1/3'])
        self.assertEqual(c['evidence']['assignment'], {'x': '1/3'})
        with self.assertRaises(g.Unsupported):
            cm.counterexample(['x=0'], 'x=1', grid_values=[0.0])

    def test_tamper_rejected(self):
        c = cm.counterexample(['x*y=1'], 'x=y')
        mutations = []
        for path, value in [
            (('evidence', 'assignment', 'x'), '1'),
            (('evidence', 'assignment', 'y'), '1'),
            (('evidence', 'goal_values', 'lhs'), '1'),
            (('evidence', 'goal_values', 'rhs'), '2'),
            (('evidence', 'hypotheses_values'), []),
            (('goal',), 'x*y=1'),
            (('hypotheses',), ['x*y=2']),
            (('schema',), 'imaginary-certificate'),
            (('verdict',), 'PROVED'),
            (('domain',), 'Real-polynomial'),
        ]:
            d = copy.deepcopy(c)
            item = d
            for p in path[:-1]:
                item = item[p]
            item[path[-1]] = value
            mutations.append(d)
        for i, altered in enumerate(mutations):
            with self.subTest(case=i), self.assertRaises(VerificationError):
                verify_certificate(altered)

    def test_randomized_exact_countermodels(self):
        rng = random.Random(20261019)
        for i in range(400):
            a = rng.randint(-3, 3)
            b = rng.randint(-3, 3)
            x = rng.choice([v for v in range(-3,4) if v != a])
            # h=(x-a)(y-b)=0 is true for y=b; x=a is false at x != a.
            hypothesis = f'(x-({a}))*(y-({b}))=0'
            goal = f'x=({a})'
            c = cm.counterexample([hypothesis], goal,
                                  grid_values=[x,b], max_points=4)
            self.assertEqual(c['verdict'], 'DISPROVED')
            self.assertIn('VERIFIED DISPROVED', verify_certificate(c))

    def test_reject_too_many_variables(self):
        with self.assertRaisesRegex(g.Unsupported, 'too many variables'):
            cm.counterexample(['a+b+c+d+e+f+g=0'], 'a=1')

    def test_reject_extreme_grid(self):
        with self.assertRaises(g.Unsupported):
            cm.counterexample(['x=0'], 'x=1', grid_values=['1' * 81])


if __name__ == '__main__':
    unittest.main()
