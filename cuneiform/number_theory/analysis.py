"""Benchmarking & statistical comparison — the hypothesis-testing framework.

The core question: does sexagesimal organization improve smooth relation
finding in sieving algorithms?
"""

from __future__ import annotations

import random
import time
from math import isqrt, gcd

from .regularity import RegularityClass, regularity_spectrum
from .smoothness import is_b_smooth, is_b_smooth_sexa, SmoothBatch
from .primes import is_prime, optimal_smoothness_bound


def generate_semiprimes(bits: int, count: int, seed: int = 42) -> list[int]:
    """Generate random semiprimes (product of two primes) of given bit size."""
    rng = random.Random(seed)
    half_bits = bits // 2
    results = []

    while len(results) < count:
        p = rng.getrandbits(half_bits) | (1 << (half_bits - 1)) | 1
        q = rng.getrandbits(bits - half_bits) | (1 << (bits - half_bits - 1)) | 1
        if is_prime(p) and is_prime(q) and p != q:
            results.append(p * q)

    return results


class SmoothDensityExperiment:
    """THE KEY EXPERIMENT: smooth density by regularity tier.

    Generate QS polynomial values Q(x) = (ceil(sqrt(n)) + x)^2 - n,
    classify each by regularity tier, and measure B-smooth rates per tier.

    If lower tiers have higher smooth rates, the sexagesimal approach has signal.
    """

    def __init__(self, n: int, sieve_range: int = 5000,
                 smoothness_bound: int | None = None):
        self.n = n
        self.sieve_range = sieve_range
        self.B = smoothness_bound or optimal_smoothness_bound(n)

    def run(self) -> dict:
        """Run the smooth density experiment."""
        sqrt_n = isqrt(self.n)

        # Generate Q(x) values
        values = []
        for x in range(-self.sieve_range, self.sieve_range + 1):
            qx = (sqrt_n + x) ** 2 - self.n
            if qx != 0:
                values.append(abs(qx))

        # Classify by tier and test smoothness
        tier_total: dict[int, int] = {}
        tier_smooth: dict[int, int] = {}

        for v in values:
            rc = RegularityClass(v)
            tier = rc.regularity_tier
            tier_total[tier] = tier_total.get(tier, 0) + 1

            if is_b_smooth(v, self.B):
                tier_smooth[tier] = tier_smooth.get(tier, 0) + 1

        # Compute rates
        tier_rates = {}
        for tier in sorted(tier_total.keys()):
            total = tier_total[tier]
            smooth = tier_smooth.get(tier, 0)
            tier_rates[tier] = {
                "total": total,
                "smooth": smooth,
                "rate": smooth / total if total > 0 else 0,
            }

        # Overall stats
        total_smooth = sum(tier_smooth.values())
        overall_rate = total_smooth / len(values) if values else 0

        return {
            "n": self.n,
            "n_bits": self.n.bit_length(),
            "sieve_range": self.sieve_range,
            "smoothness_bound": self.B,
            "total_values": len(values),
            "total_smooth": total_smooth,
            "overall_smooth_rate": overall_rate,
            "tier_rates": tier_rates,
            "tier_0_rate": tier_rates.get(0, {}).get("rate", 0),
            "tier_1_rate": tier_rates.get(1, {}).get("rate", 0),
        }


class FactoringComparison:
    """Head-to-head comparison of standard vs sexagesimal QS."""

    def __init__(self, bits: int = 40, count: int = 10, seed: int = 42):
        self.bits = bits
        self.count = count
        self.seed = seed

    def run(self) -> dict:
        """Run comparison on random semiprimes."""
        from .sieve import QuadraticSieve, SexagesimalQuadraticSieve

        numbers = generate_semiprimes(self.bits, self.count, self.seed)
        std_results = []
        sexa_results = []

        for n in numbers:
            # Standard QS
            t0 = time.perf_counter()
            qs = QuadraticSieve(n)
            std_factor = qs.factor()
            t1 = time.perf_counter()
            std_results.append({
                "n": n,
                "factor": std_factor,
                "time": t1 - t0,
                "relations": qs.stats["smooth_found"],
                "evaluations": qs.stats["sieve_evaluations"],
            })

            # Sexagesimal QS
            t0 = time.perf_counter()
            sqs = SexagesimalQuadraticSieve(n)
            sexa_factor = sqs.factor()
            t1 = time.perf_counter()
            sexa_results.append({
                "n": n,
                "factor": sexa_factor,
                "time": t1 - t0,
                "relations": sqs.stats["smooth_found"],
                "evaluations": sqs.stats["sieve_evaluations"],
                "prefilter_saves": sqs.stats["prefilter_saves"],
                "smooth_by_tier": sqs.stats["smooth_by_tier"],
            })

        # Aggregate
        std_success = sum(1 for r in std_results if r["factor"] is not None)
        sexa_success = sum(1 for r in sexa_results if r["factor"] is not None)
        std_avg_time = sum(r["time"] for r in std_results) / len(std_results)
        sexa_avg_time = sum(r["time"] for r in sexa_results) / len(sexa_results)
        std_avg_relations = sum(r["relations"] for r in std_results) / len(std_results)
        sexa_avg_relations = sum(r["relations"] for r in sexa_results) / len(sexa_results)

        return {
            "bits": self.bits,
            "count": self.count,
            "standard": {
                "success_rate": std_success / len(numbers),
                "avg_time": std_avg_time,
                "avg_relations": std_avg_relations,
                "details": std_results,
            },
            "sexagesimal": {
                "success_rate": sexa_success / len(numbers),
                "avg_time": sexa_avg_time,
                "avg_relations": sexa_avg_relations,
                "total_prefilter_saves": sum(
                    r["prefilter_saves"] for r in sexa_results),
                "details": sexa_results,
            },
            "comparison": {
                "time_ratio": sexa_avg_time / std_avg_time if std_avg_time > 0 else 0,
                "relations_ratio": (sexa_avg_relations / std_avg_relations
                                    if std_avg_relations > 0 else 0),
            },
        }
