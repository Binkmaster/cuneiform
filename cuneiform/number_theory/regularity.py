"""Regularity classification engine.

Every positive integer n decomposes uniquely as n = regular_part * cofactor
where regular_part is the largest 5-smooth divisor. The regularity tier
is determined by the number of prime factors in the cofactor.
"""

from __future__ import annotations

from cuneiform.core.smooth import extract_smooth_part, smooth_exponents
from .primes import largest_prime_factor, count_prime_factors, is_prime


def _count_prime_factors_bounded(n: int, trial_limit: int = 1_000_000) -> int:
    """Count prime factors using trial division up to a limit.

    For the remaining cofactor, if it's prime (Miller-Rabin) count as 1,
    otherwise estimate based on bit size.
    """
    count = 0
    d = 2
    while d <= trial_limit and d * d <= n:
        while n % d == 0:
            count += 1
            n //= d
        d += 1 if d == 2 else 2
    if n == 1:
        return count
    if is_prime(n):
        return count + 1
    # n is composite but too large to factor; estimate Omega(n) ~ log2(n)/avg_prime_bits
    # Conservative: at least 2 factors
    return count + max(2, n.bit_length() // 30)


class RegularityClass:
    """Classifies an integer by its 'distance' from being 5-smooth.

    Tier 0 (Regular):     cofactor = 1 (number IS 5-smooth)
    Tier 1 (Near-regular): cofactor is prime
    Tier 2:               cofactor is semiprime
    Tier k:               cofactor has k prime factors (with multiplicity)
    """

    __slots__ = ("n", "regular_part", "cofactor")

    def __init__(self, n: int):
        if n <= 0:
            raise ValueError(f"RegularityClass requires positive integer, got {n}")
        self.n = n
        self.regular_part, self.cofactor = extract_smooth_part(n)

    @property
    def is_regular(self) -> bool:
        return self.cofactor == 1

    @property
    def regularity_tier(self) -> int:
        """Number of prime factors in cofactor (with multiplicity).

        For very large cofactors (> 2^64), uses a partial factorization
        with small primes and estimates the remaining tier.
        """
        if self.cofactor == 1:
            return 0
        if self.cofactor.bit_length() <= 64:
            return count_prime_factors(self.cofactor)
        # Large cofactor: count small prime factors, estimate rest
        return _count_prime_factors_bounded(self.cofactor)

    @property
    def largest_prime(self) -> int:
        """Largest prime factor of n."""
        if self.cofactor == 1:
            if self.n == 1:
                return 1
            # Only factors 2, 3, 5
            temp = self.n
            lpf = 1
            for p in (2, 3, 5):
                if temp % p == 0:
                    lpf = p
                while temp % p == 0:
                    temp //= p
            return lpf
        if self.cofactor.bit_length() <= 64:
            return largest_prime_factor(self.cofactor)
        # For large cofactors, try small factors first
        temp = self.cofactor
        largest = 1
        d = 2
        while d <= 1_000_000 and d * d <= temp:
            while temp % d == 0:
                largest = d
                temp //= d
            d += 1 if d == 2 else 2
        if temp > 1:
            largest = temp  # remaining cofactor (may be prime or composite)
        return largest

    @property
    def smooth_exponents(self) -> tuple[int, int, int]:
        """(a, b, c) where regular_part = 2^a * 3^b * 5^c."""
        exp = smooth_exponents(self.regular_part)
        return exp if exp is not None else (0, 0, 0)

    def distance_to_regular(self, smooth_numbers: list[int] | None = None) -> int:
        """Minimum |n - r| where r is 5-smooth."""
        if self.is_regular:
            return 0
        if smooth_numbers is None:
            from cuneiform.core.smooth import generate_smooth_numbers
            smooth_numbers = [s.value for s in generate_smooth_numbers(self.n * 2)]
        best = self.n  # worst case
        for s in smooth_numbers:
            d = abs(self.n - s)
            if d < best:
                best = d
            if s > self.n + best:
                break
        return best

    def __repr__(self) -> str:
        return (f"RC(n={self.n}, reg={self.regular_part}, "
                f"cofactor={self.cofactor}, tier={self.regularity_tier})")


def classify_regularity(n: int) -> dict:
    """Convenience function returning full classification dict."""
    rc = RegularityClass(n)
    return {
        "n": n,
        "regular_part": rc.regular_part,
        "cofactor": rc.cofactor,
        "tier": rc.regularity_tier,
        "is_regular": rc.is_regular,
        "largest_prime_factor": rc.largest_prime,
        "smooth_exponents": rc.smooth_exponents,
    }


def regularity_spectrum(values: list[int]) -> dict[int, int]:
    """Classify a list of values and return {tier: count} histogram."""
    spectrum: dict[int, int] = {}
    for v in values:
        if v <= 0:
            continue
        tier = RegularityClass(v).regularity_tier
        spectrum[tier] = spectrum.get(tier, 0) + 1
    return dict(sorted(spectrum.items()))


def regularity_density(n: int) -> dict[int, float]:
    """Fraction of integers 1..n in each regularity tier."""
    tiers: dict[int, int] = {}
    for i in range(1, n + 1):
        t = RegularityClass(i).regularity_tier
        tiers[t] = tiers.get(t, 0) + 1
    return {t: count / n for t, count in sorted(tiers.items())}
