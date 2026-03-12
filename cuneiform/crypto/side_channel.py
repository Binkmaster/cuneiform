"""Sexagesimal timing analysis — side-channel perspective.

Analyzes whether sexagesimal representation creates timing differences
that could be exploited or that reveal structure.
"""

from __future__ import annotations

import time
from math import gcd

from cuneiform.number_theory.regularity import RegularityClass
from cuneiform.core.smooth import extract_smooth_part


class TimingAnalysis:
    """Measure timing differences in operations on regular vs irregular numbers."""

    def division_timing(self, numbers: list[int], divisor: int,
                        iterations: int = 1000) -> dict:
        """Measure division timing for regular vs irregular numbers."""
        regular = [n for n in numbers if RegularityClass(n).is_regular]
        irregular = [n for n in numbers if not RegularityClass(n).is_regular]

        def time_divisions(nums, div, iters):
            if not nums:
                return 0.0
            start = time.perf_counter()
            for _ in range(iters):
                for n in nums:
                    _ = n % div
                    _ = n // div
            elapsed = time.perf_counter() - start
            return elapsed / (len(nums) * iters)

        reg_time = time_divisions(regular, divisor, iterations)
        irreg_time = time_divisions(irregular, divisor, iterations)

        return {
            "regular_count": len(regular),
            "irregular_count": len(irregular),
            "regular_avg_ns": reg_time * 1e9,
            "irregular_avg_ns": irreg_time * 1e9,
            "ratio": irreg_time / reg_time if reg_time > 0 else 0,
        }

    def smooth_extraction_timing(self, numbers: list[int],
                                  iterations: int = 100) -> dict:
        """Measure how long smooth part extraction takes by tier."""
        tier_times: dict[int, list[float]] = {}

        for n in numbers:
            if n <= 0:
                continue
            tier = RegularityClass(n).regularity_tier
            start = time.perf_counter()
            for _ in range(iterations):
                extract_smooth_part(n)
            elapsed = (time.perf_counter() - start) / iterations

            if tier not in tier_times:
                tier_times[tier] = []
            tier_times[tier].append(elapsed)

        result = {}
        for tier, times in sorted(tier_times.items()):
            avg = sum(times) / len(times)
            result[tier] = {
                "count": len(times),
                "avg_ns": avg * 1e9,
            }

        return result
