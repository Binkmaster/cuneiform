"""Smooth density experiment — the central hypothesis test.

Tests whether sexagesimal regularity tier predicts smooth number density
in QS polynomial values. This is THE experiment that Phase 3 was built for,
packaged here as a reproducible, self-contained runner.

Usage:
    exp = SmoothDensityExperiment(bits=64, trials=100, smoothness_bound=1000)
    results = exp.run()
    print(exp.summary(results))
"""

from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass, field, asdict
from fractions import Fraction

from cuneiform.core.smooth import extract_smooth_part, is_smooth
from cuneiform.number_theory.regularity import RegularityClass


@dataclass
class TierResult:
    """Results for a single regularity tier."""
    tier: int
    count: int = 0
    smooth_count: int = 0

    @property
    def smooth_rate(self) -> float:
        return self.smooth_count / self.count if self.count > 0 else 0.0


@dataclass
class ExperimentResult:
    """Full experiment results."""
    bits: int
    trials: int
    smoothness_bound: int
    seed: int
    elapsed_seconds: float
    tier_results: dict[int, TierResult] = field(default_factory=dict)
    total_tested: int = 0
    total_smooth: int = 0

    @property
    def overall_smooth_rate(self) -> float:
        return self.total_smooth / self.total_tested if self.total_tested > 0 else 0.0

    def to_dict(self) -> dict:
        return {
            "bits": self.bits,
            "trials": self.trials,
            "smoothness_bound": self.smoothness_bound,
            "seed": self.seed,
            "elapsed_seconds": self.elapsed_seconds,
            "total_tested": self.total_tested,
            "total_smooth": self.total_smooth,
            "overall_smooth_rate": self.overall_smooth_rate,
            "tiers": {
                str(k): {
                    "tier": v.tier,
                    "count": v.count,
                    "smooth_count": v.smooth_count,
                    "smooth_rate": v.smooth_rate,
                }
                for k, v in sorted(self.tier_results.items())
            },
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


class SmoothDensityExperiment:
    """The core experiment: does regularity tier predict smoothness?

    For each trial:
    1. Generate a random n-bit number
    2. Classify it by regularity tier
    3. Compute QS polynomial value: Q(x) = (x + floor(sqrt(n)))^2 - n
    4. Check if Q(x) is B-smooth
    5. Record (tier, smooth_or_not)

    If tier 0 (fully regular) numbers have higher smooth rates,
    the sexagesimal hypothesis has support.
    """

    def __init__(self, bits: int = 64, trials: int = 100,
                 smoothness_bound: int = 1000, seed: int | None = None):
        self.bits = bits
        self.trials = trials
        self.smoothness_bound = smoothness_bound
        self.seed = seed if seed is not None else random.randint(0, 2**32)

    def run(self) -> ExperimentResult:
        """Run the experiment. Returns structured results."""
        rng = random.Random(self.seed)
        start = time.monotonic()

        result = ExperimentResult(
            bits=self.bits,
            trials=self.trials,
            smoothness_bound=self.smoothness_bound,
            seed=self.seed,
            elapsed_seconds=0.0,
        )

        for _ in range(self.trials):
            # Generate random n-bit number
            n = rng.getrandbits(self.bits) | (1 << (self.bits - 1))  # Ensure n-bit
            if n < 4:
                n = 4

            # Classify by regularity
            rc = RegularityClass(n)
            tier = rc.regularity_tier

            # QS polynomial: Q(x) = (x + isqrt(n))^2 - n for small x
            sqrt_n = _isqrt(n)
            # Test several x values per n
            for x in range(1, 11):
                val = (x + sqrt_n) ** 2 - n
                if val <= 0:
                    continue

                result.total_tested += 1

                if tier not in result.tier_results:
                    result.tier_results[tier] = TierResult(tier=tier)
                result.tier_results[tier].count += 1

                # Check B-smoothness
                if _is_b_smooth(val, self.smoothness_bound):
                    result.total_smooth += 1
                    result.tier_results[tier].smooth_count += 1

        result.elapsed_seconds = time.monotonic() - start
        return result

    @staticmethod
    def summary(result: ExperimentResult) -> str:
        """Human-readable summary of results."""
        lines = [
            f"Smooth Density Experiment",
            f"  bits={result.bits}, trials={result.trials}, "
            f"bound={result.smoothness_bound}, seed={result.seed}",
            f"  Time: {result.elapsed_seconds:.2f}s",
            f"  Total tested: {result.total_tested}",
            f"  Overall smooth rate: {result.overall_smooth_rate:.4f}",
            f"",
            f"  By regularity tier:",
        ]
        for tier in sorted(result.tier_results.keys()):
            tr = result.tier_results[tier]
            lines.append(
                f"    Tier {tier}: {tr.count} tested, "
                f"{tr.smooth_count} smooth, "
                f"rate={tr.smooth_rate:.4f}"
            )

        # Statistical assessment
        rates = [
            tr.smooth_rate for tr in result.tier_results.values()
            if tr.count >= 10
        ]
        if len(rates) >= 2:
            spread = max(rates) - min(rates)
            if spread < 0.01:
                lines.append(f"\n  Assessment: No significant tier effect (spread={spread:.4f})")
            elif spread < 0.05:
                lines.append(f"\n  Assessment: Possible small effect (spread={spread:.4f})")
            else:
                lines.append(f"\n  Assessment: Notable tier effect (spread={spread:.4f})")
                lines.append(f"  WARNING: Verify with larger trials before drawing conclusions")

        return "\n".join(lines)


def _is_b_smooth(n: int, bound: int) -> bool:
    """Check if n is B-smooth (all prime factors <= bound)."""
    if n <= 1:
        return True
    temp = abs(n)
    d = 2
    while d <= bound and d * d <= temp:
        while temp % d == 0:
            temp //= d
        d += 1 if d == 2 else 2
    return temp == 1 or temp <= bound


def _isqrt(n: int) -> int:
    """Integer square root."""
    if n < 0:
        return 0
    if n == 0:
        return 0
    x = n
    y = (x + 1) // 2
    while y < x:
        x = y
        y = (x + n // x) // 2
    return x
