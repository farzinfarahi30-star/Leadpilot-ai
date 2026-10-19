#!/usr/bin/env python3
"""NOVA Math Guard v0.2 — dependency-free exact arithmetic and polynomial checking.

Supported: integer/rational arithmetic; multivariate polynomial identity checks;
linear equations in one variable over the rationals. No approximate floats.
The verdict UNKNOWN is intentional for problems outside the supported fragment.
"""
import argparse
import ast
from fractions import Fraction
from functools import reduce

MAX_POWER = 32
MAX_TERMS = 10000
MAX_DEGREE = 128
MAX_AST_NODES = 1000
MAX_MULTIPLICATIONS = 100000


class Unsupported(ValueError):
    pass


def clean(poly):
    return {m: c for m, c in poly.items() if c}


def add(a, b, sign=1):
    c = a.copy()
    if len(a) + len(b) > 2 * MAX_TERMS:
        raise Unsupported('expression expansion is too large')
    for m, v in b.items():
        c[m] = c.get(m, Fraction(0)) + sign * v
    return clean(c)


def mul(a, b):
    if len(a) * len(b) > MAX_MULTIPLICATIONS:
        raise Unsupported('expression multiplication is too large')
    c = {}
    for m, v in a.items():
        for n, w in b.items():
            powers = dict(m)
            for name, power in n:
                powers[name] = powers.get(name, 0) + power
            if sum(powers.values()) > MAX_DEGREE:
                raise Unsupported('polynomial degree exceeds limit')
            mono = tuple(sorted((k, p) for k, p in powers.items() if p))
            c[mono] = c.get(mono, Fraction(0)) + v * w
            if len(c) > MAX_TERMS:
                raise Unsupported('expression expansion is too large')
    return clean(c)


def const(p):
    if any(m for m in p):
        raise Unsupported('division or exponent requires a rational constant')
    return p.get((), Fraction(0))


def scale(p, factor):
    return clean({m: v * factor for m, v in p.items()})


def power(a, n):
    if n == 0 and not a:
        raise Unsupported('0**0 is convention-dependent and not accepted')
    if n < 0:
        value = const(a)
        if not value:
            raise Unsupported('division by zero')
        if n < -MAX_POWER:
            raise Unsupported('power exceeds limit')
        return {(): value ** n}
    if n > MAX_POWER:
        raise Unsupported('power exceeds limit')
    result = {(): Fraction(1)}
    while n:
        if n & 1:
            result = mul(result, a)
        n //= 2
        if n:
            a = mul(a, a)
    return result


def convert(node):
    if isinstance(node, ast.Constant) and type(node.value) is int:
        return {(): Fraction(node.value)} if node.value else {}
    if isinstance(node, ast.Name) and node.id.isidentifier() and not node.id.startswith('_'):
        return {((node.id, 1),): Fraction(1)}
    if isinstance(node, ast.UnaryOp):
        v = convert(node.operand)
        if isinstance(node.op, ast.USub):
            return scale(v, -1)
        if isinstance(node.op, ast.UAdd):
            return v
    if isinstance(node, ast.BinOp):
        a, b = convert(node.left), convert(node.right)
        if isinstance(node.op, ast.Add):
            return add(a, b)
        if isinstance(node.op, ast.Sub):
            return add(a, b, -1)
        if isinstance(node.op, ast.Mult):
            return mul(a, b)
        if isinstance(node.op, ast.Div):
            denom = const(b)
            if not denom:
                raise Unsupported('division by zero')
            return scale(a, 1 / denom)
        if isinstance(node.op, ast.Pow):
            exponent = const(b)
            if exponent.denominator != 1:
                raise Unsupported('fractional exponents not supported')
            return power(a, exponent.numerator)
    raise Unsupported('unsupported syntax; use integers, variables, + - * / ** and parentheses')


def parse(expression):
    if len(expression) > 500:
        raise Unsupported('input exceeds size limit')
    try:
        parsed = ast.parse(expression, mode='eval')
        if sum(1 for _ in ast.walk(parsed)) > MAX_AST_NODES:
            raise Unsupported('syntax tree is too large')
        return convert(parsed.body)
    except (SyntaxError, RecursionError, OverflowError) as e:
        raise Unsupported(f'could not parse input: {e}') from e


def equation(text):
    if text.count('=') != 1:
        raise Unsupported('provide exactly one = sign')
    left, right = map(str.strip, text.split('='))
    return parse(left), parse(right)


def variable_names(p):
    return {var for mono in p for var, _ in mono}


def substitute_variable(poly, variable, value):
    """Specialize one variable, retaining exact polynomial coefficients."""
    result = {}
    for monomial, coefficient in poly.items():
        powers = dict(monomial)
        exponent = powers.pop(variable, 0)
        residual = tuple(sorted(powers.items()))
        result[residual] = result.get(residual, Fraction(0)) + coefficient * value ** exponent
    return clean(result)


