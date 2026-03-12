"""Post-quantum crypto analysis through the sexagesimal lens.

Analyzes NIST PQC standard parameters (ML-KEM/Kyber, Falcon/FN-DSA,
Dilithium/ML-DSA) for sexagesimal regularity properties.
"""

from __future__ import annotations

from math import gcd

from cuneiform.number_theory.regularity import RegularityClass
from cuneiform.core.smooth import extract_smooth_part


# NIST PQC standard parameters
PQC_PARAMS = {
    "ML-KEM-512": {"q": 3329, "n": 256, "k": 2, "eta1": 3, "eta2": 2},
    "ML-KEM-768": {"q": 3329, "n": 256, "k": 3, "eta1": 2, "eta2": 2},
    "ML-KEM-1024": {"q": 3329, "n": 256, "k": 4, "eta1": 2, "eta2": 2},
    "Falcon-512": {"q": 12289, "n": 512},
    "Falcon-1024": {"q": 12289, "n": 1024},
    "Dilithium2": {"q": 8380417, "n": 256, "k": 4, "l": 4},
    "Dilithium3": {"q": 8380417, "n": 256, "k": 6, "l": 5},
    "Dilithium5": {"q": 8380417, "n": 256, "k": 8, "l": 7},
}


class PostQuantumRegularityAnalysis:
    """Analyze post-quantum cryptographic schemes through regularity."""

    def parameter_regularity_survey(self) -> dict:
        """Survey all NIST PQC standard parameters for regularity.

        For each scheme: modulus q, polynomial degree n, and derived
        constants — their regularity class, distance to regular numbers,
        and mod-60 residue.
        """
        results = {}
        for name, params in PQC_PARAMS.items():
            q = params["q"]
            n = params["n"]

            rc_q = RegularityClass(q)
            rc_n = RegularityClass(n)
            smooth_part_q, cofactor_q = extract_smooth_part(q)

            entry = {
                "q": q,
                "q_mod_60": q % 60,
                "q_tier": rc_q.regularity_tier,
                "q_smooth_part": smooth_part_q,
                "q_cofactor": cofactor_q,
                "q_smooth_fraction": smooth_part_q / q,
                "n": n,
                "n_mod_60": n % 60,
                "n_tier": rc_n.regularity_tier,
                "n_is_regular": rc_n.is_regular,
            }

            # q-1 analysis (relevant for NTT roots of unity)
            q_minus_1 = q - 1
            rc_qm1 = RegularityClass(q_minus_1)
            entry["q_minus_1"] = q_minus_1
            entry["q_minus_1_tier"] = rc_qm1.regularity_tier
            entry["q_minus_1_smooth_part"] = rc_qm1.regular_part
            entry["q_minus_1_smooth_fraction"] = rc_qm1.regular_part / q_minus_1

            # Additional parameters
            if "k" in params:
                entry["k"] = params["k"]
            if "eta1" in params:
                entry["eta1"] = params["eta1"]
                entry["eta2"] = params["eta2"]

            results[name] = entry

        return results

    def ring_structure_analysis(self, q: int = 3329, n: int = 256) -> dict:
        """Analyze R_q = Z_q[x]/(x^n + 1) from a sexagesimal perspective.

        The roots of x^n + 1 mod q are the 2n-th roots of unity.
        Analyze their residue classes mod 60.
        """
        # Find primitive 2n-th root of unity mod q
        roots = []
        for g in range(2, q):
            if pow(g, 2 * n, q) == 1 and pow(g, n, q) != 1:
                # g is a primitive 2n-th root
                root = g
                for i in range(2 * n):
                    r = pow(root, i, q)
                    if pow(r, n, q) == q - 1:  # r^n ≡ -1 mod q
                        roots.append(r)
                break

        if not roots:
            return {"q": q, "n": n, "roots_found": 0, "note": "No roots found"}

        # Classify roots by regularity
        root_tiers: dict[int, int] = {}
        root_mod60: dict[int, int] = {}
        for r in roots:
            tier = RegularityClass(r).regularity_tier
            root_tiers[tier] = root_tiers.get(tier, 0) + 1
            m = r % 60
            root_mod60[m] = root_mod60.get(m, 0) + 1

        return {
            "q": q,
            "n": n,
            "roots_found": len(roots),
            "root_tier_distribution": dict(sorted(root_tiers.items())),
            "root_mod60_distribution": dict(sorted(root_mod60.items())),
            "regular_roots_fraction": root_tiers.get(0, 0) / len(roots) if roots else 0,
        }

    def kyber_specific_analysis(self) -> dict:
        """Kyber/ML-KEM specific analysis.

        Kyber uses q = 3329, which factors as 3329 = prime.
        3329 mod 60 = 29 (near-regular residue class).
        3328 = 3329 - 1 = 2^8 * 13 → smooth_part = 256, cofactor = 13.
        """
        q = 3329
        n = 256

        # NTT compatibility: q ≡ 1 mod 2n?
        ntt_compatible = (q - 1) % (2 * n) == 0

        # Analyze the structure of Z_q*
        rc_q = RegularityClass(q)
        rc_qm1 = RegularityClass(q - 1)

        # Powers of 2 in q-1
        qm1 = q - 1
        two_power = 0
        temp = qm1
        while temp % 2 == 0:
            temp //= 2
            two_power += 1

        return {
            "q": q,
            "q_mod_60": q % 60,
            "q_tier": rc_q.regularity_tier,
            "q_minus_1": qm1,
            "q_minus_1_factored": f"2^{two_power} * {temp}",
            "q_minus_1_smooth_part": rc_qm1.regular_part,
            "q_minus_1_tier": rc_qm1.regularity_tier,
            "ntt_compatible_256": ntt_compatible,
            "n_is_power_of_2": n & (n - 1) == 0,
            "n_is_regular": RegularityClass(n).is_regular,
            "observation": (
                f"q-1 = {qm1} = 2^{two_power} × {temp}. "
                f"The 5-smooth part of q-1 is {rc_qm1.regular_part}, "
                f"giving a smooth fraction of {rc_qm1.regular_part / qm1:.4f}. "
                f"NTT uses 2n={2*n}-th roots, requiring (q-1) divisible by {2*n}: "
                f"{'Yes' if ntt_compatible else 'No'}."
            ),
        }

    def falcon_specific_analysis(self) -> dict:
        """Falcon/FN-DSA specific analysis.

        Falcon uses q = 12289, n = 512 or 1024.
        12289 mod 60 = 49.
        12288 = 12289 - 1 = 2^12 * 3 = 12288 → 5-smooth!
        """
        q = 12289
        rc_q = RegularityClass(q)
        rc_qm1 = RegularityClass(q - 1)

        return {
            "q": q,
            "q_mod_60": q % 60,
            "q_tier": rc_q.regularity_tier,
            "q_minus_1": q - 1,
            "q_minus_1_tier": rc_qm1.regularity_tier,
            "q_minus_1_is_regular": rc_qm1.is_regular,
            "q_minus_1_smooth_exponents": rc_qm1.smooth_exponents,
            "observation": (
                f"q-1 = {q - 1} is {'5-smooth (regular)' if rc_qm1.is_regular else 'not regular'}! "
                f"Smooth exponents: 2^{rc_qm1.smooth_exponents[0]} * "
                f"3^{rc_qm1.smooth_exponents[1]} * 5^{rc_qm1.smooth_exponents[2]}. "
                f"This means ALL roots of unity in Z_q have order dividing a 5-smooth number. "
                f"The NTT arithmetic is entirely within the 'regular' domain."
            ),
        }

    def dilithium_specific_analysis(self) -> dict:
        """Dilithium/ML-DSA specific analysis.

        q = 8380417. q mod 60 = 17. q-1 = 8380416 = 2^23 * 3 * ... hmm.
        """
        q = 8380417
        rc_q = RegularityClass(q)
        rc_qm1 = RegularityClass(q - 1)

        # Factor q-1
        qm1 = q - 1
        temp = qm1
        factors = {}
        for p in (2, 3, 5):
            while temp % p == 0:
                temp //= p
                factors[p] = factors.get(p, 0) + 1

        return {
            "q": q,
            "q_mod_60": q % 60,
            "q_tier": rc_q.regularity_tier,
            "q_minus_1": qm1,
            "q_minus_1_tier": rc_qm1.regularity_tier,
            "q_minus_1_smooth_part": rc_qm1.regular_part,
            "q_minus_1_cofactor": rc_qm1.cofactor,
            "q_minus_1_smooth_exponents": rc_qm1.smooth_exponents,
            "observation": (
                f"q-1 = {qm1}, smooth part = {rc_qm1.regular_part}, "
                f"cofactor = {rc_qm1.cofactor}. "
                f"Smooth fraction = {rc_qm1.regular_part / qm1:.6f}."
            ),
        }

    def full_survey(self) -> dict:
        """Run all analyses."""
        return {
            "parameter_survey": self.parameter_regularity_survey(),
            "kyber": self.kyber_specific_analysis(),
            "falcon": self.falcon_specific_analysis(),
            "dilithium": self.dilithium_specific_analysis(),
        }
