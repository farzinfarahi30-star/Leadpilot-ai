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
CONDITIONAL_SCHEMA = 'NOVA-MATH-GUARD-CONDITIONAL-CERT-1'
RADICAL_SCHEMA = 'NOVA-MATH-GUARD-RADICAL-CERT-1'
CONDITIONAL_COUNTEREXAMPLE_SCHEMA = 'NOVA-MATH-GUARD-CONDITIONAL-COUNTEREXAMPLE-CERT-1'
REAL_SOS_SCHEMA = 'NOVA-MATH-GUARD-REAL-SOS-CERT-1'
REAL_SOS_POWER_SCHEMA = 'NOVA-MATH-GUARD-REAL-SOS-POWER-CERT-2'
MAX_RADICAL_EXPONENT = 4
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



def as_joint_polynomials(statements):
    """Re-encode independently parsed equations into one shared Q[X] ring."""
    parsed = [parse_equation(statement) for statement in statements]
    all_variables = set()
    for parser, _, _ in parsed:
        all_variables.update(parser.names)
    engine = Symbolic(all_variables)
    def lift(old_engine, p):
        return {
            tuple(m[old_engine.position[name]] if name in old_engine.position else 0
                  for name in engine.names): coefficient
            for m, coefficient in p.items()
        }
    return engine, [(lift(old, lhs), lift(old, rhs)) for old, lhs, rhs in parsed]


def load_normal_form(engine, data):
    """Parse an exact, strictly canonical polynomial representation."""
    if not isinstance(data, list) or len(data) > MAX_TERMS:
        fail('invalid multiplier normal form')
    result = {}
    for term in data:
        if not isinstance(term, dict) or set(term) != {'monomial', 'coefficient'}:
            fail('invalid multiplier term')
        monomial = term['monomial']
        if not isinstance(monomial, list) or len(monomial) > len(engine.names):
            fail('invalid multiplier monomial')
        power_vector = [0] * len(engine.names)
        seen = set()
        for factor in monomial:
            if (not isinstance(factor, list) or len(factor) != 2 or
                    not isinstance(factor[0], str) or factor[0] not in engine.position or
                    type(factor[1]) is not int or factor[1] <= 0 or factor[1] > MAX_DEGREE or
                    factor[0] in seen):
                fail('invalid multiplier monomial exponent/variable')
            seen.add(factor[0])
            power_vector[engine.position[factor[0]]] = factor[1]
        if sum(power_vector) > MAX_DEGREE:
            fail('multiplier monomial degree too large')
        coefficient = rational(term['coefficient'])
        if not coefficient or tuple(power_vector) in result:
            fail('zero or duplicate multiplier term')
        result[tuple(power_vector)] = coefficient
    if engine.normal_form(result) != data:
        fail('multiplier normal form is not canonical')
    return result


def verify_conditional(document):
    if not isinstance(document, dict) or set(document) != {
            'schema', 'kind', 'hypotheses', 'goal', 'domain', 'verdict', 'evidence'}:
        fail('conditional certificate has incorrect structure')
    if (document['schema'] != CONDITIONAL_SCHEMA or document['kind'] != 'conditional' or
            document['domain'] != 'Q-polynomial' or document['verdict'] != 'PROVED'):
        fail('unsupported conditional certificate')
    hypotheses = document['hypotheses']
    if not isinstance(hypotheses, list) or not 1 <= len(hypotheses) <= 8:
        fail('expected 1-8 hypotheses')
    evidence = document['evidence']
    if not isinstance(evidence, dict) or set(evidence) != {'multipliers_normal_forms'}:
        fail('incorrect conditional evidence')
    forms = evidence['multipliers_normal_forms']
    if not isinstance(forms, list) or len(forms) != len(hypotheses):
        fail('one multiplier required per hypothesis')
    engine, equations = as_joint_polynomials([*hypotheses, document['goal']])
    basis = [engine.plus(lhs, rhs, -1) for lhs, rhs in equations[:-1]]
    target = engine.plus(equations[-1][0], equations[-1][1], -1)
    reconstructed = {}
    for divisor, normal_form in zip(basis, forms):
        quotient = load_normal_form(engine, normal_form)
        reconstructed = engine.plus(reconstructed, engine.times(quotient, divisor))
    if target != reconstructed:
        fail('goal does not equal combination of hypotheses')
    return 'VERIFIED PROVED: polynomial consequence under specified equality hypotheses over Q'


