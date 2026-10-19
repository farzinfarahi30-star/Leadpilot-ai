# NOVA's backward strategy: aim for consequential discoveries, not version numbers

## Goal (long term, NOT achieved)

A **new mathematical result** that is independently checked, genuinely not already in
published work, and relevant to an important unresolved problem. A benchmark pass, a
new certificate type, or a new GitHub release does not qualify.

## Work backward from that goal

1. **Public, precise target.** Select a genuinely open question in polynomial
   optimization / real algebraic geometry, with a dated literature record and
   a small, reproducible subproblem. We have **not yet selected a claim that
   survives a rigorous novelty audit**. Do not invent one.
2. **Independent acceptance criterion.** Formalize the exact statement (including
   whether it is about rational, real, complex, or ordered-field solutions).
   Design an independent checker *before* searching for a proof.
3. **Necessary computational capability.** We need rational/field algebra,
   inequalities, exact SOS witnesses, countermodels, and ideally Lean-kernel
   verification. The v0.8 addition addresses a small part of the SOS layer.
4. **Adversarial testing.** Intentionally corrupt witnesses, vary domains,
   inspect counterexamples, run seeded randomized cases, and cross-check against
   different mathematical software. UNKNOWN stays UNKNOWN.
5. **Literature and human review gate.** Search academic papers and existing
   formal proof libraries; collect independent researcher feedback. Register
   priority claims only after a proof and real novelty investigation.

## Immediate result: meaningful missing capability in v0.7

v0.7 could prove x^2=0 -> x=0 over fields, but not the valid **real-only**
implication x^2+y^2=0 -> x=0. It is FALSE over C: take x=i, y=1.

v0.8 constructs exactly this known certificate, using h=x^2+y^2 and t=x:

    t^2 + y^2 = h.

Under h=0 at a point in any ordered field containing Q, both squares are
nonnegative. Their sum being zero forces t=0. More generally the verifier
accepts only identities

    t^2 + sum_j positive_rational_weight_j * (s_j)^2
          = sum_i (q_i) * (h_i)

with exact rational polynomial q_i,s_j. The independent checker enforces
strictly positive rational weights and *exactly recomputes* the identity.
This is a **known Positivstellensatz-style proof mechanism**, not a new theorem.

The v0.8 generator only tries finite, small constant multiplier combinations
and recognizes some positive-semidefinite quadratic residuals using one fixed
rational Gram matrix. It is incomplete even on some SOS polynomials. Failure
is UNKNOWN, not FALSE. It is neither an optimization solver nor a proof of
Lean/Coq-level kernel soundness.

## Nearby research and novelty warnings (checked 2026-10-19)

- Existing Lean SOS certifier: https://github.com/leanprover/sos
- 2026 work integrating polynomial proof search and Lean 4:
  https://arxiv.org/abs/2604.13514
- 2026 SOS-to-Lean neuro-symbolic technique:
  https://arxiv.org/abs/2605.15445
- Background on real Nullstellensatz / SOS methods:
  https://math.berkeley.edu/~bernd/cbms.pdf

These examples mean we must **not** advertise a software-first SOS pipeline as
unprecedented. The present goal is reliable, small-scale experiments and
measurable capability gaps, not promotional novelty claims.

## Actual next gates

- Produce a Lean 4 proof that directly checks generated real-SOS certificates
  in an actual `lake build` run; Lean is **not installed** in this environment.
- Form a public test set from published open benchmark questions with citations,
  including negative controls that cannot be decided by this solver.
- Acquire an independently reviewed, genuinely new candidate before submitting
  any mathematical discovery paper or claiming priority.

## Update on 2026-10-19: v0.9 benchmark, no discovery claim

- v0.8 verdict for `x^4+y^4=0 -> x=0` over ordered fields: `UNKNOWN`.
- v0.9 constructs and verifies a real-SOS power-4 certificate for this exact
  known inference, plus power-6 and power-8 examples.
- A test with `x^10+y^10=0 -> x=0` remains `UNKNOWN` because the fixed proof
  powers end at 8. This is an honest limitation, not evidence of falsity.
- `x^4-y^4=0 -> x=0` is `DISPROVED` by an exact rational counterexample.

### External comparison / novelty gate

Lean's existing SOS tactic already tackles more complex problems, including
Motzkin-polynomial nonnegativity with optional Positivstellensatz powers:
https://github.com/leanprover/sos

Existing automated polynomial reasoning and Lean 4 proof-certificate work:
https://arxiv.org/abs/2604.13514

Our v0.9 technique is an elementary bounded implementation, not a claim to
surpass those systems. Before any announcement of an original discovery,
we would require a precisely stated genuinely open conjecture, a verified
certificate/proof, independent replication, and a documented literature
novelty search. The next benchmark should explicitly include inequalities
and non-SOS examples (e.g., Motzkin) **as unsupported/UNKNOWN**, to quantify
the gap rather than imply they are solved.
