#!/usr/bin/env python3
"""Small, reproducible backward-chain benchmark of known real-algebra cases.

No novelty is claimed. Any PROVED/DISPROVED verdict must have an independently
verified certificate; UNKNOWN is retained as such.
"""
import json
from pathlib import Path
import nova_math_guard as g
from real_sos_prover import decide
from independent_verifier import verify_certificate

CASES = [
    ('real_only_base', ['x**2+y**2=0'], 'x=0'),
    ('scaled_real_only', ['4*x**2+9*y**2=0'], 'y=0'),
    ('affine_square', ['(x+y)**2+z**2=0'], 'x+y=0'),
    ('combined_constraints', ['x**2+y**2=0', 'z**2+w**2=0'], 'x+z=0'),
    ('field_radical', ['x**2=0'], 'x=0'),
    ('negative_rational', ['x*y=1'], 'x=y'),
    ('real_quartic_now_proved', ['x**4+y**4=0'], 'x=0'),
    ('real_sextic_now_proved', ['x**6+y**6=0'], 'x=0'),
    ('real_octic_now_proved', ['x**8+y**8=0'], 'x=0'),
    ('real_positive_cross_terms', ['x**4+2*x**2*y**2+y**4=0'], 'x=0'),
    ('real_decic_still_unknown', ['x**10+y**10=0'], 'x=0'),
    ('invalid_signed_quartic', ['x**4-y**4=0'], 'x=0'),
]


def run():
    records = []
    for name, hypotheses, goal in CASES:
        try:
            cert = decide(hypotheses, goal)
            verification = verify_certificate(cert)
            record = {'case': name, 'hypotheses': hypotheses, 'goal': goal,
                      'verdict': cert['verdict'], 'kind': cert['kind'],
                      'independently_verified': True, 'verification': verification}
        except g.Unsupported as ex:
            record = {'case': name, 'hypotheses': hypotheses, 'goal': goal,
                      'verdict': 'UNKNOWN', 'kind': None,
                      'independently_verified': False, 'reason': str(ex)}
        records.append(record)
        print(f'{name}: {record["verdict"]} ({record["kind"] or "no certificate"})')
    result = {'project': 'NOVA Math Guard', 'version': '0.9',
              'novelty_claimed': False, 'benchmark': 'selected established examples',
              'cases': records}
    return result


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
