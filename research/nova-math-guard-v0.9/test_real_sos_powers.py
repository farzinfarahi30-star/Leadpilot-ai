"""Adversarial and property tests for exact even-power SOS proof certificates.

These are soundness/regression tests for the supported fragment, not proofs that
all generated certificates are free from implementation bugs.
"""
import copy
import random
import unittest
from fractions import Fraction

import nova_math_guard as g
from independent_verifier import VerificationError, verify_certificate, REAL_SOS_POWER_SCHEMA
from real_sos_prover import certify, decide, monomial_sos


class RealPowerCertificateTests(unittest.TestCase):
    def checked(self, hypotheses, goal, expected_power=None):
        certificate = certify(hypotheses, goal)
        self.assertEqual(certificate['schema'], REAL_SOS_POWER_SCHEMA)
        self.assertEqual(certificate['kind'], 'real-sos')
        self.assertEqual(certificate['verdict'], 'PROVED')
        if expected_power:
            self.assertEqual(certificate['evidence']['goal_even_power'], expected_power)
        self.assertIn('VERIFIED PROVED:', verify_certificate(certificate))
        return certificate

    def test_quartic_real_implication(self):
        self.checked(['x**4+y**4=0'], 'x=0', 4)

    def test_octic_real_implication(self):
        self.checked(['x**8+y**8=0'], 'y=0', 8)

    def test_sextic_real_implication(self):
        self.checked(['x**6+2*y**6=0'], 'x=0', 6)

    def test_positive_cross_monomials(self):
        self.checked(['x**4+2*x**2*y**2+y**4=0'], 'x=0', 4)

    def test_legacy_quadratic_case_still_works(self):
        self.checked(['x**2+y**2=0'], 'x=0', 2)

    def test_legacy_format_remains_accepted(self):
        import json
        from pathlib import Path
        old = json.loads((Path(__file__).parent / 'certificates' / 'real_sum_two_squares.json').read_text())
        self.assertIn('VERIFIED PROVED:', verify_certificate(old))

    def test_tampered_target_power_rejected(self):
        cert = self.checked(['x**4+y**4=0'], 'x=0', 4)
        for incorrect in (0, 1, 3, -4, 10, True, 2.0):
            with self.subTest(incorrect=incorrect):
                altered = copy.deepcopy(cert)
                altered['evidence']['goal_even_power'] = incorrect
                with self.assertRaises(VerificationError):
                    verify_certificate(altered)
        altered = copy.deepcopy(cert)
        altered['evidence']['goal_even_power'] = 2
        with self.assertRaises(VerificationError):
            verify_certificate(altered)

    def test_corrupt_weight_and_square_rejected(self):
        cert = self.checked(['x**4+y**4=0'], 'x=0', 4)
        for value in ('-1', '0', '1/0', '1.0'):
            with self.subTest(value=value):
                altered = copy.deepcopy(cert)
                altered['evidence']['weighted_squares'][0]['weight'] = value
                with self.assertRaises(VerificationError):
                    verify_certificate(altered)
        altered = copy.deepcopy(cert)
        altered['evidence']['weighted_squares'][0]['polynomial_normal_form'][0]['coefficient'] = '2'
        with self.assertRaises(VerificationError):
            verify_certificate(altered)

    def test_fake_domain_rejected(self):
        cert = self.checked(['x**4+y**4=0'], 'x=0', 4)
        cert['domain'] = 'complex-fields-over-Q'
        with self.assertRaises(VerificationError):
            verify_certificate(cert)

    def test_no_false_proof_for_signed_quartic(self):
        cert = decide(['x**4-y**4=0'], 'x=0')
        self.assertEqual(cert['verdict'], 'DISPROVED')
        self.assertIn('VERIFIED DISPROVED:', verify_certificate(cert))

    def test_higher_power_returns_unknown(self):
        with self.assertRaisesRegex(g.Unsupported, '^UNKNOWN:'):
            decide(['x**10+y**10=0'], 'x=0')

    def test_reconstruct_randomized_diagonal_monomial_sos(self):
        rng = random.Random(20261019)
        for i in range(400):
            polynomial = {}
            for _ in range(rng.randrange(1, 7)):
                c = Fraction(rng.randrange(1, 8), rng.randrange(1, 8))
                monomial = tuple((name, 2 * rng.randrange(1, 5))
                                 for name in 'xyz' if rng.randrange(3) == 0)
                polynomial = g.add(polynomial, {monomial: c})
            components = monomial_sos(polynomial)
            self.assertIsNotNone(components, msg=f'case {i}')
            reconstruction = {}
            for weight, square in components:
                self.assertGreater(weight, 0)
                reconstruction = g.add(reconstruction, g.scale(g.mul(square, square), weight))
            self.assertEqual(reconstruction, polynomial)

    def test_invalid_monomial_sos_rejected(self):
        self.assertIsNone(monomial_sos(g.parse('x**3 + y**4')))
        self.assertIsNone(monomial_sos(g.parse('x**4 - y**4')))
        self.assertIsNone(monomial_sos({}))

    def test_property_generated_proof_certificates(self):
        rng = random.Random(9619)
        for i in range(240):
            degree = rng.choice((2, 4, 6, 8))
            a, b = rng.randint(1, 4), rng.randint(1, 4)
            hypothesis = f'{a}*x**{degree}+{b}*y**{degree}=0'
            result = self.checked([hypothesis], 'x=0', degree)
            self.assertEqual(result['verdict'], 'PROVED', msg=f'case {i}')


if __name__ == '__main__':
    unittest.main()
