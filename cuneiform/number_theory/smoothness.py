"""Smooth number detection — standard and sexagesimal-aware.

Smoothness detection is THE bottleneck in all sieving algorithms.
CUNEIFORM's approach: extract the 5-smooth part first, then classify
the cofactor.
"""

from __future__ import annotations

from cuneiform.core.smooth import extract_smooth_part
from .primes import sieve_of_eratosthenes
from .regularity import RegularityClass


def is_b_smooth(n: int, bound: int) -> bool:
    """Standard B-smoothness test. Is every prime factor of |n| <= bound?"""
    if n == 0:
        return False
    temp = abs(n)
    d = 2
    while d <= bound and d * d <= temp:
        while temp % d == 0:
            temp //= d
        d += 1 if d == 2 else 2
    return temp <= bound


def is_b_smooth_sexa(n: int, bound: int) -> tuple[bool, dict]:
    """Sexagesimal-aware smoothness test.

    Extracts the 5-smooth part first, then tests the cofactor.
    Returns (is_smooth, metadata).
    """
    if n == 0:
        return False, {"regular_part": 0, "cofactor": 0, "divisions": 0}

    temp = abs(n)
    divisions = 0
    reg = 1

    # Phase 1: Extract full 5-smooth part (very fast)
    for p in (2, 3, 5):
        while temp % p == 0:
            temp //= p
            reg *= p
            divisions += 1

    if temp == 1:
        return True, {
            "regular_part": reg,
            "cofactor": 1,
            "cofactor_factors": [],
            "regularity_tier": 0,
            "divisions": divisions,
        }

    # Phase 2: Factor cofactor against primes 7..bound
    cofactor_factors = []
    d = 7
    while d <= bound and d * d <= temp:
        while temp % d == 0:
            temp //= d
            cofactor_factors.append(d)
            divisions += 1
        # Skip even numbers and multiples of 3/5 (cofactor is coprime to 30)
        d += _next_coprime_step(d)

    smooth = True
    if temp > 1:
        if temp <= bound:
            cofactor_factors.append(temp)
        else:
            smooth = False

    return smooth, {
        "regular_part": reg,
        "cofactor": abs(n) // reg,
        "cofactor_factors": cofactor_factors,
        "regularity_tier": RegularityClass(abs(n)).regularity_tier if n != 0 else 0,
        "divisions": divisions,
    }


def _next_coprime_step(d: int) -> int:
    """Step to next integer coprime to 30 (= 2*3*5).

    The residues coprime to 30 in [1,30] are: 1,7,11,13,17,19,23,29.
    Steps between consecutive: 6,4,2,4,2,4,6,2 (repeating).
    """
    # Simple approach: just step by 2 and skip multiples of 3 and 5
    nd = d + 2
    while nd % 3 == 0 or nd % 5 == 0:
        nd += 2
    return nd - d


# Precomputed wheel for stepping through numbers coprime to 30
_WHEEL30 = [4, 2, 4, 2, 4, 6, 2, 6]  # Gaps between successive coprimes to 30


def primes_coprime_to_60(bound: int) -> list[int]:
    """Primes > 5 up to bound, ordered naturally.

    These are exactly the primes in residue classes coprime to 60.
    """
    return [p for p in sieve_of_eratosthenes(bound) if p > 5]


def primes_by_residue_class_60(bound: int) -> list[int]:
    """Primes up to bound, ordered by proximity to multiples of 60.

    Tier 1: primes ≡ ±1 (mod 60) — 59, 61, 119, 121, ...
    Tier 2: other primes coprime to 60
    """
    all_primes = sieve_of_eratosthenes(bound)
    tier1 = []
    tier2 = []

    for p in all_primes:
        if p <= 5:
            continue
        r = p % 60
        if r in (1, 59):
            tier1.append(p)
        else:
            tier2.append(p)

    return tier1 + tier2


class SmoothBatch:
    """Batch smooth detection with sexagesimal preprocessing.

    Classifies values by regularity tier first, then tests tier-by-tier.
    Tier-0 values are immediately smooth. Tier-1 need one primality test.
    """

    def __init__(self, values: list[int], bound: int):
        self.values = values
        self.bound = bound

    def process(self) -> dict:
        """Process all values with sexagesimal preprocessing."""
        smooth_values = []
        tier_dist = {}
        smooth_by_tier = {}
        total_divisions = 0
        prefilter_saves = 0

        for v in self.values:
            if v == 0:
                continue
            av = abs(v)
            rc = RegularityClass(av)
            tier = rc.regularity_tier
            tier_dist[tier] = tier_dist.get(tier, 0) + 1

            if rc.is_regular:
                # Tier 0: automatically smooth
                smooth_values.append(v)
                smooth_by_tier[0] = smooth_by_tier.get(0, 0) + 1
                prefilter_saves += 1
                continue

            # For higher tiers, test the cofactor
            is_smooth, meta = is_b_smooth_sexa(av, self.bound)
            total_divisions += meta["divisions"]
            if is_smooth:
                smooth_values.append(v)
                smooth_by_tier[tier] = smooth_by_tier.get(tier, 0) + 1

        return {
            "smooth_values": smooth_values,
            "smooth_count": len(smooth_values),
            "total_count": len(self.values),
            "smooth_rate": len(smooth_values) / len(self.values) if self.values else 0,
            "tier_distribution": dict(sorted(tier_dist.items())),
            "smooth_by_tier": dict(sorted(smooth_by_tier.items())),
            "total_divisions": total_divisions,
            "prefilter_saves": prefilter_saves,
        }

    def compare_with_standard(self) -> dict:
        """Compare sexagesimal vs standard smooth detection."""
        # Standard
        std_divisions = 0
        std_smooth = 0
        for v in self.values:
            if v == 0:
                continue
            av = abs(v)
            # Count divisions for standard approach
            temp = av
            divs = 0
            d = 2
            while d <= self.bound and d * d <= temp:
                while temp % d == 0:
                    temp //= d
                    divs += 1
                d += 1 if d == 2 else 2
            if temp <= self.bound:
                std_smooth += 1
            std_divisions += divs

        # Sexagesimal
        sexa_result = self.process()

        return {
            "standard_smooth": std_smooth,
            "sexa_smooth": sexa_result["smooth_count"],
            "standard_divisions": std_divisions,
            "sexa_divisions": sexa_result["total_divisions"],
            "division_ratio": (sexa_result["total_divisions"] / std_divisions
                               if std_divisions > 0 else 0),
            "prefilter_saves": sexa_result["prefilter_saves"],
        }
