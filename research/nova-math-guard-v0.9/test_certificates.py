"""Independent certificate check, adversarial mutation, and randomized regression."""
import copy
import json
import random
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

from nova_certificates import certify
from independent_verifier import verify_certificate, VerificationError
import nova_math_guard as guard


class CertificateTests(unittest.TestCase):
    def assert_verified(self, kind, equation, expected):
        cert = certify(kind, equation)
        self.assertEqual(cert['verdict'], expected)
        self.assertIn('VERIFIED', verify_certificate(cert))
        return cert

    def test_example_certificates(self):
        cases = [
            ('identity', '(x+y)**2=x*x+2*x*y+y*y', 'PROVED'),
            ('identity', 'x**2=x', 'DISPROVED'),
            ('identity', '1/3+1/6=1/2', 'PROVED'),
            ('identity', '2=3', 'DISPROVED'),
            ('identity', 'x-x=1', 'DISPROVED'),
            ('identity', 'x-x=0', 'PROVED'),
            ('identity', 'x+z-x=z+1', 'DISPROVED'),
            ('linear', '3*x+7=22', 'UNIQUE'),
            ('linear', 'x/3+2=1/2', 'UNIQUE'),
            ('linear', '2*x+1=2*x+2', 'NONE'),
            ('linear', '2*x+1=2*x+1', 'ALL'),
            ('linear', '1=2', 'NONE'),
            ('linear', '0=0', 'ALL'),
            ('linear', 'x**2 + 2*x=x**2+4', 'UNIQUE'),
        ]
        for kind, equation, verdict in cases:
            with self.subTest(equation=equation):
                self.assert_verified(kind, equation, verdict)

    def test_mutation_rejected(self):
        original = self.assert_verified('identity', 'x**2=x', 'DISPROVED')
        mutations = [
            lambda d: d.update(verdict='PROVED'),
            lambda d: d.update(domain='R-polynomial'),
            lambda d: d.update(schema='bogus'),
            lambda d: d.update(statement='x**2=x**2'),
            lambda d: d['evidence'].update(lhs_value='0'),
            lambda d: d['evidence'].update(rhs_value='0'),
            lambda d: d['evidence']['assignment'].update(x='1'),
            lambda d: d['evidence'].update(lhs_normal_form=[]),
            lambda d: d['evidence'].update(rhs_normal_form=[]),
            lambda d: d['evidence']['assignment'].update(x='1/0'),
            lambda d: d['evidence']['assignment'].update(what='3'),
        ]
        for i, mutation in enumerate(mutations):
            with self.subTest(mutation=i):
                corrupted = copy.deepcopy(original)
                mutation(corrupted)
                with self.assertRaises(VerificationError):
                    verify_certificate(corrupted)

    def test_linear_tamper_rejected(self):
        good = self.assert_verified('linear', '3*x+7=22', 'UNIQUE')
        for edit in [lambda c: c['evidence'].update(solution='1'),
                     lambda c: c.update(verdict='NONE'),
                     lambda c: c['evidence'].update(difference_normal_form=[])]:
            copy_cert = copy.deepcopy(good)
            edit(copy_cert)
            with self.assertRaises(VerificationError):
                verify_certificate(copy_cert)

    def test_unsupported_is_not_certified(self):
        for kind, statement in [('linear', 'x**2=9'), ('linear', 'x+y=0'),
                                ('identity', 'x/y=2'), ('identity', '0**0=1')]:
            with self.subTest(statement=statement), self.assertRaises(guard.Unsupported):
                certify(kind, statement)

    def test_randomized_certificate_consistency(self):
        rng = random.Random(20261019)
        variables = ['x', 'y', 'z']
        for _ in range(1200):
            terms = []
            for __ in range(rng.randint(1, 6)):
                coefficient = rng.randint(-6, 6)
                powers = [rng.randint(0, 3) for _ in variables]
                factors = [str(coefficient)]
                factors.extend(f'{name}**{degree}' for name, degree in zip(variables, powers) if degree)
                terms.append('(' + '*'.join(factors) + ')')
            poly = '+'.join(terms)
            equation = f'{poly}={poly}' if rng.randrange(2) == 0 else f'{poly}=0'
            cert = certify('identity', equation)
            verdict = cert['verdict']
            self.assertIn(verdict, ('PROVED', 'DISPROVED'))
            self.assertTrue(verify_certificate(cert).startswith('VERIFIED'))

    def test_random_linear_solution(self):
        rng = random.Random(639271)
        for _ in range(500):
            a, b, c, d = [rng.randint(-20, 20) for __ in range(4)]
            text = f'({a})*x+({b})=({c})*x+({d})'
            want = 'UNIQUE' if a != c else ('ALL' if b == d else 'NONE')
            self.assert_verified('linear', text, want)

    def test_standalone_verifier_process(self):
        cert = self.assert_verified('identity', '(x+y)**3=x**3+3*x*x*y+3*x*y*y+y**3', 'PROVED')
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'certificate.json'
            path.write_text(json.dumps(cert), encoding='utf-8')
            proc = subprocess.run([sys.executable, 'independent_verifier.py', str(path)],
                                  capture_output=True, text=True, timeout=10)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            cert['verdict'] = 'DISPROVED'
            path.write_text(json.dumps(cert), encoding='utf-8')
            proc = subprocess.run([sys.executable, 'independent_verifier.py', str(path)],
                                  capture_output=True, text=True, timeout=10)
            self.assertEqual(proc.returncode, 1)
            self.assertIn('REJECTED', proc.stderr)


if __name__ == '__main__':
    unittest.main()
