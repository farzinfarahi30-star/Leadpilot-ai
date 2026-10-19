#!/usr/bin/env python3
"""Certify a restricted class of polynomial consequences of equalities.

A certificate establishes goal_L-goal_R = sum_i Q_i*(hyp_iL-hyp_iR) in Q[x].
If polynomial division cannot find a witness it reports UNKNOWN, never FALSE.
"""
import argparse
import json
from fractions import Fraction
from pathlib import Path

import nova_math_guard as g
from nova_certificates import normal_form
from independent_verifier import MAX_CERT_BYTES, CONDITIONAL_SCHEMA

MAX_HYPOTHESES = 8
MAX_STEPS = 20000


def leading(poly, names):
    """Highest monomial under graded lex order (global sorted variable names)."""
    return max(poly, key=lambda mono: (sum(power for _, power in mono),
                                       tuple(dict(mono).get(name, 0) for name in names)))


def quotient_monomial(dividend, divisor):
    a, b = dict(dividend), dict(divisor)
    if any(a.get(name, 0) < degree for name, degree in b.items()):
        return None
    return tuple((name, a.get(name, 0) - b.get(name, 0)) for name in sorted(a)
                 if a.get(name, 0) - b.get(name, 0))



def constant_combination(goal, divisors):
    """Solve A*q=b over Q: each hypothesis has a constant scalar multiplier.

    This detects consequences that simple ordered polynomial division misses,
    such as (x+y=3 AND x-y=1) => x=2.
    """
    monomials = sorted(set(goal).union(*(set(p) for p in divisors)))
    n = len(divisors)
    if len(monomials) > g.MAX_TERMS:
        raise g.Unsupported('UNKNOWN: linear-combination system too large')
    matrix = [[p.get(m, Fraction(0)) for p in divisors] +
              [goal.get(m, Fraction(0))] for m in monomials]
    pivots = []
    row = 0
    for col in range(n):
        pivot = next((i for i in range(row, len(matrix)) if matrix[i][col]), None)
        if pivot is None:
            continue
        matrix[row], matrix[pivot] = matrix[pivot], matrix[row]
        denominator = matrix[row][col]
        matrix[row] = [v / denominator for v in matrix[row]]
        for i in range(len(matrix)):
            if i != row and matrix[i][col]:
                scale = matrix[i][col]
                matrix[i] = [v - scale * u for v, u in zip(matrix[i], matrix[row])]
        pivots.append((col, row))
        row += 1
    if any(all(v == 0 for v in values[:-1]) and values[-1] != 0
           for values in matrix):
        return None
    q = [Fraction(0)] * n
    for col, row in pivots:
        q[col] = matrix[row][-1]
    polys = [{(): coefficient} if coefficient else {} for coefficient in q]
    result = {}
    for multiplier, divisor in zip(polys, divisors):
        result = g.add(result, g.mul(multiplier, divisor))
    if result != goal:
        raise AssertionError('constant-combination system yielded invalid solution')
    return polys


def divides(goal, divisors):
    """Exact multivariate division with explicit polynomial quotient witnesses.

    A nonzero remainder is inconclusive, NOT a counterexample: divisors are
    not assumed to be a Groebner basis and no completeness is claimed.
    """
    names = sorted(set(g.variable_names(goal)).union(
        *(g.variable_names(p) for p in divisors)))
    basis = [p for p in divisors if p]
    basis_positions = [i for i, p in enumerate(divisors) if p]
    quotient = [{} for _ in divisors]
    dividend = dict(goal)
    residual = {}
    for step in range(MAX_STEPS):
        if not dividend:
            break
        top = leading(dividend, names)
        for index, divisor in zip(basis_positions, basis):
            head = leading(divisor, names)
            mono = quotient_monomial(top, head)
            if mono is None:
                continue
            coefficient = dividend[top] / divisor[head]
            piece = {mono: coefficient}
            quotient[index] = g.add(quotient[index], piece)
            dividend = g.add(dividend, g.mul(piece, divisor), -1)
            break
        else:
            residual = g.add(residual, {top: dividend[top]})
            del dividend[top]
    else:
        raise g.Unsupported('UNKNOWN: reduction exceeded safe step limit')
    if residual:
        raise g.Unsupported('UNKNOWN: nonzero division remainder; may still be a consequence')
    reconstructed = {}
    for multiplier, divisor in zip(quotient, divisors):
        reconstructed = g.add(reconstructed, g.mul(multiplier, divisor))
    if reconstructed != goal:
        raise AssertionError('failed independent quotient reconstruction')
    return quotient


def certify(hypotheses, goal):
    if not isinstance(hypotheses, list) or not (1 <= len(hypotheses) <= MAX_HYPOTHESES):
        raise g.Unsupported('provide 1 to 8 polynomial-equality hypotheses')
    if not isinstance(goal, str) or len(goal) > 500:
        raise g.Unsupported('goal must be an equation <=500 characters')
    diffs = []
    for hypothesis in hypotheses:
        if not isinstance(hypothesis, str) or len(hypothesis) > 500:
            raise g.Unsupported('each hypothesis must be an equation <=500 characters')
        a, b = g.equation(hypothesis)
        diffs.append(g.add(a, b, -1))
    a, b = g.equation(goal)
    target = g.add(a, b, -1)
    multipliers = constant_combination(target, diffs)
    if multipliers is None:
        multipliers = divides(target, diffs)
    cert = {'schema': CONDITIONAL_SCHEMA, 'kind': 'conditional',
            'hypotheses': hypotheses, 'goal': goal, 'domain': 'Q-polynomial',
            'verdict': 'PROVED',
            'evidence': {'multipliers_normal_forms': [normal_form(q) for q in multipliers]}}
    if len(json.dumps(cert, ensure_ascii=False).encode('utf-8')) > MAX_CERT_BYTES:
        raise g.Unsupported('certificate exceeds verifier size limit')
    return cert


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--given', action='append', required=True,
                        help='hypothesis equation, repeat for multiple assumptions')
    parser.add_argument('--goal', required=True, help='equation to derive')
    parser.add_argument('-o', '--output', help='certificate path, else stdout')
    args = parser.parse_args()
    try:
        certificate = certify(args.given, args.goal)
    except (g.Unsupported, OverflowError, RecursionError) as err:
        parser.error('UNKNOWN/UNSUPPORTED: ' + str(err))
    content = json.dumps(certificate, indent=2, ensure_ascii=False, sort_keys=True) + '\n'
    if len(content.encode('utf-8')) > MAX_CERT_BYTES:
        parser.error('UNKNOWN/UNSUPPORTED: formatted certificate too large')
    if args.output:
        Path(args.output).write_text(content, encoding='utf-8')
        print(f'CERTIFICATE CREATED: {args.output} (conditional PROVED)')
    else:
        print(content, end='')


if __name__ == '__main__':
    main()
