import copy
import random
import unittest
from fractions import Fraction

import nova_math_guard as g
from independent_verifier import VerificationError, verify_certificate
from real_sos_prover import certify, decide, quadratic_sos


class RealSOSTests(unittest.TestCase):
    def verify(self, given, goal):
        result = certify(given, goal)
        self.assertEqual(result['kind'], 'real-sos')
        self.assertIn('VERIFIED PROVED', verify_certificate(result))
        return result

    def test_real_not_complex(self):
        self.verify(['x**2+y**2=0'], 'x=0')
        # At complex point x=i,y=1, premise x^2+y^2=0, goal x=0 fails.

    def test_scaling(self):
        self.verify(['4*x**2+9*y**2=0'], 'x=0')

    def test_square_with_cross_terms(self):
        self.verify(['(x+y)**2+z**2=0'], 'x+y=0')

    def test_two_hypotheses(self):
        self.verify(['x**2+y**2=0', 'z**2+w**2=0'], 'x+z=0')

    def test_invalid_complex_domain_rejected(self):
        bad = self.verify(['x**2+y**2=0'], 'x=0')
        bad['domain'] = 'Q-polynomial'
        with self.assertRaises(VerificationError):
            verify_certificate(bad)

    def test_bad_negative_weight_rejected(self):
        bad = self.verify(['x**2+y**2=0'], 'x=0')
        bad['evidence']['weighted_squares'][0]['weight'] = '-1'
        with self.assertRaises(VerificationError):
            verify_certificate(bad)

    def test_bad_gram_polynomial_rejected(self):
        bad = self.verify(['x**2+y**2=0'], 'x=0')
        bad['evidence']['weighted_squares'][0]['polynomial_normal_form'][0]['coefficient'] = '3'
        with self.assertRaises(VerificationError):
            verify_certificate(bad)

    def test_degenerate_psd_gram(self):
        result = quadratic_sos(g.parse('(2*x-3*y)**2'))
        self.assertIsNotNone(result)
        total = {}
        for w, p in result:
            total = g.add(total, g.scale(g.mul(p,p), w))
        self.assertEqual(total, g.parse('(2*x-3*y)**2'))

    def test_indefinite_is_not_sos(self):
        self.assertIsNone(quadratic_sos(g.parse('x*y')))
        self.assertIsNone(quadratic_sos(g.parse('x**2-y**2')))

    def test_refutation_preserved(self):
        self.assertEqual(decide(['x*y=1'], 'x=y')['verdict'], 'DISPROVED')

    def test_randomized_positive_quadratics(self):
        rng = random.Random(20261019)
        for _ in range(250):
            matrix = [[rng.randint(-3,3) for _ in range(3)] for _ in range(rng.randint(1,5))]
            poly = {}
            for row in matrix:
                p = {((name, 1),): Fraction(v) for name, v in zip('xyz',row) if v}
                poly = g.add(poly, g.mul(p,p))
            components = quadratic_sos(poly)
            self.assertIsNotNone(components)
            reconstructed = {}
            for w, p in components:
                reconstructed = g.add(reconstructed, g.scale(g.mul(p,p), w))
            self.assertEqual(reconstructed, poly)


if __name__ == '__main__':
    unittest.main()
