"""Runs the scalar-representation side-channel leakage experiment.

Does a base-60 / mixed-radix encoding of an ECC secret scalar leak less to a
power-analysis side channel than plain binary?  This is the one place where a
number's *representation* legitimately matters to cryptography — the hardness
of ECDLP is base-invariant, but the operation sequence a scalar multiplication
performs, and therefore what a side channel sees, is not.

Metric is exhaustive and pre-committed (see cuneiform/crypto/scalar_leakage):
residual attacker uncertainty in bits after observing one operation trace,
under a standard SPA leakage model.  Higher = safer.

    python ideas/scalar_leakage_experiment.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cuneiform.crypto.scalar_leakage import run_experiment  # noqa: E402


def main() -> None:
    n_bits = 16
    result = run_experiment(n_bits=n_bits)

    print("=" * 74)
    print("Scalar-representation side-channel leakage")
    print(f"exhaustive over all {n_bits}-bit scalars; projected to "
          f"{result['crypto_bits']}-bit key")
    print("=" * 74)
    print()
    print("Leakage model: DOUBLE distinguishable from ADD; ADD/SUB")
    print("indistinguishable; table index hidden unless noted.")
    print("Residual = attacker's leftover uncertainty (bits). Higher = safer.")
    print()

    header = f"{'scheme':<34}{'leak':>6}  {'residual':>9}  {'proj@256':>9}"
    print(header)
    print("-" * len(header))
    for row in result["schemes"]:
        print(f"{row['scheme']:<34}"
              f"{row['leak_rate'] * 100:>5.0f}%  "
              f"{row['residual_bits']:>8.1f}b  "
              f"{row['projected_residual_at_crypto']:>8.1f}b")
        print(f"    {row['note']}")
    print()

    dpa = result["dpa"]
    print("DPA axis (representation randomization vs trace averaging):")
    print(f"    fixed scheme:      {dpa['fixed_scheme_distinct_traces']} "
          f"distinct trace for a fixed secret (no protection)")
    print(f"    randomized signed: "
          f"{dpa['randomized_mean_distinct_traces']:.0f} distinct traces "
          f"(min {dpa['randomized_min_distinct_traces']}) over "
          f"{dpa['runs_per_scalar']} runs of a fixed secret")
    print()
    print("Reading the table: the base value buys nothing by itself. Binary")
    print("double-and-add and base-60-with-a-leaking-lookup both leak the")
    print("whole scalar. What lowers leakage is a generic mechanism any radix")
    print("shares (windowing hides digit values; signed-digit hides signs;")
    print("a constant op-sequence hides everything at the SPA level), and")
    print("base-60's window advantage is real only while the table lookup")
    print("does not itself leak. base-16 gets the same protection as base-60.")


if __name__ == "__main__":
    main()