def verify_radical(document):
    """Check t**k == sum(q_i * h_i), hence t=0 at every field-valued zero.

    This verifier is separate from the witness search. The proof relies only
    on the absence of nonzero nilpotents in fields (and more generally reduced
    Q-algebras); arbitrary commutative Q-algebras are NOT covered.
    """
    required = {'schema', 'kind', 'hypotheses', 'goal', 'domain', 'verdict', 'evidence'}
    if not isinstance(document, dict) or set(document) != required:
        fail('radical certificate has incorrect structure')
    if (document['schema'] != RADICAL_SCHEMA or document['kind'] != 'radical' or
            document['domain'] != 'Q-polynomial' or document['verdict'] != 'PROVED'):
        fail('unsupported radical certificate')
    hypotheses = document['hypotheses']
    if not isinstance(hypotheses, list) or not 1 <= len(hypotheses) <= 8:
        fail('expected 1-8 hypotheses')
    evidence = document['evidence']
    if not isinstance(evidence, dict) or set(evidence) != {'power', 'multipliers_normal_forms'}:
        fail('invalid radical evidence structure')
    exponent = evidence['power']
    if type(exponent) is not int or not 2 <= exponent <= MAX_RADICAL_EXPONENT:
        fail('invalid radical exponent')
    forms = evidence['multipliers_normal_forms']
    if not isinstance(forms, list) or len(forms) != len(hypotheses):
        fail('one multiplier required per hypothesis')
    engine, equations = as_joint_polynomials([*hypotheses, document['goal']])
    basis = [engine.plus(lhs, rhs, -1) for lhs, rhs in equations[:-1]]
    target = engine.plus(equations[-1][0], equations[-1][1], -1)
    powered_goal = engine.raised(target, exponent)
    reconstructed = {}
    for divisor, form in zip(basis, forms):
        quotient = load_normal_form(engine, form)
        reconstructed = engine.plus(reconstructed, engine.times(quotient, divisor))
    if powered_goal != reconstructed:
        fail('goal power does not equal combination of hypotheses')
    return f'VERIFIED PROVED: goal follows from equalities at all common zeros over fields containing Q (power {exponent})'


def verify_real_sos(document):
    """Prove t=0 over all ordered fields via a checkable exact SOS identity.

    t**2 + sum_j positive_weight_j * square(polynomial_j)
          == sum_i polynomial_multiplier_i * hypothesis_i.

    A zero sum of nonnegative elements in an ordered field forces t=0.
    This deliberately does NOT certify a claim over C or arbitrary fields.
    """
    keys = {'schema', 'kind', 'hypotheses', 'goal', 'domain', 'verdict', 'evidence'}
    if not isinstance(document, dict) or set(document) != keys:
        fail('invalid real SOS certificate structure')
    if (document['schema'] not in (REAL_SOS_SCHEMA, REAL_SOS_POWER_SCHEMA) or
            document['kind'] != 'real-sos' or
            document['domain'] != 'ordered-fields-over-Q' or
            document['verdict'] != 'PROVED'):
        fail('invalid real SOS domain or verdict')
    hypotheses = document['hypotheses']
    if not isinstance(hypotheses, list) or not 1 <= len(hypotheses) <= 8:
        fail('expected 1-8 equality hypotheses')
    evidence = document['evidence']
    power_schema = document['schema'] == REAL_SOS_POWER_SCHEMA
    required_keys = {'multipliers_normal_forms', 'weighted_squares'}
    if power_schema:
        required_keys.add('goal_even_power')
    if not isinstance(evidence, dict) or set(evidence) != required_keys:
        fail('invalid real SOS evidence')
    power = evidence['goal_even_power'] if power_schema else 2
    if type(power) is not int or power not in (2, 4, 6, 8):
        fail('goal power must be one of 2, 4, 6, 8')
    forms = evidence['multipliers_normal_forms']
    squares = evidence['weighted_squares']
    if (not isinstance(forms, list) or len(forms) != len(hypotheses) or
            not isinstance(squares, list) or not 1 <= len(squares) <= 32):
        fail('wrong number of SOS multipliers or squares')
    engine, equations = as_joint_polynomials([*hypotheses, document['goal']])
    hypothesis_polys = [engine.plus(left, right, -1) for left, right in equations[:-1]]
    target = engine.plus(equations[-1][0], equations[-1][1], -1)
    lhs = engine.raised(target, power)
    for square in squares:
        if not isinstance(square, dict) or set(square) != {'weight', 'polynomial_normal_form'}:
            fail('invalid weighted square structure')
        weight = rational(square['weight'])
        if weight <= 0:
            fail('SOS weights must be strictly positive rationals')
        polynomial = load_normal_form(engine, square['polynomial_normal_form'])
        if not polynomial:
            fail('zero polynomial is not a valid SOS component')
        squared = engine.times(polynomial, polynomial)
        lhs = engine.plus(lhs, engine.times(engine.constant(weight), squared))
    rhs = {}
    for hypothesis, form in zip(hypothesis_polys, forms):
        multiplier = load_normal_form(engine, form)
        rhs = engine.plus(rhs, engine.times(hypothesis, multiplier))
    if lhs != rhs:
        fail('alleged real SOS polynomial identity is false')
    return (f'VERIFIED PROVED: exact real SOS certificate with target power {power}; '
            'conclusion holds in every ordered field containing Q')


