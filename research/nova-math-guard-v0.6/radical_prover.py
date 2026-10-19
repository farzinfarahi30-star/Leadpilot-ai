#!/usr/bin/env python3
"""Find exact power-ideal certificates for polynomial consequences over fields.

A certificate is t**k = sum(Q_i*h_i) over Q[variables], with 2 <= k <= 4.
At a common zero of all h_i in any field containing Q, t**k=0 forces t=0.
This is a bounded sufficient search, NOT a complete implication algorithm.
"""
import argparse
import json
from pathlib import Path

import nova_math_guard as g
from conditional_prover import certify as certify_ideal, MAX_HYPOTHESES
from groebner_prover import ideal_membership, sum_lifts
from independent_verifier import (
    MAX_CERT_BYTES, RADICAL_SCHEMA, MAX_RADICAL_EXPONENT,
    verify_certificate,
)
from nova_certificates import normal_form


def certify(hypotheses, goal, *, max_power=MAX_RADICAL_EXPONENT):
    if type(max_power) is not int or not 2 <= max_power <= MAX_RADICAL_EXPONENT:
        raise g.Unsupported('maximum power must be an integer from 2 to 4')
    if not isinstance(hypotheses, list) or not 1 <= len(hypotheses) <= MAX_HYPOTHESES:
        raise g.Unsupported('provide 1 to 8 hypotheses')
    if not isinstance(goal, str) or len(goal) > 500:
        raise g.Unsupported('goal must be a polynomial equation <=500 characters')
    for hypothesis in hypotheses:
        if not isinstance(hypothesis, str) or len(hypothesis) > 500:
            raise g.Unsupported('hypothesis must be a polynomial equation <=500 characters')

    # Return the older, stronger ideal-membership witness if one exists.
    try:
        return certify_ideal(hypotheses, goal)
    except g.Unsupported as err:
        if not str(err).startswith('UNKNOWN:'):
            raise

    generators = []
    for hypothesis in hypotheses:
        left, right = g.equation(hypothesis)
        generators.append(g.add(left, right, -1))
    left, right = g.equation(goal)
    target = g.add(left, right, -1)

    for k in range(2, max_power + 1):
        try:
            powered = g.power(target, k)
            multipliers = ideal_membership(powered, generators)
        except g.Unsupported as err:
            if not str(err).startswith('UNKNOWN:'):
                raise
            continue
        if sum_lifts(multipliers, generators) != powered:
            raise AssertionError('internal reconstruction of radical witness failed')
        certificate = {
            'schema': RADICAL_SCHEMA, 'kind': 'radical',
            'hypotheses': hypotheses, 'goal': goal,
            'domain': 'Q-polynomial', 'verdict': 'PROVED',
            'evidence': {
                'power': k,
                'multipliers_normal_forms': [normal_form(q) for q in multipliers]
            }
        }
        if len(json.dumps(certificate, ensure_ascii=False).encode('utf-8')) > MAX_CERT_BYTES:
            raise g.Unsupported('UNKNOWN: certificate too large')
        # The generator cannot bless its own evidence: independent check first.
        verify_certificate(certificate)
        return certificate
    raise g.Unsupported(f'UNKNOWN: no bounded power-ideal certificate found (max power {max_power})')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--given', action='append', required=True)
    parser.add_argument('--goal', required=True)
    parser.add_argument('--max-power', type=int, default=MAX_RADICAL_EXPONENT)
    parser.add_argument('-o', '--output')
    args = parser.parse_args()
    try:
        certificate = certify(args.given, args.goal, max_power=args.max_power)
    except (g.Unsupported, OverflowError, RecursionError) as err:
        parser.error('UNKNOWN/UNSUPPORTED: ' + str(err))
    content = json.dumps(certificate, indent=2, sort_keys=True, ensure_ascii=False) + '\n'
    if len(content.encode('utf-8')) > MAX_CERT_BYTES:
        parser.error('UNKNOWN/UNSUPPORTED: formatted certificate too large')
    if args.output:
        Path(args.output).write_text(content, encoding='utf-8')
        print(f'CERTIFICATE CREATED: {args.output} ({certificate["kind"]} PROVED)')
    else:
        print(content, end='')


if __name__ == '__main__':
    main()
