#!/usr/bin/env python3
"""NOVA Math Guard v0.7: bounded rational countermodel search.

Given rational-coefficient polynomial equations h_i=0 and proposed conclusion
 t=0, find an exact rational tuple satisfying all h_i but not t.

An exhibited witness logically DISPROVES universal implication over Q and any
field containing Q. Exhaustion of the finite search grid is NEVER a proof.
"""
import argparse
from fractions import Fraction
import itertools
import json
from pathlib import Path

import nova_math_guard as g
from conditional_prover import MAX_HYPOTHESES
from independent_verifier import (
    CONDITIONAL_COUNTEREXAMPLE_SCHEMA, MAX_CERT_BYTES, verify_certificate,
)

DEFAULT_VALUES = (Fraction(0), Fraction(1), Fraction(-1),
                  Fraction(2), Fraction(-2), Fraction(1, 2),
                  Fraction(-1, 2), Fraction(3), Fraction(-3),
                  Fraction(1, 3), Fraction(-1, 3))
MAX_GRID_POINTS = 100000
MAX_VARIABLES = 6


def counterexample(hypotheses, goal, *, grid_values=DEFAULT_VALUES,
                   max_points=20000):
    """Return verified negative certificate, or raise Unsupported(UNKNOWN).

    `max_points` counts inspected assignments, not potential search-space size.
    This is a complete search ONLY within the visited grid points.
    """
    if not isinstance(hypotheses, list) or not 1 <= len(hypotheses) <= MAX_HYPOTHESES:
        raise g.Unsupported('1 to 8 equality hypotheses required')
    if not isinstance(goal, str) or len(goal) > 500:
        raise g.Unsupported('goal must be a short equality')
    if type(max_points) is not int or not 1 <= max_points <= MAX_GRID_POINTS:
        raise g.Unsupported('max_points must be an integer between 1 and 100000')
    if not isinstance(grid_values, (tuple, list)) or not grid_values or len(grid_values) > 32:
        raise g.Unsupported('expected 1 to 32 rational grid values')
    values = []
    for item in grid_values:
        if isinstance(item, (float, complex, bool)):
            raise g.Unsupported('grid values must be exact rationals, not floats')
        try:
            q = Fraction(item)
        except (ValueError, ZeroDivisionError, TypeError):
            raise g.Unsupported('invalid rational grid value') from None
        if max(len(str(q.numerator)), len(str(q.denominator))) > 80:
            raise g.Unsupported('rational grid value too large')
        if q not in values:
            values.append(q)

    for equation in [*hypotheses, goal]:
        if not isinstance(equation, str) or len(equation) > 500:
            raise g.Unsupported('all equations must be strings <=500 characters')
    parsed = [g.equation(statement) for statement in [*hypotheses, goal]]
    names = sorted(set().union(*(g.variable_names(p) for lr in parsed for p in lr)))
    if len(names) > MAX_VARIABLES:
        raise g.Unsupported('UNKNOWN: too many variables for bounded grid search')

    inspected = 0
    for candidate in itertools.product(values, repeat=len(names)):
        if inspected >= max_points:
            break
        inspected += 1
        assignment = dict(zip(names, candidate))
        hypotheses_values = [
            (g.evaluate(lhs, assignment), g.evaluate(rhs, assignment))
            for lhs, rhs in parsed[:-1]
        ]
        if any(left != right for left, right in hypotheses_values):
            continue
        goal_left, goal_right = (
            g.evaluate(parsed[-1][0], assignment),
            g.evaluate(parsed[-1][1], assignment),
        )
        if goal_left == goal_right:
            continue
        certificate = {
            'schema': CONDITIONAL_COUNTEREXAMPLE_SCHEMA,
            'kind': 'conditional-counterexample',
            'hypotheses': hypotheses,
            'goal': goal,
            'domain': 'Q-polynomial',
            'verdict': 'DISPROVED',
            'evidence': {
                'assignment': {key: str(assignment[key]) for key in names},
                'hypotheses_values': [
                    {'lhs': str(lhs), 'rhs': str(rhs)} for lhs, rhs in hypotheses_values
                ],
                'goal_values': {'lhs': str(goal_left), 'rhs': str(goal_right)},
            },
        }
        if len(json.dumps(certificate, ensure_ascii=False).encode('utf-8')) > MAX_CERT_BYTES:
            raise g.Unsupported('UNKNOWN: certificate too large')
        # Independently parse, evaluate, and check every equation before release.
        verify_certificate(certificate)
        return certificate
    raise g.Unsupported(f'UNKNOWN: no rational counterexample among {inspected} tested grid assignments')


def decide(hypotheses, goal, *, max_points=20000):
    """Three-valued result: proved, disproved, or UNKNOWN.

    Use the existing proof-producing algebra engine first; a countermodel is
    attempted only when no bounded positive certificate is found.
    """
    from radical_prover import certify
    try:
        result = certify(hypotheses, goal)
    except g.Unsupported as ex:
        if not str(ex).startswith('UNKNOWN:'):
            raise
    else:
        verify_certificate(result)
        return result
    return counterexample(hypotheses, goal, max_points=max_points)


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--given', required=True, action='append')
    cli.add_argument('--goal', required=True)
    cli.add_argument('--max-points', type=int, default=20000)
    cli.add_argument('--refute-only', action='store_true',
                     help='skip positive proof search')
    cli.add_argument('-o', '--output')
    args = cli.parse_args()
    try:
        document = (counterexample(args.given, args.goal, max_points=args.max_points)
                    if args.refute_only else decide(args.given, args.goal,
                                                    max_points=args.max_points))
    except (g.Unsupported, RecursionError, OverflowError) as error:
        cli.error('UNKNOWN/UNSUPPORTED: ' + str(error))
    text = json.dumps(document, indent=2, sort_keys=True) + '\n'
    if len(text.encode('utf-8')) > MAX_CERT_BYTES:
        cli.error('UNKNOWN: formatted certificate exceeds limit')
    if args.output:
        Path(args.output).write_text(text, encoding='utf-8')
        print(f'CERTIFICATE CREATED: {args.output} ({document["verdict"]})')
    else:
        print(text, end='')


if __name__ == '__main__':
    main()
