#!/usr/bin/env python3
"""Reproducible small research exercise: exact binomial identities vs perturbations.

These are classical identities, NOT novel mathematics or an open-problem solution.
"""
import json
from math import comb
from pathlib import Path

from nova_certificates import certify
from independent_verifier import verify_certificate


def binomial_rhs(n, mutate=False):
    terms = []
    for k in range(n + 1):
        coefficient = comb(n, k) + (1 if mutate and k == n // 2 else 0)
        factors = [str(coefficient)]
        if n-k:
            factors.append('x' + (f'**{n-k}' if n-k != 1 else ''))
        if k:
            factors.append('y' + (f'**{k}' if k != 1 else ''))
        terms.append('*'.join(factors))
    return '+'.join(terms)


def run():
    result = {'project': 'NOVA Math Guard', 'version': '0.3',
              'objective': 'classical binomial identities and altered near-misses',
              'novelty_claimed': False, 'tested_degrees': [], 'certificates_verified': 0,
              'valid_identities': 0, 'refuted_near_misses': 0, 'examples': []}
    for n in range(1, 13):
        for mutated in [False, True]:
            statement = f'(x+y)**{n}={binomial_rhs(n, mutated)}'
            certificate = certify('identity', statement)
            expected = 'DISPROVED' if mutated else 'PROVED'
            assert certificate['verdict'] == expected
            assert verify_certificate(certificate).startswith('VERIFIED')
            result['certificates_verified'] += 1
            result['refuted_near_misses' if mutated else 'valid_identities'] += 1
            if n in (2, 8, 12):
                result['examples'].append({'degree': n, 'mutated': mutated,
                                            'verdict': certificate['verdict'],
                                            'counterexample': certificate['evidence'].get('assignment')})
        result['tested_degrees'].append(n)
    return result


if __name__ == '__main__':
    report = run()
    path = Path(__file__).parent / 'RESEARCH_RESULTS.json'
    path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f'PASS: {report["certificates_verified"]} independently verified certificates '
          f'({report["valid_identities"]} classical truths, '
          f'{report["refuted_near_misses"]} counterexamples).')
    print(f'Report: {path}')
