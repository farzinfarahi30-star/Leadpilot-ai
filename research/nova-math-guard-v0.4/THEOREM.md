# Mathematical capabilities and limitations

v0.4 retains v0.3's exact coefficient-uniqueness test for polynomial identities,
deterministic rational counterexamples to nonidentities, and one-variable
rational linear-equation solver. These are classical techniques with finite
computational cutoffs; they are not new mathematical discoveries.

v0.4 adds conditional polynomial certificates. See `CERTIFICATE_THEORY.md`
for the precise proof statement, soundness argument, algorithmic incompleteness,
logical vacuity warning, and limitations. The independent verifier remains
ordinary unverified Python software, not Lean 4 or Coq.
