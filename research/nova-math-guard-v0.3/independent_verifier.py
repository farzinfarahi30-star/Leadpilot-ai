#!/usr/bin/env python3
"""Independent NOVA Math Guard certificate verifier (Python stdlib only).

This module does not import the certificate generator or NOVA Math Guard.
It reconstructs polynomial semantics using exponent vectors, rather than
NOVA Math Guard's named sparse-monomial representation.

IMPORTANT: a verified certificate is only a proof of the precise statement in
Q[variables], not of an arbitrary theorem or a solution to an open problem.
"""
import ast
import json
import sys
from fractions import Fraction
from pathlib import Path

SCHEMA = 'NOVA-MATH-GUARD-CERT-1'
MAX_INPUT = 500
MAX_AST_NODES = 1000
MAX_TERMS = 10000
MAX_POWER = 32
MAX_DEGREE = 128
MAX_MULTIPLICATIONS = 100000
MAX_CERT_BYTES = 65536


class VerificationError(ValueError):
    pass


def fail(message):
    raise VerificationError(message)


def rational(s):
    if not isinstance(s, str) or len(s) > 512:
        fail('rational evidence must be a short string')
    try:
        value = Fraction(s)
    except (ValueError, ZeroDivisionError, TypeError, OverflowError):
        fail('invalid rational evidence')
    if str(value) != s:
        fail('rational evidence is not canonical')
    return value


class Symbolic:
    def __init__(self, variable_names):
        self.names = tuple(sorted(variable_names))
        self.zero = (0,) * len(self.names)
        self.position = {name: i for i, name in enumerate(self.names)}

    def constant(self, value):
        value = Fraction(value)
        return {self.zero: value} if value else {}

    def scalar(self, p):
        if set(p) - {self.zero}:
            fail('denominator/exponent requires a rational constant')
        return p.get(self.zero, Fraction(0))

    @staticmethod
    def tidy(p):
        out = {k: v for k, v in p.items() if v}
        if len(out) > MAX_TERMS:
            fail('too many terms')
        return out

    def plus(self, a, b, sign=1):
        result = dict(a)
        for powers, coefficient in b.items():
            result[powers] = result.get(powers, Fraction(0)) + sign * coefficient
        return self.tidy(result)

    def times(self, a, b):
        if len(a) * len(b) > MAX_MULTIPLICATIONS:
            fail('polynomial multiplication too large')
        result = {}
        for am, ac in a.items():
            for bm, bc in b.items():
                monomial = tuple(x + y for x, y in zip(am, bm))
                if sum(monomial) > MAX_DEGREE:
                    fail('degree too large')
                result[monomial] = result.get(monomial, Fraction(0)) + ac * bc
                if len(result) > MAX_TERMS:
                    fail('too many terms')
        return self.tidy(result)

    def raised(self, base, integer):
        if abs(integer) > MAX_POWER:
            fail('exponent too large')
        if integer == 0 and not base:
            fail('0**0 is not supported')
        if integer < 0:
            val = self.scalar(base)
            if not val:
                fail('division by zero')
            return self.constant(val ** integer)
        result = self.constant(1)
        for _ in range(integer):
            result = self.times(result, base)
        return result

    def expression(self, node):
        if isinstance(node, ast.Constant) and type(node.value) is int:
            return self.constant(node.value)
        if isinstance(node, ast.Name) and node.id in self.position:
            unit = list(self.zero)
            unit[self.position[node.id]] = 1
            return {tuple(unit): Fraction(1)}
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            operand = self.expression(node.operand)
            return operand if isinstance(node.op, ast.UAdd) else self.times(self.constant(-1), operand)
        if isinstance(node, ast.BinOp):
            lhs, rhs = self.expression(node.left), self.expression(node.right)
            if isinstance(node.op, ast.Add):
                return self.plus(lhs, rhs)
            if isinstance(node.op, ast.Sub):
                return self.plus(lhs, rhs, -1)
            if isinstance(node.op, ast.Mult):
                return self.times(lhs, rhs)
            if isinstance(node.op, ast.Div):
                denominator = self.scalar(rhs)
                if not denominator:
                    fail('division by zero')
                return self.times(lhs, self.constant(1 / denominator))
            if isinstance(node.op, ast.Pow):
                power = self.scalar(rhs)
                if power.denominator != 1:
                    fail('fractional exponent unsupported')
                return self.raised(lhs, power.numerator)
        fail('unsupported expression syntax')

    def normal_form(self, p):
        return [
            {'monomial': [[name, degree] for name, degree in zip(self.names, monomial) if degree],
             'coefficient': str(coefficient)}
            for monomial, coefficient in sorted(p.items(), key=lambda item: tuple((name, degree) for name, degree in zip(self.names, item[0]) if degree))
        ]

    def evaluate(self, p, assignment):
        total = Fraction(0)
        for monomial, coefficient in p.items():
            term = coefficient
            for name, power in zip(self.names, monomial):
                term *= assignment[name] ** power
            total += term
        return total


