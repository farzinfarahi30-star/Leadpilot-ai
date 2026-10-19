# NOVA Math Guard v0.9 — exact even-power real certificates

**Status:** small, experimentally tested mathematical verification prototype.
**Historical breakthrough claim:** **none**. All included mathematical examples are known.
**Cost:** no paid API calls. Essential code uses only Python 3 standard library;
optional SymPy is for separate differential checks.

This release is an incremental improvement with a concrete, measured capability gain:
**the previous release returned UNKNOWN for `x^4 + y^4 = 0 -> x = 0` over
ordered fields; v0.9 produces an exact, independently checked certificate.**
The same technique also handles selected degree-6 and degree-8 cases.

## Run

```sh
python3 run_all.py
python3 real_sos_prover.py --sos-only --given 'x**4+y**4=0' --goal 'x=0' -o /tmp/quartic.json
python3 independent_verifier.py /tmp/quartic.json
python3 research_backchain.py
```

Full offline regression tests are dependency-free. If SymPy is available,
`run_all.py` additionally cross-checks 300 exact even-power certificates plus
300 earlier quadratic examples. Pass `--with-differential` to include the
3,300 previous randomized algebra comparisons.

## New proof format

`NOVA-MATH-GUARD-REAL-SOS-POWER-CERT-2` describes the exact polynomial identity

```
  (goal_left - goal_right)^(2k) + sum_j c_j * s_j^2
    = sum_i q_i * (hypothesis_i_left - hypothesis_i_right)
```

where `2k in {2,4,6,8}`, `c_j` are strictly positive rational numbers,
`q_i` and `s_j` are rational-coefficient polynomials, and the identity is
verified exactly by `independent_verifier.py`. The conclusion follows for
**every assignment to an ordered field containing Q** that satisfies all
hypothesis equations, since a sum of squares with nonnegative weights can
vanish only when each summand vanishes. The claim is **not** over C.

For `x^4+y^4=0` and goal `x=0`, the certificate states precisely:

```
  x^4 + (y^2)^2 = 1*(x^4+y^4)
```

Under the hypothesis, both summands on the left are nonnegative; hence
`x^4=0` and `x=0` over an ordered field. This result is elementary and
**not a new theorem**.

The new constructor combines bounded constant multipliers with two exact
sufficient SOS heuristics:
- rational Gram/LDL decomposition of some degree-2 polynomials;
- sums of positive rational multiples of squares of monomials, up to 32 terms.

The search tries at most 4,000 constant-multiplier candidates and four
even goal powers. It is **incomplete**. Search failure returns `UNKNOWN`, not
a counterexample. Rational counterexamples are independently checked and may
return `DISPROVED` when one is found.

## Evidence included

- `certificates/real_power_quartic.json`, `real_power_sextic.json`,
  `real_power_octic.json`, `real_power_mixed.json` — checkable exact witnesses.
- `test_real_sos_powers.py` — adversarial mutations, compatibility checks,
  400 seeded monomial-SOS reconstructions and 240 seeded valid proofs.
- `differential_real_power_sympy_optional.py` — 300 SymPy identity checks.
- `BENCHMARK_DELTA.json` and `.md` — independently checked 12-case before/after
  comparison; v0.8: 5 PROVED, 2 DISPROVED, 5 UNKNOWN; v0.9: 9, 2, 1.
- `research_backchain.py` and `RESEARCH_BACKCHAIN.md` — fixed
  research benchmark and conservative priorities.
- `THEOREM.md`, `CERTIFICATE_THEORY.md` — transparent mathematical semantics.
- `SHA256SUMS` — repository file-integrity checks; not a publisher signature.

The old certificate schemas (identity, linear, ideal, radical, real-SOS-v1,
negative rational witness) remain independently verifiable. `run_all.py` checks
**all** certificates in the extracted release and refuses inconsistent files.

## Limits / trust

- **No theorem of historic importance has been solved.** This isn't a claim
  of mathematical novelty or research priority; equivalent SOS ideas are
  classical and already implemented in sophisticated tools.
- Independent Python verification is not formally proved: the implementation
  may contain defects. No Lean 4 kernel verification has been run here.
- The input syntax is restricted to bounded rational polynomials and equality
  premises. General inequalities, algebraic extension coefficients, difficult
  non-SOS nonnegative polynomials, and complete real algebraic geometry are
  outside the supported system.
- The domain of a real-SOS certificate is *ordered fields containing Q*;
  extending a verdict to all commutative rings or complex fields would be a
  mathematical error.
- The default 4,000-multiplier cap, powers `2/4/6/8`, 32-SOS-square cap and
  degree limits mean many true statements remain `UNKNOWN`.
- The integrity file detects accidental changes only; public access does not
  confer a license. No code license has been assigned by the owner.
- For externally supplied input, run the program with OS-level time/memory
  limits; its bounded algebra and JSON checks are not a hardened service.

## Reproducible release

Extract the ZIP into an empty folder and run `python3 run_all.py` from that
folder. A passing run verifies this implementation's supported regression
cases, not all mathematics. Every included certificate can also be checked
individually with `python3 independent_verifier.py certificates/NAME.json`.

**Published:** 2026-10-19 · **Version:** 0.9
