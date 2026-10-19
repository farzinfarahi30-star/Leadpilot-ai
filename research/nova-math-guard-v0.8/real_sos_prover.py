#!/usr/bin/env python3
"""Deterministic, bounded REAL sum-of-squares certificate search.

Completeness is NOT claimed. A positive result is checked by an independent
certificate verifier and is true over ordered fields, not over C.
"""
import argparse
import itertools
import json
from fractions import Fraction
from pathlib import Path

import nova_math_guard as g
from independent_verifier import MAX_CERT_BYTES, REAL_SOS_SCHEMA, verify_certificate
from nova_certificates import normal_form

COEFFICIENTS = tuple(map(Fraction, ['-4', '-3', '-2', '-1', '-1/2', '-1/3',
                                    '1/3', '1/2', '1', '2', '3', '4']))
MAX_CANDIDATES = 4000
MAX_VARIABLES = 6


def quadratic_sos(polynomial):
    """Express degree <=2 positive-semidefinite quadratic polynomial as
    positive rational weights times squares of rational affine polynomials.

    Uses exact rational pivoted LDL decomposition of its *fixed* Gram matrix
    in basis (1,x,y,...). This fixed Gram choice is intentionally incomplete.
    """
    names = sorted(g.variable_names(polynomial))
    if len(names) > MAX_VARIABLES:
        return None
    size = len(names) + 1
    gram = [[Fraction(0) for _ in range(size)] for _ in range(size)]
    for monomial, coefficient in polynomial.items():
        powers = dict(monomial)
        degree = sum(powers.values())
        if degree > 2:
            return None
        if not degree:
            gram[0][0] += coefficient
        elif degree == 1:
            if len(powers) != 1:
                return None
            i = names.index(next(iter(powers))) + 1
            gram[0][i] += coefficient / 2
            gram[i][0] += coefficient / 2
        elif len(powers) == 1:
            i = names.index(next(iter(powers))) + 1
            gram[i][i] += coefficient
        elif len(powers) == 2 and all(v == 1 for v in powers.values()):
            a, b = sorted(powers)
            i, j = names.index(a) + 1, names.index(b) + 1
            gram[i][j] += coefficient / 2
            gram[j][i] += coefficient / 2
        else:
            return None
    # Symmetric exact LDL with semidefinite zero pivots accepted only when
    # the corresponding row vanishes. Positive pivots give weighted squares.
    components = []
    for i in range(size):
        d = gram[i][i]
        if d < 0:
            return None
        if not d:
            if any(gram[i][j] for j in range(i + 1, size)):
                return None
            continue
        coeffs = [Fraction(0)] * size
        coeffs[i] = 1
        for j in range(i + 1, size):
            coeffs[j] = gram[i][j] / d
        p = {}
        for j, coefficient in enumerate(coeffs):
            if coefficient:
                mono = () if j == 0 else ((names[j - 1], 1),)
                p[mono] = coefficient
        components.append((d, p))
        for j in range(i + 1, size):
            for k in range(i + 1, size):
                gram[j][k] -= d * coeffs[j] * coeffs[k]
    reconstructed = {}
    for weight, p in components:
        reconstructed = g.add(reconstructed, g.scale(g.mul(p, p), weight))
    if reconstructed != polynomial:
        raise AssertionError('SOS decomposition reconstruction mismatch')
    return components


def multiplier_candidates(equations):
    # Zero or up to two constant multipliers, no unbounded nonlinear search.
    # Only a finite candidate list is visited, deterministically.
    n = len(equations)
    for i in range(n):
        for coefficient in COEFFICIENTS:
            values = [Fraction(0)] * n
            values[i] = coefficient
            yield values
    for i, j in itertools.combinations(range(n), 2):
        for ci, cj in itertools.product(COEFFICIENTS, repeat=2):
            values = [Fraction(0)] * n
            values[i], values[j] = ci, cj
            yield values


def certify(hypotheses, goal):
    if (not isinstance(hypotheses, list) or not 1 <= len(hypotheses) <= 8 or
            not all(isinstance(h, str) and len(h) <= 500 for h in hypotheses) or
            not isinstance(goal, str) or len(goal) > 500):
        raise g.Unsupported('provide 1-8 equalities and a goal equation <=500 characters')
    hpolys = []
    for h in hypotheses:
        a, b = g.equation(h)
        hpolys.append(g.add(a, b, -1))
    a, b = g.equation(goal)
    target = g.add(a, b, -1)
    if len(set().union(g.variable_names(target), *(g.variable_names(h) for h in hpolys))) > MAX_VARIABLES:
        raise g.Unsupported('UNKNOWN: more than six variables')
    target_square = g.mul(target, target)
    tested = 0
    for weights in multiplier_candidates(hpolys):
        tested += 1
        if tested > MAX_CANDIDATES:
            break
        rhs = {}
        for c, h in zip(weights, hpolys):
            if c:
                rhs = g.add(rhs, g.scale(h, c))
        residual = g.add(rhs, target_square, -1)
        sos = quadratic_sos(residual)
        if not sos:
            continue
        certificate = {
            'schema': REAL_SOS_SCHEMA,
            'kind': 'real-sos',
            'hypotheses': hypotheses,
            'goal': goal,
            'domain': 'ordered-fields-over-Q',
            'verdict': 'PROVED',
            'evidence': {
                'multipliers_normal_forms': [normal_form({(): q} if q else {}) for q in weights],
                'weighted_squares': [
                    {'weight': str(weight), 'polynomial_normal_form': normal_form(p)}
                    for weight, p in sos
                ],
            },
        }
        if len(json.dumps(certificate, ensure_ascii=False).encode('utf-8')) > MAX_CERT_BYTES:
            raise g.Unsupported('UNKNOWN: SOS certificate exceeds verifier limit')
        verify_certificate(certificate)
        return certificate
    raise g.Unsupported(f'UNKNOWN: no SOS certificate in {min(tested, MAX_CANDIDATES)} bounded candidates')


def decide(hypotheses, goal):
    """Proofs under ordered-field semantics; rational countermodels refute."""
    from radical_prover import certify as radical_certify
    from conditional_counterexample import counterexample
    try:
        result = radical_certify(hypotheses, goal)
    except g.Unsupported as e:
        if not str(e).startswith('UNKNOWN:'):
            raise
    else:
        verify_certificate(result)
        return result
    try:
        return certify(hypotheses, goal)
    except g.Unsupported as e:
        if not str(e).startswith('UNKNOWN:'):
            raise
    return counterexample(hypotheses, goal)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--given', action='append', required=True)
    parser.add_argument('--goal', required=True)
    parser.add_argument('--sos-only', action='store_true')
    parser.add_argument('-o', '--output')
    args = parser.parse_args()
    try:
        result = certify(args.given, args.goal) if args.sos_only else decide(args.given, args.goal)
    except g.Unsupported as e:
        parser.error('UNKNOWN/UNSUPPORTED: ' + str(e))
    text = json.dumps(result, indent=2, sort_keys=True) + '\n'
    if args.output:
        Path(args.output).write_text(text, encoding='utf-8')
        print(f'CERTIFICATE CREATED: {args.output} ({result["verdict"]})')
    else:
        print(text, end='')


if __name__ == '__main__':
    main()
