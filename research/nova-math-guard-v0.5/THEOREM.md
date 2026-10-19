# Mathematical capabilities and limitations

v0.5 retains v0.3's exact coefficient-uniqueness test for polynomial identities,
deterministic rational counterexamples to nonidentities, and one-variable
rational linear-equation solver. These are classical techniques with finite
computational cutoffs; they are not new mathematical discoveries.

v0.5 adds conditional polynomial certificates. See `CERTIFICATE_THEORY.md`
for the precise proof statement, soundness argument, algorithmic incompleteness,
logical vacuity warning, and limitations. The independent verifier remains
ordinary unverified Python software, not Lean 4 or Coq.

## Additional theorem used in v0.5

**Buchberger criterion (classical):** A finite set of generators is a Gröbner
basis if every pairwise S-polynomial reduces to zero under multivariate
polynomial division, for a fixed admissible monomial order. Algorithmic
completion adds nonzero S-polynomial remainders until this holds. By
retaining original-generator representations through every operation,
NOVA can extract exact certificates of ideal membership; each certificate
is checked by an independent algebra implementation.

The computational budget can interrupt the algorithm, leaving the result
UNKNOWN. No original mathematical theorem is claimed.
