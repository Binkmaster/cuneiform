"""Rational price level detection and sexagesimal retracements.

Detects price levels where the ratio to a reference price is expressible
as a terminating sexagesimal fraction (5-smooth denominator).
"""

from __future__ import annotations

from fractions import Fraction

from cuneiform.core.smooth import is_smooth, generate_smooth_numbers
from cuneiform.core.rational import SexaRational
from cuneiform.number_theory.regularity import RegularityClass


# Standard Fibonacci retracement levels
_FIB_LEVELS = {
    Fraction(0): "0%",
    Fraction(236, 1000): "23.6%",
    Fraction(382, 1000): "38.2%",
    Fraction(1, 2): "50%",
    Fraction(618, 1000): "61.8%",
    Fraction(786, 1000): "78.6%",
    Fraction(1): "100%",
}


def _generate_smooth_ratios(max_val: int = 120) -> list[Fraction]:
    """Generate all 5-smooth ratios p/q where p,q <= max_val."""
    smooths = [s.value for s in generate_smooth_numbers(max_val)]
    ratios = set()
    for p in smooths:
        for q in smooths:
            if q > 0:
                ratios.add(Fraction(p, q))
    return sorted(ratios)


class RationalPriceLevels:
    """Detect rational price levels — prices where the ratio to a
    reference is a terminating sexagesimal fraction."""

    def __init__(self, reference_price: float):
        self.ref = reference_price

    def generate_levels(self, range_pct: float = 0.20,
                        max_smooth: int = 60) -> list[dict]:
        """Generate all rational price levels within range_pct of reference.

        Returns levels sorted by regularity (most regular first).
        """
        ratios = _generate_smooth_ratios(max_smooth)
        levels = []

        for ratio in ratios:
            r_float = float(ratio)
            if abs(r_float - 1.0) > range_pct:
                continue
            if r_float <= 0:
                continue

            price = self.ref * r_float
            nearest_fib = self._nearest_fib(r_float)

            levels.append({
                "price": round(price, 4),
                "ratio": ratio,
                "ratio_decimal": round(r_float, 6),
                "regularity_tier": 0,  # All fully regular by construction
                "sexa_notation": str(SexaRational(ratio)),
                "nearest_fib": nearest_fib,
                "fib_distance": self._fib_distance(r_float),
            })

        # Add tier-1 levels (one prime > 5)
        for p in (7, 11, 13):
            for ratio in ratios:
                r_float = float(ratio)
                for variant_f in (r_float * p, r_float / p):
                    if abs(variant_f - 1.0) > range_pct or variant_f <= 0:
                        continue
                    variant = Fraction(ratio.numerator * p, ratio.denominator) if variant_f == r_float * p else Fraction(ratio.numerator, ratio.denominator * p)
                    price = self.ref * float(variant)
                    levels.append({
                        "price": round(price, 4),
                        "ratio": variant,
                        "ratio_decimal": round(float(variant), 6),
                        "regularity_tier": 1,
                        "irregular_prime": p,
                        "nearest_fib": self._nearest_fib(float(variant)),
                        "fib_distance": self._fib_distance(float(variant)),
                    })

        levels.sort(key=lambda l: (l["regularity_tier"], abs(l["ratio_decimal"] - 1.0)))
        return levels

    def compare_with_fibonacci(self) -> dict:
        """Compare sexagesimal levels with Fibonacci retracements."""
        sexa_levels = self.generate_levels(range_pct=1.0)
        comparisons = []

        for fib_frac, fib_name in _FIB_LEVELS.items():
            fib_float = float(fib_frac)
            # Find closest sexagesimal level
            nearest = min(sexa_levels,
                         key=lambda l: abs(l["ratio_decimal"] - fib_float))
            comparisons.append({
                "fib_level": fib_name,
                "fib_value": fib_float,
                "nearest_sexa_value": nearest["ratio_decimal"],
                "distance": abs(nearest["ratio_decimal"] - fib_float),
                "sexa_notation": nearest.get("sexa_notation", ""),
            })

        return {
            "comparisons": comparisons,
            "observation": (
                "Fibonacci retracement levels are closely approximated by "
                "5-smooth rational levels, suggesting the effectiveness of "
                "Fibonacci in TA may stem from proximity to clean rational "
                "ratios rather than the golden ratio itself."
            ),
        }

    def _nearest_fib(self, ratio: float) -> str | None:
        """Find nearest standard Fibonacci level name."""
        best_name = None
        best_dist = 0.02  # threshold
        for fib_frac, name in _FIB_LEVELS.items():
            d = abs(float(fib_frac) - ratio)
            if d < best_dist:
                best_dist = d
                best_name = name
        return best_name

    def _fib_distance(self, ratio: float) -> float:
        """Distance to nearest Fibonacci level."""
        return min(abs(float(f) - ratio) for f in _FIB_LEVELS.keys())


