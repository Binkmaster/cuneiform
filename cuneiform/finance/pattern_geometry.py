"""Pattern detection using rational trigonometry.

The checkmark pattern (morning dip-and-recovery) analyzed with exact
rational geometry — quadrance for magnitude, spread for sharpness.
"""

from __future__ import annotations

from fractions import Fraction

from cuneiform.geometry.point import RatPoint
from cuneiform.geometry.quadrance import Quadrance
from cuneiform.geometry.spread import Spread


class RationalCheckmark:
    """Checkmark pattern detection using rational geometry.

    Models the first N minutes of trading as three points:
    A = (0, open), B = (t_low, low), C = (N, close)

    Computes quadrance (dip/recovery magnitude) and spread
    (sharpness of the reversal) using exact rational arithmetic.
    """

    def detect(self, candles: list[dict],
               time_window: int = 30) -> dict:
        """Detect checkmark pattern in candle data.

        candles: list of {"open": float, "high": float, "low": float, "close": float}
        time_window: number of candles to analyze
        """
        if len(candles) < 3:
            return {"detected": False, "reason": "insufficient data"}

        subset = candles[:time_window]
        open_price = subset[0]["open"]

        # Find the low point
        low_idx = min(range(len(subset)), key=lambda i: subset[i]["low"])
        low_price = subset[low_idx]["low"]
        close_price = subset[-1]["close"]

        # Need a dip followed by recovery
        if low_idx == 0 or low_idx >= len(subset) - 1:
            return {"detected": False, "reason": "no dip pattern"}

        if close_price <= low_price:
            return {"detected": False, "reason": "no recovery"}

        # Model as three rational points (scale to avoid floats)
        scale = 10000
        A = RatPoint(Fraction(0), Fraction(int(open_price * scale)))
        B = RatPoint(Fraction(low_idx), Fraction(int(low_price * scale)))
        C = RatPoint(Fraction(len(subset) - 1), Fraction(int(close_price * scale)))

        # Compute quadrances
        q_dip = Quadrance.between(A, B)       # Dip magnitude
        q_recovery = Quadrance.between(B, C)   # Recovery magnitude
        q_total = Quadrance.between(A, C)      # Net move

        # Compute spread at B (sharpness of reversal)
        # Spread = 1 - (Q_AC / (Q_AB * Q_BC))... use the from_sides formula
        spread_B = Spread.from_sides(q_dip, q_recovery, q_total)

        # Classify pattern
        dip_pct = (open_price - low_price) / open_price if open_price > 0 else 0
        recovery_pct = (close_price - low_price) / low_price if low_price > 0 else 0
        spread_float = float(spread_B.value) if spread_B.value is not None else 0

        if spread_float > 0.5:
            shape = "sharp_V"
        elif spread_float > 0.2:
            shape = "moderate_V"
        else:
            shape = "soft_U"

        # Symmetry: ratio of dip quadrance to recovery quadrance
        symmetry = float(q_dip.value / q_recovery.value) if q_recovery.value > 0 else 0

        return {
            "detected": True,
            "shape": shape,
            "dip_pct": round(dip_pct, 4),
            "recovery_pct": round(recovery_pct, 4),
            "dip_quadrance": q_dip.value,
            "recovery_quadrance": q_recovery.value,
            "spread_at_dip": spread_B.value,
            "spread_float": round(spread_float, 6),
            "symmetry_ratio": round(symmetry, 4),
            "low_index": low_idx,
            "time_window": time_window,
        }
