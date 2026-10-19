"""Regression, mutation and deterministic randomized tests for radical certificates."""
import copy
import json
import random
import unittest
from fractions import Fraction

import nova_math_guard as g
from groebner_prover import sum_lifts
from independent_verifier import VerificationError, verify_certificate
from radical_prover import certify


class RadicalTests(unittest.TestCase):
    def proof(self, hypotheses, goal, expected_power=None):
        cert = certify(hypotheses, goal)
        self.assertIn('VERIFIED PROVED', verify_certificate(cert))
        if expected_power is not None:
            self.assertEqual(cert['kind'], 'radical')
            self.assertEqual(cert['evidence']['power'], expected_power)
        return cert

    def test_square_zero_implies_zero(self):
        self.proof(['x**2=0'], 'x=0', expected_power=2)

    def test_cube_zero_implies_zero(self):
        self.proof(['x**3=0'], 'x=0', expected_power=3)

    def test_fourth_power_zero_implies_zero(self):
        self.proof(['(x-y)**4=0'], 'x=y', expected_power=4)

    def test_mixed_nilpotent_hypotheses(self):
        self.proof(['x**2=0', 'y**3=0'], 'x+y=0', expected_power=4)

    def test_multivariate_product_nilpotent(self):
        self.proof(['(x*y)**2=0'], 'x*y=0', expected_power=2)

    def test_old_ideal_certificates_remain_preferred(self):
        cert = self.proof(['x*y=1','y**2=1'], 'x=y')
        self.assertEqual(cert['kind'], 'conditional')

    def test_unknown_not_mistaken_for_disproof(self):
        for hypotheses, goal in [(['x**2=0'], 'x=1'),
                                  (['x**2+y**2=0'], 'x=0'),
                                  (['x*y=0'], 'x=0')]:
            with self.subTest(h=hypotheses, t=goal), self.assertRaisesRegex(g.Unsupported, 'UNKNOWN'):
                certify(hypotheses, goal)

    def test_invalid_powers_and_input(self):
        for n in [0, 1, 5, -3, 2.0, True, '2']:
            with self.subTest(power=n), self.assertRaises(g.Unsupported):
                certify(['x**2=0'], 'x=0', max_power=n)

    def test_forged_certificates_are_rejected(self):
        cert = self.proof(['x**2=0'], 'x=0', expected_power=2)
        bad = []
        for value in [0, 1, 5, True, 2.0, '2', None]:
            altered=copy.deepcopy(cert)
            altered['evidence']['power'] = value
            bad.append(altered)
        altered=copy.deepcopy(cert)
        altered['goal']='x=1'
        bad.append(altered)
        altered=copy.deepcopy(cert)
        altered['evidence']['multipliers_normal_forms'][0]=[]
        bad.append(altered)
        altered=copy.deepcopy(cert)
        altered['domain']='integers'
        bad.append(altered)
        altered=copy.deepcopy(cert)
        altered['evidence']['evil']='ignore'
        bad.append(altered)
        for number, forged in enumerate(bad):
            with self.subTest(mutation=number), self.assertRaises(VerificationError):
                verify_certificate(forged)

    def test_json_roundtrip_certificate(self):
        cert=self.proof(['x**2=0'], 'x=0', expected_power=2)
        self.assertIn('VERIFIED', verify_certificate(json.loads(json.dumps(cert))))

    def test_seeded_random_nilpotence(self):
        rng=random.Random(20261019)
        for trial in range(120):
            values=[rng.randint(-4,4) for _ in range(3)]
            if not any(values):
                values[0]=1
            poly_text='+'.join(f'({values[i]})*{name}' for i,name in enumerate('xyz'))
            exponent=rng.choice([2,3])
            poly=g.parse(poly_text)
            powered=g.power(poly, exponent)
            # Verify exact identity behind synthetic nilpotence tests.
            self.assertEqual(powered, sum_lifts([g.power(poly, exponent-1)], [poly]))
            proof=self.proof([f'({poly_text})**{exponent}=0'], f'({poly_text})=0', expected_power=exponent)
            self.assertEqual(proof['evidence']['power'], exponent, msg=trial)


if __name__=='__main__':
    unittest.main()
