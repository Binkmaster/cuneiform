"""Scaling analysis — does any Phase 3 signal persist at cryptographic bit sizes?

The fundamental question: does the sexagesimal advantage (if any)
scale with the size of the numbers being factored?
"""

from __future__ import annotations

import random
from math import isqrt, log, exp, sqrt

from cuneiform.number_theory.primes import is_prime, optimal_smoothness_bound
from cuneiform.number_theory.regularity import RegularityClass
from cuneiform.number_theory.smoothness import is_b_smooth
from cuneiform.number_theory.analysis import generate_semiprimes


class ScalingAnalysis:
    """Scale Phase 3 smooth density results to larger bit sizes.

    Three possible outcomes:
    A) Advantage grows with bit size -> potential asymptotic improvement
    B) Advantage is constant -> useful optimization, not paradigm shift
    C) Advantage shrinks with bit size -> the effect is an artifact
    """

    def __init__(self, bit_sizes: list[int] | None = None):
        self.bit_sizes = bit_sizes or [32, 48, 64, 80, 96, 128]
        self.results: dict[int, dict] = {}

    def smooth_density_scaling(self, trials_per_size: int = 5,
                                sieve_range: int = 2000) -> dict:
        """The critical scaling test.

        For each bit size:
        1. Generate random semiprimes
        2. Compute QS polynomial values Q(x)
        3. Classify by regularity tier
        4. Measure B-smooth rate per tier
        5. Compute ratio of smooth rates between tiers
        """
        for bits in self.bit_sizes:
            tier_stats: dict[int, dict] = {}

            semiprimes = generate_semiprimes(bits, trials_per_size)
            for n in semiprimes:
                sqrt_n = isqrt(n)
                B = optimal_smoothness_bound(n)
                M = min(sieve_range, int(B * 2))

                for x in range(-M, M + 1):
                    qx = (sqrt_n + x) ** 2 - n
                    if qx == 0:
                        continue
                    aqx = abs(qx)
                    tier = RegularityClass(aqx).regularity_tier
                    smooth = is_b_smooth(aqx, B)

                    if tier not in tier_stats:
                        tier_stats[tier] = {"smooth": 0, "total": 0}
                    tier_stats[tier]["total"] += 1
                    if smooth:
                        tier_stats[tier]["smooth"] += 1

            # Compute rates
            tier_rates = {}
            for tier, stats in sorted(tier_stats.items()):
                rate = stats["smooth"] / stats["total"] if stats["total"] > 0 else 0
                tier_rates[tier] = {
                    "smooth": stats["smooth"],
                    "total": stats["total"],
                    "rate": rate,
                }

            # Compute advantage ratio: tier 0-1 rate vs tier 2+ rate
            low_tier_smooth = sum(
                tier_stats.get(t, {}).get("smooth", 0) for t in (0, 1))
            low_tier_total = sum(
                tier_stats.get(t, {}).get("total", 0) for t in (0, 1))
            high_tier_smooth = sum(
                v["smooth"] for t, v in tier_stats.items() if t >= 2)
            high_tier_total = sum(
                v["total"] for t, v in tier_stats.items() if t >= 2)

            low_rate = low_tier_smooth / low_tier_total if low_tier_total > 0 else 0
            high_rate = high_tier_smooth / high_tier_total if high_tier_total > 0 else 0
            advantage_ratio = low_rate / high_rate if high_rate > 0 else float("inf")

            self.results[bits] = {
                "tier_rates": tier_rates,
                "low_tier_rate": low_rate,
                "high_tier_rate": high_rate,
                "advantage_ratio": advantage_ratio,
                "smoothness_bound": optimal_smoothness_bound(
                    semiprimes[0]) if semiprimes else 0,
            }

        return self.results

    def compute_scaling_exponent(self) -> dict:
        """Fit the tier advantage ratio as a function of bit size.

        Model: advantage_ratio = A * bits^alpha + C

        alpha > 0: advantage grows (extraordinary)
        alpha ~ 0: advantage is constant (good)
        alpha < 0: advantage shrinks (disappointing)

        Uses simple least-squares on log-log data.
        """
        if not self.results:
            return {"error": "Run smooth_density_scaling first"}

        points = []
        for bits, data in sorted(self.results.items()):
            ratio = data["advantage_ratio"]
            if ratio > 0 and ratio != float("inf"):
                points.append((bits, ratio))

        if len(points) < 2:
            return {"error": "Not enough data points", "points": points}

        # Log-log linear regression: log(ratio) = alpha * log(bits) + log(A)
        n = len(points)
        sum_x = sum(log(b) for b, _ in points)
        sum_y = sum(log(r) for _, r in points)
        sum_xy = sum(log(b) * log(r) for b, r in points)
        sum_x2 = sum(log(b) ** 2 for b, _ in points)

        denom = n * sum_x2 - sum_x ** 2
        if abs(denom) < 1e-15:
            return {"error": "Degenerate data", "points": points}

        alpha = (n * sum_xy - sum_x * sum_y) / denom
        log_A = (sum_y - alpha * sum_x) / n
        A = exp(log_A)

        # R-squared
        mean_y = sum_y / n
        ss_tot = sum((log(r) - mean_y) ** 2 for _, r in points)
        ss_res = sum(
            (log(r) - (alpha * log(b) + log_A)) ** 2
            for b, r in points
        )
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        return {
            "alpha": alpha,
            "A": A,
            "r_squared": r_squared,
            "interpretation": (
                "growing advantage" if alpha > 0.1
                else "constant advantage" if alpha > -0.1
                else "shrinking advantage"
            ),
            "data_points": points,
        }

    def extrapolate_to_rsa(self) -> dict:
        """Extrapolate to RSA-1024, RSA-2048, RSA-4096 bit sizes."""
        fit = self.compute_scaling_exponent()
        if "error" in fit:
            return fit

        alpha = fit["alpha"]
        A = fit["A"]

        predictions = {}
        for target_bits in [512, 1024, 2048, 4096]:
            predicted_ratio = A * (target_bits ** alpha)
            predictions[target_bits] = {
                "predicted_advantage_ratio": predicted_ratio,
                "interpretation": (
                    f"Tier 0-1 values ~{predicted_ratio:.2f}x more likely "
                    f"to be smooth than tier 2+ values at {target_bits} bits"
                ),
            }

        return {
            "scaling_fit": fit,
            "predictions": predictions,
            "caveat": (
                "Extrapolation from small bit sizes. These predictions "
                "need verification at larger sizes with more compute."
            ),
        }

    def regularity_in_sieve_region(self, n: int,
                                     sieve_radius: int = 5000) -> dict:
        """Map the regularity landscape of the sieve region.

        Look for clustering, periodicity, and correlation with x's regularity.
        """
        sqrt_n = isqrt(n)
        tier_by_x: dict[int, int] = {}
        tier_counts: dict[int, int] = {}

        for x in range(-sieve_radius, sieve_radius + 1):
            qx = (sqrt_n + x) ** 2 - n
            if qx == 0:
                continue
            tier = RegularityClass(abs(qx)).regularity_tier
            tier_by_x[x] = tier
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

        # Check for periodicity mod 60
        mod60_tier: dict[int, dict[int, int]] = {}
        for x, tier in tier_by_x.items():
            r = x % 60
            if r not in mod60_tier:
                mod60_tier[r] = {}
            mod60_tier[r][tier] = mod60_tier[r].get(tier, 0) + 1

        # Compute average tier by residue class mod 60
        avg_tier_by_residue = {}
        for r in sorted(mod60_tier):
            dist = mod60_tier[r]
            total = sum(dist.values())
            avg = sum(t * c for t, c in dist.items()) / total if total > 0 else 0
            avg_tier_by_residue[r] = round(avg, 3)

        # Find "best" residue classes (lowest average tier)
        sorted_residues = sorted(avg_tier_by_residue.items(), key=lambda x: x[1])
        best_residues = sorted_residues[:10]

        return {
            "n": n,
            "sieve_radius": sieve_radius,
            "tier_distribution": dict(sorted(tier_counts.items())),
            "avg_tier_by_residue_mod60": avg_tier_by_residue,
            "best_residues_mod60": best_residues,
            "total_values": len(tier_by_x),
        }

    def nfs_polynomial_value_distribution(self, bits: int = 64,
                                           degree: int = 3,
                                           trials: int = 3) -> dict:
        """Analyze NFS polynomial values by regularity.

        Generates degree-d polynomials with small coefficients and
        analyzes the regularity of their values across a sieve region.
        """
        rng = random.Random(42)
        tier_stats: dict[int, dict] = {}

        for _ in range(trials):
            n = generate_semiprimes(bits, 1)[0]
            # Simple polynomial: f(x) = c_d*x^d + ... + c_0
            # Coefficients chosen small for demo
            coeffs = [rng.randint(1, 100) for _ in range(degree + 1)]
            B = optimal_smoothness_bound(n)

            for a in range(1, 500):
                val = sum(c * (a ** i) for i, c in enumerate(coeffs))
                if val <= 0:
                    continue
                tier = RegularityClass(val).regularity_tier
                smooth = is_b_smooth(val, B)

                if tier not in tier_stats:
                    tier_stats[tier] = {"smooth": 0, "total": 0}
                tier_stats[tier]["total"] += 1
                if smooth:
                    tier_stats[tier]["smooth"] += 1

        tier_rates = {}
        for tier, stats in sorted(tier_stats.items()):
            rate = stats["smooth"] / stats["total"] if stats["total"] > 0 else 0
            tier_rates[tier] = {"rate": rate, **stats}

        return {
            "polynomial_degree": degree,
            "bits": bits,
            "tier_rates": tier_rates,
        }
