"""Support/resistance detection using regularity analysis.

Identifies price levels where price repeatedly reverses, weighted
by the regularity of the level's ratio to key reference prices.
"""

from __future__ import annotations

from fractions import Fraction
from collections import defaultdict

from cuneiform.number_theory.regularity import RegularityClass


class RationalSupportResistance:
    """S/R detection with regularity weighting."""

    def __init__(self, prices: list[float], volumes: list[float] | None = None):
        self.prices = prices
        self.volumes = volumes or [1.0] * len(prices)

    def detect_levels(self, num_levels: int = 10,
                      bin_pct: float = 0.005) -> list[dict]:
        """Detect S/R levels using price clustering + regularity.

        Groups prices into bins, counts touches per bin, then
        weights each bin by the regularity of its ratio to the
        high and low of the series.
        """
        if not self.prices:
            return []

        high = max(self.prices)
        low = min(self.prices)
        price_range = high - low
        if price_range == 0:
            return []

        bin_size = price_range * bin_pct
        bins: dict[int, dict] = defaultdict(lambda: {"count": 0, "volume": 0.0})

        for i, p in enumerate(self.prices):
            bin_idx = int((p - low) / bin_size) if bin_size > 0 else 0
            bins[bin_idx]["count"] += 1
            bins[bin_idx]["volume"] += self.volumes[i]

        # Score each bin
        scored = []
        for bin_idx, data in bins.items():
            price = low + (bin_idx + 0.5) * bin_size
            if price <= 0:
                continue

            # Regularity of ratio to high/low
            ratio_to_high = price / high
            ratio_to_low = price / low if low > 0 else 0

            # Approximate as fraction and check regularity
            frac_high = Fraction(price).limit_denominator(1000) / Fraction(high).limit_denominator(1000)
            reg_score = self._regularity_score(frac_high)

            touch_score = data["count"] / len(self.prices)
            vol_score = data["volume"] / sum(self.volumes) if sum(self.volumes) > 0 else 0

            total_score = touch_score * 0.4 + vol_score * 0.3 + reg_score * 0.3

            scored.append({
                "price": round(price, 4),
                "touch_count": data["count"],
                "volume": round(data["volume"], 2),
                "regularity_score": round(reg_score, 4),
                "total_score": round(total_score, 6),
                "ratio_to_high": round(ratio_to_high, 4),
            })

        scored.sort(key=lambda x: x["total_score"], reverse=True)
        return scored[:num_levels]

    def _regularity_score(self, frac: Fraction) -> float:
        """Score a fraction by how regular its denominator is.

        Score is 1.0 for tier-0 (regular), decaying with higher tiers.
        """
        if frac.denominator <= 0:
            return 0.0
        try:
            rc = RegularityClass(frac.denominator)
            tier = rc.regularity_tier
            return 1.0 / (1 + tier)
        except (ValueError, OverflowError):
            return 0.0
