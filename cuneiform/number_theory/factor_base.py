"""Factor base construction — standard and sexagesimal-tiered."""

from __future__ import annotations

from math import gcd

from .primes import sieve_of_eratosthenes, legendre_symbol, optimal_smoothness_bound
from .reciprocals import ModularReciprocalPair


class StandardFactorBase:
    """Standard factor base: primes p <= B where n is a QR mod p."""

    def __init__(self, n: int, bound: int | None = None):
        self.n = n
        self.B = bound or optimal_smoothness_bound(n)
        self.primes: list[int] = []
        self._build()

    def _build(self):
        self.primes = [-1]  # -1 handles sign
        for p in sieve_of_eratosthenes(self.B):
            if p == 2 or legendre_symbol(self.n, p) >= 0:
                self.primes.append(p)

    def size(self) -> int:
        return len(self.primes)


class SexagesimalFactorBase:
    """Factor base organized by sexagesimal regularity tiers.

    Same primes as standard, but ordered:
    1. Regular primes: 2, 3, 5
    2. Tier 1: primes ≡ ±1 (mod 60)
    3. Tier 2: other primes coprime to 60
    """

    def __init__(self, n: int, bound: int | None = None):
        self.n = n
        self.B = bound or optimal_smoothness_bound(n)
        self.regular_primes = [2, 3, 5]
        self.tier_1_primes: list[int] = []
        self.tier_2_primes: list[int] = []
        self._build()

    def _build(self):
        all_primes = sieve_of_eratosthenes(self.B)
        for p in all_primes:
            if p <= 5:
                continue
            if p != 2 and legendre_symbol(self.n, p) == -1:
                continue
            r = p % 60
            if r in (1, 59):
                self.tier_1_primes.append(p)
            else:
                self.tier_2_primes.append(p)

    def all_primes(self) -> list[int]:
        """All primes ordered by tier."""
        return self.regular_primes + self.tier_1_primes + self.tier_2_primes

    def all_primes_with_sign(self) -> list[int]:
        """Include -1 for sign handling."""
        return [-1] + self.all_primes()

    def size(self) -> int:
        return len(self.regular_primes) + len(self.tier_1_primes) + len(self.tier_2_primes)

    def tier_analysis(self) -> dict:
        total = self.size()
        return {
            "regular": len(self.regular_primes),
            "tier_1": len(self.tier_1_primes),
            "tier_2": len(self.tier_2_primes),
            "total": total,
            "tier_1_fraction": len(self.tier_1_primes) / total if total else 0,
        }


def compare_factor_bases(n: int, bound: int | None = None) -> dict:
    """Compare standard vs sexagesimal factor bases."""
    std = StandardFactorBase(n, bound)
    sexa = SexagesimalFactorBase(n, bound)
    std_set = set(std.primes) - {-1}
    sexa_set = set(sexa.all_primes())
    return {
        "standard_size": std.size(),
        "sexa_size": sexa.size(),
        "same_primes": std_set == sexa_set,
        "standard_primes": sorted(std_set),
        "tier_analysis": sexa.tier_analysis(),
    }
