"""Reproducible regression checks for certified Groebner completion."""
import copy
import random
import unittest
from fractions import Fraction

import nova_math_guard as g
from conditional_prover import certify
from groebner_prover import ideal_membership, sum_lifts
from independent_verifier import verify_certificate, VerificationError


class GroebnerTests(unittest.TestCase):
    def verified(self, givens, goal):
        certificate = certify(givens, goal)
        self.assertIn('VERIFIED PROVED', verify_certificate(certificate))
        return certificate

    def test_nontrivial_buchberger_pair(self):
        c = self.verified(['x*y=1', 'y**2=1'], 'x=y')
        self.assertEqual(c['goal'], 'x=y')

    def test_nontrivial_second_pair(self):
        self.verified(['x*y=1', 'y**2=1'], 'x**2=1')

    def test_new_polynomial_from_pair(self):
        self.verified(['x*y=1', 'y**2=1'], 'x**2-y**2=0')

    def test_order_invariance_of_implication(self):
        for givens in (['x*y=1', 'y**2=1'], ['y**2=1', 'x*y=1']):
            with self.subTest(givens=givens):
                self.verified(givens, 'x=y')

    def test_zero_and_repeated_hypotheses(self):
        self.verified(['x=x', 'x*y=1', 'x*y=1', 'y**2=1'], 'x=y')

    def test_not_every_logical_consequence_is_ideal_membership(self):
        with self.assertRaisesRegex(g.Unsupported, 'UNKNOWN'):
            certify(['x**2=0'], 'x=0')

    def test_not_a_consequence(self):
        with self.assertRaisesRegex(g.Unsupported, 'UNKNOWN'):
            certify(['x*y=1', 'y**2=1'], 'x=2')

    def test_tampered_new_certificate_is_rejected(self):
        cert = self.verified(['x*y=1', 'y**2=1'], 'x=y')
        altered = copy.deepcopy(cert)
        altered['goal'] = 'x=y+1'
        with self.assertRaises(VerificationError):
            verify_certificate(altered)
        altered = copy.deepcopy(cert)
        altered['evidence']['multipliers_normal_forms'][0] = []
        with self.assertRaises(VerificationError):
            verify_certificate(altered)

    def test_seeded_ideal_membership_certificate(self):
        rng = random.Random(20261019)
        f = [g.parse('x*y-1'), g.parse('y**2-1')]
        for trial in range(250):
            multipliers = []
            for _ in f:
                coeffs = [rng.randint(-4, 4) for _ in range(4)]
                text = f'({coeffs[0]})+({coeffs[1]})*x+({coeffs[2]})*y+({coeffs[3]})*x*y'
                multipliers.append(g.parse(text))
            goal = sum_lifts(multipliers, f)
            result = ideal_membership(goal, f)
            self.assertEqual(goal, sum_lifts(result, f), msg=f'trial={trial}')

    def test_synthetic_zero_target(self):
        generators = [g.parse('x**2-1'), g.parse('x*y-1')]
        coeffs = ideal_membership({}, generators)
        self.assertEqual(sum_lifts(coeffs, generators), {})


if __name__ == '__main__':
    unittest.main()
