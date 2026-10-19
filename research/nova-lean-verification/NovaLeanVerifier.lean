import Lean

namespace NovaLeanVerifier

theorem square_sum_not_three_mod_four :
    ∀ x y : Fin 4, (x.val * x.val + y.val * y.val) % 4 ≠ 3 := by
  decide

#print axioms square_sum_not_three_mod_four

end NovaLeanVerifier