def find_counterexample(nonzero_poly):
    """Deterministically find an integer point where a nonzero polynomial is nonzero.

    For each variable, a nonzero polynomial of degree d over the integral
    domain Q[remaining variables] cannot have d+1 distinct roots. Trying
    0,...,d therefore preserves a nonzero polynomial at every step.
    """
    if not nonzero_poly:
        raise ValueError('a zero polynomial has no counterexample')
    remainder = nonzero_poly
    assignment = {}
    for variable in sorted(variable_names(nonzero_poly)):
        degree = max(dict(monomial).get(variable, 0) for monomial in remainder)
        for integer in range(degree + 1):
            candidate = substitute_variable(remainder, variable, Fraction(integer))
            if candidate:
                assignment[variable] = Fraction(integer)
                remainder = candidate
                break
        else:
            raise AssertionError('failed to construct polynomial witness')
    if const(remainder) == 0:
        raise AssertionError('constructed witness does not refute identity')
    return assignment


def evaluate(poly, assignment):
    total = Fraction(0)
    for monomial, coefficient in poly.items():
        term = coefficient
        for variable, degree in monomial:
            term *= assignment[variable] ** degree
        total += term
    return total


def check_identity(text):
    left, right = equation(text)
    diff = add(left, right, -1)
    if not diff:
        return 'PROVED: polynomial identity (exact rational-coefficient normal form).'
    assignment = find_counterexample(diff)
    for variable in variable_names(left) | variable_names(right):
        assignment.setdefault(variable, Fraction(0))
    a, b = evaluate(left, assignment), evaluate(right, assignment)
    if a == b:
        raise AssertionError('counterexample was not independently verified')
    assigned = ', '.join(f'{name}={assignment[name]}' for name in sorted(assignment))
    return f'DISPROVED: exact counterexample [{assigned or "no variables"}]; left={a}; right={b}.'


def solve_linear(text):
    left, right = equation(text)
    diff = add(left, right, -1)
    variables = variable_names(diff)
    if not variables:
        return 'ALL RATIONAL VALUES: equation is always true.' if not diff else 'NO SOLUTION: unequal constants.'
    if len(variables) != 1:
        raise Unsupported('only one-variable linear equations are supported')
    var = next(iter(variables))
    a = Fraction(0)
    b = Fraction(0)
    for mono, coeff in diff.items():
        if mono == ():
            b += coeff
        elif mono == ((var, 1),):
            a += coeff
        else:
            raise Unsupported('only linear equations are supported; cannot claim completeness')
    if a == 0:
        return 'ALL RATIONAL VALUES: equation is always true.' if b == 0 else 'NO SOLUTION: contradictory constants.'
    answer = -b / a
    # Independent substitution check using original polynomial forms.
    if evaluate(left, {var: answer}) != evaluate(right, {var: answer}):
        raise AssertionError('candidate did not survive independent substitution')
    return f'PROVED: unique rational solution {var} = {answer} (exact substitution checked).'


def calculate(text):
    return f'EXACT: {const(parse(text))}'


def selftest():
    cases = [
        ('calc', '1/3 + 2/7', 'EXACT: 13/21'),
        ('calc', '(2**20 - 1)/7', 'EXACT: 1048575/7'),
        ('prove', '(x+y)**2 = x**2+2*x*y+y**2', 'PROVED:'),
        ('prove', '(a+b)*(a-b)=a**2-b**2', 'PROVED:'),
        ('prove', '(x+1)**3 = x**3+3*x**2+3*x+1', 'PROVED:'),
        ('prove', 'x**2=x', 'DISPROVED:'),
        ('prove', '1/3+1/6=1/2', 'PROVED:'),
        ('solve', '3*x+7=22', 'x = 5'),
        ('solve', 'x/3+2=1/2', 'x = -9/2'),
        ('solve', '2*x+1=2*x+2', 'NO SOLUTION:'),
        ('solve', '2*x+1=2*x+1', 'ALL RATIONAL VALUES:'),
        ('solve', '0*x=4', 'NO SOLUTION:'),
    ]
    handlers = {'calc': calculate, 'prove': check_identity, 'solve': solve_linear}
    for mode, expr, expect in cases:
        ans = handlers[mode](expr)
        assert expect in ans, (mode, expr, ans)
    rejected = [
        ('calc', '0.1+0.2'),  # refuse floating-point approximations
        ('calc', '__import__("os").system("echo evil")'),
        ('prove', 'x/y=1'),
        ('solve', 'x**2=4'),
        ('solve', 'x+y=3'),
        ('calc', '1/0'),
        ('calc', '0**0'),
        ('calc', 'x**129'),
    ]
    for mode, expr in rejected:
        try:
            handlers[mode](expr)
        except Unsupported:
            pass
        else:
            raise AssertionError(f'must refuse unsupported input: {mode} {expr}')
    print(f'PASS: {len(cases)} exact cases + {len(rejected)} refusal tests.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['calc', 'prove', 'solve', 'selftest'])
    parser.add_argument('expression', nargs='?', help='quoted expression or equation; use ** for powers')
    args = parser.parse_args()
    if args.mode == 'selftest':
        selftest()
        return
    if not args.expression:
        parser.error('expression is required')
    try:
        print({'calc': calculate, 'prove': check_identity, 'solve': solve_linear}[args.mode](args.expression))
    except Unsupported as e:
        print(f'UNKNOWN/UNSUPPORTED: {e}')


if __name__ == '__main__':
    main()
