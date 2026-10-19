"""Independent replay, adversarial mutations, and generated consequences."""
import copy
import json
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import nova_math_guard as g
from conditional_prover import certify
from independent_verifier import verify_certificate, VerificationError


class ConditionalTests(unittest.TestCase):
    def verified(self, assumptions, goal):
        certificate = certify(assumptions, goal)
        self.assertEqual(certificate['verdict'], 'PROVED')
        self.assertTrue(verify_certificate(certificate).startswith('VERIFIED PROVED'))
        return certificate

    def test_nontrivial_polynomial_implication(self):
        certificate = self.verified(['x=y'], 'x**2=y**2')
        terms = certificate['evidence']['multipliers_normal_forms'][0]
        self.assertEqual(len(terms), 2)  # exact x+y factor

    def test_quadratic_consequence(self):
        self.verified(['x**2+y**2=z**2'], 'z**2-x**2=y**2')

    def test_powers_from_equality(self):
        for n in range(1, 11):
            with self.subTest(n=n):
                self.verified(['x=y'], f'x**{n}=y**{n}')

    def test_two_hypothesis_linear_combination(self):
        certificate = self.verified(['x+y=3', 'x-y=1'], 'x=2')
        multipliers = certificate['evidence']['multipliers_normal_forms']
        self.assertEqual(multipliers[0][0]['coefficient'], '1/2')
        self.assertEqual(multipliers[1][0]['coefficient'], '1/2')

    def test_transitive_relation(self):
        self.verified(['x=y', 'y=z'], 'x=z')

    def test_trivial_goal_and_zero_hypothesis(self):
        self.verified(['x=x'], 'z=z')

    def test_assumption_contradiction_logic(self):
        # Over Q, 1=0 has no satisfying assignments, so it implies any equation.
        self.verified(['1=0'], 'x=11')

    def test_no_false_unprovability(self):
        with self.assertRaisesRegex(g.Unsupported, 'UNKNOWN'):
            certify(['x=y'], 'x+1=y')
        with self.assertRaisesRegex(g.Unsupported, 'UNKNOWN'):
            certify(['x**2=y**2'], 'x=y')  # not even logically implied
        # A valid consequence can remain UNKNOWN: no Groebner basis computation.
        with self.assertRaisesRegex(g.Unsupported, 'UNKNOWN'):
            certify(['x*y=1', 'y**2=1'], 'x=y')

    def test_nontrivial_elimination(self):
        self.verified(['x*y=0', 'x*(y-1)=0'], 'x=0')

    def test_malformed_and_tampered_certificates_rejected(self):
        cert = self.verified(['x=y'], 'x**2=y**2')
        mutations = [
            lambda a: a.update(goal='x**2=y**3'),
            lambda a: a.update(hypotheses=['x=0']),
            lambda a: a.update(verdict='DISPROVED'),
            lambda a: a.update(schema='NOVA-MATH-GUARD-CERT-1'),
            lambda a: a.update(hypotheses=[]),
            lambda a: a.update(hypotheses=['x=y', 'z=1']),
            lambda a: a['evidence'].update(multipliers_normal_forms=[[]]),
            lambda a: a['evidence']['multipliers_normal_forms'][0][0].update(coefficient='3'),
            lambda a: a['evidence']['multipliers_normal_forms'][0][0].update(coefficient='1/0'),
            lambda a: a['evidence']['multipliers_normal_forms'][0][0].update(coefficient='0'),
            lambda a: a['evidence']['multipliers_normal_forms'][0][0]['monomial'][0].__setitem__(1, -1),
            lambda a: a['evidence']['multipliers_normal_forms'][0][0]['monomial'][0].__setitem__(1, True),
            lambda a: a['evidence']['multipliers_normal_forms'][0].reverse(),
            lambda a: a['evidence']['multipliers_normal_forms'][0].append(copy.deepcopy(a['evidence']['multipliers_normal_forms'][0][0])),
        ]
        for i, mutation in enumerate(mutations):
            changed = copy.deepcopy(cert)
            mutation(changed)
            with self.subTest(mutation=i), self.assertRaises(VerificationError):
                verify_certificate(changed)

    def test_older_certificates_still_verify(self):
        folder = Path(__file__).parent / 'certificates'
        for path in folder.glob('*.json'):
            if path.name.startswith('conditional_'):
                continue
            with self.subTest(path=path.name):
                self.assertIn('VERIFIED', verify_certificate(json.loads(path.read_text())))

    def test_seeded_randomized_generated_consequences(self):
        rng = random.Random(20261019)
        for _ in range(300):
            a = rng.randint(-5, 5)
            b = rng.randint(-5, 5)
            c = rng.randint(-5, 5)
            d = rng.randint(-5, 5)
            # Every goal is (x-y)*(A*x+B*y+C*z+D)=0 under x=y.
            q = f'({a})*x+({b})*y+({c})*z+({d})'
            goal = f'(x-y)*({q})=0'
            cert = certify(['x=y'], goal)
            self.assertEqual(cert['verdict'], 'PROVED')
            self.assertIn('VERIFIED', verify_certificate(cert))

    def test_separate_verifier_process_rejects_tampering(self):
        certificate = self.verified(['x=y'], 'x**2=y**2')
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'cert.json'
            path.write_text(json.dumps(certificate))
            verifier_path = Path(__file__).parent / 'independent_verifier.py'
            result = subprocess.run([sys.executable, verifier_path, path], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            certificate['goal'] = 'x**2=y**2+1'
            path.write_text(json.dumps(certificate))
            rejected = subprocess.run([sys.executable, verifier_path, path], capture_output=True, text=True, timeout=10)
            self.assertEqual(rejected.returncode, 1)
            self.assertIn('REJECTED', rejected.stderr)


if __name__ == '__main__':
    unittest.main()