def parse_equation(text):
    if not isinstance(text, str) or len(text) > MAX_INPUT or text.count('=') != 1:
        fail('expected one equation no longer than 500 characters')
    left, right = (part.strip() for part in text.split('='))
    try:
        trees = [ast.parse(part, mode='eval') for part in (left, right)]
    except (SyntaxError, RecursionError, MemoryError, OverflowError):
        fail('invalid equation syntax')
    if sum(1 for tree in trees for _ in ast.walk(tree)) > MAX_AST_NODES:
        fail('syntax tree too large')
    names = set()
    for tree in trees:
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if not node.id.isidentifier() or node.id.startswith('_'):
                    fail('invalid variable name')
                names.add(node.id)
    engine = Symbolic(names)
    try:
        return engine, engine.expression(trees[0].body), engine.expression(trees[1].body)
    except (RecursionError, OverflowError, MemoryError):
        fail('equation exceeds computation limits')


def verify_certificate(document):
    if not isinstance(document, dict) or set(document) != {'schema', 'kind', 'statement', 'domain', 'verdict', 'evidence'}:
        fail('certificate has incorrect structure')
    if document['schema'] != SCHEMA or document['domain'] != 'Q-polynomial':
        fail('unsupported schema or domain')
    if document['kind'] not in ('identity', 'linear') or not isinstance(document['evidence'], dict):
        fail('invalid kind or evidence')

    engine, lhs, rhs = parse_equation(document['statement'])
    diff = engine.plus(lhs, rhs, -1)
    evidence = document['evidence']

    if document['kind'] == 'identity':
        if not {'lhs_normal_form', 'rhs_normal_form'} <= set(evidence):
            fail('identity missing normal forms')
        if evidence['lhs_normal_form'] != engine.normal_form(lhs) or evidence['rhs_normal_form'] != engine.normal_form(rhs):
            fail('normal form does not match independently recomputed result')
        if document['verdict'] == 'PROVED':
            if set(evidence) != {'lhs_normal_form', 'rhs_normal_form'} or lhs != rhs:
                fail('invalid equality claim')
        elif document['verdict'] == 'DISPROVED':
            if set(evidence) != {'lhs_normal_form', 'rhs_normal_form', 'assignment', 'lhs_value', 'rhs_value'}:
                fail('counterexample evidence incomplete')
            assignment = evidence['assignment']
            if not isinstance(assignment, dict) or set(assignment) != set(engine.names):
                fail('missing or extra variable values in counterexample')
            values = {key: rational(assignment[key]) for key in engine.names}
            left_value, right_value = engine.evaluate(lhs, values), engine.evaluate(rhs, values)
            if left_value == right_value or str(left_value) != evidence['lhs_value'] or str(right_value) != evidence['rhs_value']:
                fail('counterexample does not refute equality')
        else:
            fail('invalid identity verdict')
        return f'VERIFIED {document["verdict"]}: exact polynomial identity certificate over Q'

    if set(evidence) not in ({'difference_normal_form'}, {'difference_normal_form', 'variable', 'solution'}):
        fail('incorrect linear evidence')
    if evidence['difference_normal_form'] != engine.normal_form(diff):
        fail('incorrect equation normal form')
    variables = {name for powers in diff for name, exponent in zip(engine.names, powers) if exponent}
    if len(variables) > 1:
        fail('not a one-variable linear equation')
    if not variables:
        outcome = 'ALL' if not diff else 'NONE'
        if document['verdict'] != outcome or len(evidence) != 1:
            fail('wrong constant-equation outcome')
        return f'VERIFIED {outcome}: constant rational equation'
    variable = next(iter(variables))
    a = Fraction(0)
    b = Fraction(0)
    for powers, coefficient in diff.items():
        if powers == engine.zero:
            b += coefficient
        elif powers[engine.position[variable]] == 1 and sum(powers) == 1:
            a += coefficient
        else:
            fail('nonlinear expression cannot carry a linear certificate')
    if a == 0:
        outcome = 'ALL' if b == 0 else 'NONE'
        if document['verdict'] != outcome or len(evidence) != 1:
            fail('wrong degenerate-linear outcome')
        return f'VERIFIED {outcome}: exact linear equation'
    answer = -b / a
    if document['verdict'] != 'UNIQUE' or evidence.get('variable') != variable or evidence.get('solution') != str(answer):
        fail('incorrect unique-solution claim')
    if engine.evaluate(lhs, {variable: answer, **{n: Fraction(0) for n in engine.names if n != variable}}) != engine.evaluate(rhs, {variable: answer, **{n: Fraction(0) for n in engine.names if n != variable}}):
        fail('solution substitution failed')
    return f'VERIFIED UNIQUE: {variable}={answer} over Q'


def main():
    if len(sys.argv) != 2:
        print('Usage: python3 independent_verifier.py certificate.json', file=sys.stderr)
        sys.exit(2)
    try:
        target = Path(sys.argv[1])
        if target.stat().st_size > MAX_CERT_BYTES:
            fail('certificate too large')
        document = json.loads(target.read_text(encoding='utf-8'))
        print(verify_certificate(document))
    except (VerificationError, OSError, ValueError, TypeError) as ex:
        print(f'REJECTED: {ex}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
