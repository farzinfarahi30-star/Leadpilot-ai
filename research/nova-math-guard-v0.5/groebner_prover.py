#!/usr/bin/env python3
"""Bounded Buchberger completion with lifted Q[X]-ideal membership certificates.

For each generated basis polynomial b_j, retain explicit coefficients h_ji
such that b_j = sum_i h_ji * f_i, where f_i are original hypotheses.
If goal reduces to zero, reconstruct multipliers for original f_i.

This is a *search* algorithm, never a proof checker: the independent verifier
must validate the returned certificate. Resource exhaustion means UNKNOWN.
"""
from collections import deque
from fractions import Fraction
import nova_math_guard as g

MAX_BASIS = 48
MAX_PAIRS = 600
MAX_DIVISION_STEPS = 2500
MAX_TOTAL_DIVISION_STEPS = 30000


def leading(poly, names):
    return max(poly, key=lambda mono: (sum(power for _, power in mono),
                                       tuple(dict(mono).get(name, 0) for name in names)))


def monomial_divide(numerator, denominator):
    powers = dict(numerator)
    for name, exponent in denominator:
        if powers.get(name, 0) < exponent:
            return None
        powers[name] -= exponent
    return tuple(sorted((name, degree) for name, degree in powers.items() if degree))


def monomial_lcm(a, b):
    merged = dict(a)
    for name, exponent in b:
        merged[name] = max(exponent, merged.get(name, 0))
    return tuple(sorted(merged.items()))


def monic(poly, vector, names):
    coeff = poly[leading(poly, names)]
    if coeff == 1:
        return poly, vector
    return g.scale(poly, Fraction(1) / coeff), [g.scale(q, Fraction(1) / coeff) for q in vector]


class Budget:
    steps = 0

    def tick(self):
        self.steps += 1
        if self.steps > MAX_TOTAL_DIVISION_STEPS:
            raise g.Unsupported('UNKNOWN: Groebner search exhausted total reduction budget')


def reduce(poly, basis, names, budget):
    """Return (remainder, quotients) where poly == rem + sum(q_i * basis_i)."""
    dividend = dict(poly)
    quotients = [{} for _ in basis]
    remainder = {}
    for _ in range(MAX_DIVISION_STEPS):
        if not dividend:
            return remainder, quotients
        budget.tick()
        head = leading(dividend, names)
        for j, basis_poly in enumerate(basis):
            generator_head = leading(basis_poly, names)
            difference = monomial_divide(head, generator_head)
            if difference is not None:
                coefficient = dividend[head] / basis_poly[generator_head]
                factor = {difference: coefficient}
                quotients[j] = g.add(quotients[j], factor)
                dividend = g.add(dividend, g.mul(factor, basis_poly), -1)
                break
        else:
            remainder[head] = dividend.pop(head)
            if len(remainder) > g.MAX_TERMS:
                raise g.Unsupported('UNKNOWN: remainder too large')
    raise g.Unsupported('UNKNOWN: Groebner division exhausted per-polynomial budget')


def combine(vector, other, factor, sign=1):
    return [g.add(a, g.mul(factor, b), sign) for a, b in zip(vector, other)]


def ideal_membership(target, generators):
    """Return exact multipliers Q_i with target=sum Q_i*generators, else UNKNOWN.

    If the degree/term/step/basis limits do not bind, Buchberger termination and
    the normal-form criterion decide ideal membership over Q[X]. This bounded
    implementation conservatively returns UNKNOWN on nonzero remainder.
    """
    names = sorted(set(g.variable_names(target)).union(*(g.variable_names(f) for f in generators)))
    n = len(generators)
    if not target:
        return [{} for _ in generators]
    basis = []
    lifts = []
    for i, f in enumerate(generators):
        if not f:
            continue
        lift = [{} for _ in generators]
        lift[i] = {(): Fraction(1)}
        normalized_poly, normalized_lift = monic(f, lift, names)
        basis.append(normalized_poly)
        lifts.append(normalized_lift)
    if not basis:
        raise g.Unsupported('UNKNOWN: zero hypotheses do not generate a nonzero goal')
    pairs = deque((i, j) for i in range(len(basis)) for j in range(i))
    budget = Budget()
    pair_count = 0
    while pairs:
        i, j = pairs.popleft()
        pair_count += 1
        if pair_count > MAX_PAIRS:
            raise g.Unsupported('UNKNOWN: Groebner pair budget exhausted')
        bi, bj = basis[i], basis[j]
        hi, hj = leading(bi, names), leading(bj, names)
        lcm = monomial_lcm(hi, hj)
        fi = {monomial_divide(lcm, hi): Fraction(1) / bi[hi]}
        fj = {monomial_divide(lcm, hj): Fraction(1) / bj[hj]}
        sp = g.add(g.mul(fi, bi), g.mul(fj, bj), -1)
        if not sp:
            continue
        s_lift = combine(
            [g.mul(fi, v) for v in lifts[i]],
            lifts[j], fj, -1,
        )
        rem, qs = reduce(sp, basis, names, budget)
        if not rem:
            continue
        for q, lift in zip(qs, lifts):
            if q:
                s_lift = combine(s_lift, lift, q, -1)
        if len(basis) >= MAX_BASIS:
            raise g.Unsupported('UNKNOWN: Groebner basis-size limit exceeded')
        rem, s_lift = monic(rem, s_lift, names)
        # Every new polynomial must retain an exact witness in original generators.
        if g.add(
            rem,
            sum_lifts(s_lift, generators), -1,
        ):
            raise AssertionError('Groebner lifted witness reconstruction failed')
        new_id = len(basis)
        pairs.extend((new_id, j) for j in range(new_id))
        basis.append(rem)
        lifts.append(s_lift)
    rem, qs = reduce(target, basis, names, budget)
    if rem:
        raise g.Unsupported('UNKNOWN: target not in the generated ideal over Q[X]')
    result = [{} for _ in generators]
    for q, lift in zip(qs, lifts):
        if q:
            result = combine(result, lift, q)
    if g.add(target, sum_lifts(result, generators), -1):
        raise AssertionError('Groebner target witness reconstruction failed')
    return result


def sum_lifts(multipliers, generators):
    total = {}
    for q, f in zip(multipliers, generators):
        total = g.add(total, g.mul(q, f))
    return total