class SexagesimalRetracements:
    """Drop-in replacement for Fibonacci retracements using 5-smooth levels."""

    def __init__(self, high: float, low: float):
        self.high = max(high, low)
        self.low = min(high, low)
        self.range = self.high - self.low

    def levels(self) -> list[dict]:
        """Generate sexagesimal retracement levels.

        Core levels from 5-smooth ratios near standard Fibonacci:
        - 1/5 = 0;12 (20.0%) — shallow retracement
        - 1/4 = 0;15 (25.0%) — close to Fib 23.6%
        - 1/3 = 0;20 (33.3%) — strong, often ignored by Fib
        - 3/8 = 0;22,30 (37.5%) — close to Fib 38.2%
        - 1/2 = 0;30 (50.0%) — identical to Fib
        - 5/8 = 0;37,30 (62.5%) — close to Fib 61.8%
        - 2/3 = 0;40 (66.7%) — strong, between Fib levels
        - 3/4 = 0;45 (75.0%) — close to Fib 78.6%
        - 4/5 = 0;48 (80.0%) — deep retracement
        - 5/6 = 0;50 (83.3%) — level Fib doesn't have
        """
        retracement_ratios = [
            (Fraction(1, 6), "1/6 = 0;10"),
            (Fraction(1, 5), "1/5 = 0;12"),
            (Fraction(1, 4), "1/4 = 0;15"),
            (Fraction(1, 3), "1/3 = 0;20"),
            (Fraction(3, 8), "3/8 = 0;22,30"),
            (Fraction(2, 5), "2/5 = 0;24"),
            (Fraction(1, 2), "1/2 = 0;30"),
            (Fraction(3, 5), "3/5 = 0;36"),
            (Fraction(5, 8), "5/8 = 0;37,30"),
            (Fraction(2, 3), "2/3 = 0;40"),
            (Fraction(3, 4), "3/4 = 0;45"),
            (Fraction(4, 5), "4/5 = 0;48"),
            (Fraction(5, 6), "5/6 = 0;50"),
        ]

        result = []
        for ratio, label in retracement_ratios:
            price = self.low + self.range * float(ratio)
            nearest_fib = None
            for fib_frac, fib_name in _FIB_LEVELS.items():
                if abs(float(fib_frac) - float(ratio)) < 0.02:
                    nearest_fib = fib_name
                    break

            result.append({
                "ratio": ratio,
                "label": label,
                "price": round(price, 4),
                "pct": round(float(ratio) * 100, 1),
                "nearest_fib": nearest_fib,
                "is_regular": True,  # All 5-smooth by construction
            })

        return result

    def fibonacci_levels(self) -> list[dict]:
        """Standard Fibonacci levels for comparison."""
        fib_ratios = [
            (0.236, "23.6%"), (0.382, "38.2%"), (0.500, "50%"),
            (0.618, "61.8%"), (0.786, "78.6%"),
        ]
        return [
            {"ratio": r, "label": name,
             "price": round(self.low + self.range * r, 4)}
            for r, name in fib_ratios
        ]