def verify_conditional_counterexample(document):
    """Independently check a rational point satisfying every hypothesis,
    while falsifying the goal. No proof-search code is imported.
    """
    fields = {'schema', 'kind', 'hypotheses', 'goal', 'domain', 'verdict', 'evidence'}
    if not isinstance(document, dict) or set(document) != fields:
        fail('incorrect counterexample certificate structure')
    if (document['schema'] != CONDITIONAL_COUNTEREXAMPLE_SCHEMA or
            document['kind'] != 'conditional-counterexample' or
            document['domain'] != 'Q-polynomial' or document['verdict'] != 'DISPROVED'):
        fail('unsupported conditional counterexample certificate')
    hypotheses = document['hypotheses']
    if not isinstance(hypotheses, list) or not 1 <= len(hypotheses) <= 8:
        fail('expected 1-8 equality hypotheses')
    evidence = document['evidence']
    if not isinstance(evidence, dict) or set(evidence) != {
            'assignment', 'hypotheses_values', 'goal_values'}:
        fail('invalid counterexample evidence keys')
    engine, equations = as_joint_polynomials([*hypotheses, document['goal']])
    values = evidence['assignment']
    if not isinstance(values, dict) or set(values) != set(engine.names):
        fail('assignment must contain precisely all statement variables')
    assignment = {name: rational(values[name]) for name in engine.names}
    hypo_evidence = evidence['hypotheses_values']
    if not isinstance(hypo_evidence, list) or len(hypo_evidence) != len(hypotheses):
        fail('expected values for every hypothesis')
    for (lhs, rhs), reported in zip(equations[:-1], hypo_evidence):
        if not isinstance(reported, dict) or set(reported) != {'lhs', 'rhs'}:
            fail('invalid hypothesis evaluation')
        left, right = engine.evaluate(lhs, assignment), engine.evaluate(rhs, assignment)
        if left != right or reported['lhs'] != str(left) or reported['rhs'] != str(right):
            fail('a hypothesis is false or an evaluation was forged')
    report = evidence['goal_values']
    if not isinstance(report, dict) or set(report) != {'lhs', 'rhs'}:
        fail('invalid goal evaluation')
    lhs, rhs = equations[-1]
    left, right = engine.evaluate(lhs, assignment), engine.evaluate(rhs, assignment)
    if left == right or report['lhs'] != str(left) or report['rhs'] != str(right):
        fail('goal is true at assigned point or an evaluation was forged')
    return ('VERIFIED DISPROVED: rational point satisfies every premise and '
            'falsifies the conclusion; implication fails over Q and fields containing Q')


def verify_certificate(document):
    if isinstance(document, dict) and document.get('schema') in (REAL_SOS_SCHEMA, REAL_SOS_POWER_SCHEMA):
        return verify_real_sos(document)
    if isinstance(document, dict) and document.get('schema') == CONDITIONAL_COUNTEREXAMPLE_SCHEMA:
        return verify_conditional_counterexample(document)
    if isinstance(document, dict) and document.get('schema') == CONDITIONAL_SCHEMA:
        return verify_conditional(document)
    if isinstance(document, dict) and document.get('schema') == RADICAL_SCHEMA:
        return verify_radical(document)
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
