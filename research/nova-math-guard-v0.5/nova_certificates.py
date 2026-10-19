#!/usr/bin/env python3
"""Generate exact proof/refutation certificates for NOVA Math Guard v0.3.

Run independent_verifier.py separately to independently verify output.
"""
import argparse
import ast
import json
from fractions import Fraction
from pathlib import Path

import nova_math_guard as g
from independent_verifier import SCHEMA, MAX_CERT_BYTES


def normal_form(poly):
    return [
        {'monomial': [[name, degree] for name, degree in monomial], 'coefficient': str(coefficient)}
        for monomial, coefficient in sorted(poly.items())
    ]


def certify(kind, statement):
    if kind not in {'identity', 'linear'}:
        raise g.Unsupported('certificate kind must be identity or linear')
    lhs, rhs = g.equation(statement)
    # Keep even syntactic variables that vanished during simplification.
    syntactic_variables = {node.id for part in statement.split("=")
                           for node in ast.walk(ast.parse(part.strip(), mode="eval"))
                           if isinstance(node, ast.Name)}
    difference = g.add(lhs, rhs, -1)
    if kind == 'identity':
        evidence = {'lhs_normal_form': normal_form(lhs), 'rhs_normal_form': normal_form(rhs)}
        if not difference:
            verdict = 'PROVED'
        else:
            verdict = 'DISPROVED'
            point = g.find_counterexample(difference)
            for name in syntactic_variables:
                point.setdefault(name, Fraction(0))
            lvalue, rvalue = g.evaluate(lhs, point), g.evaluate(rhs, point)
            if lvalue == rvalue:
                raise AssertionError('failed counterexample validation')
            evidence.update({'assignment': {name: str(point[name]) for name in sorted(point)},
                             'lhs_value': str(lvalue), 'rhs_value': str(rvalue)})
    else:
        evidence = {'difference_normal_form': normal_form(difference)}
        names = g.variable_names(difference)
        if len(names) > 1:
            raise g.Unsupported('only one-variable linear equations can be certified')
        if not names:
            verdict = 'ALL' if not difference else 'NONE'
        else:
            variable = next(iter(names))
            a = Fraction(0)
            b = Fraction(0)
            for monomial, coefficient in difference.items():
                if not monomial:
                    b += coefficient
                elif monomial == ((variable, 1),):
                    a += coefficient
                else:
                    raise g.Unsupported('nonlinear equation cannot be certified')
            if not a:
                verdict = 'ALL' if not b else 'NONE'
            else:
                verdict = 'UNIQUE'
                answer = -b / a
                if g.evaluate(lhs, {variable: answer}) != g.evaluate(rhs, {variable: answer}):
                    raise AssertionError('substitution check failed')
                evidence.update({'variable': variable, 'solution': str(answer)})
    return {'schema': SCHEMA, 'kind': kind, 'statement': statement,
            'domain': 'Q-polynomial', 'verdict': verdict, 'evidence': evidence}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind', choices=['identity', 'linear'])
    parser.add_argument('statement', help='quote the equation, using ** for powers')
    parser.add_argument('-o', '--output', help='JSON destination (default: print to stdout)')
    args = parser.parse_args()
    try:
        doc = certify(args.kind, args.statement)
    except g.Unsupported as e:
        parser.error('UNKNOWN/UNSUPPORTED: ' + str(e))
    rendered = json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + '\n'
    if len(rendered.encode('utf-8')) > MAX_CERT_BYTES:
        parser.error('UNKNOWN/UNSUPPORTED: certificate exceeds independent verifier size limit')
    if args.output:
        Path(args.output).write_text(rendered, encoding='utf-8')
        print(f'CERTIFICATE CREATED: {args.output} ({doc["verdict"]})')
    else:
        print(rendered, end='')


if __name__ == '__main__':
    main()
