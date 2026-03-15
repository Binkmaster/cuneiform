"""Quadratic Sieve — standard and sexagesimal variants.

The QS is simpler than NFS and serves as the primary testing ground
for the sexagesimal hypothesis.
"""

from __future__ import annotations

from math import log
import random

from cuneiform.core.accel import gcd, isqrt, powmod
from .primes import sieve_of_eratosthenes, legendre_symbol, tonelli_shanks
from .factor_base import StandardFactorBase, SexagesimalFactorBase
from .regularity import RegularityClass


def _trial_divide(n: int, primes: list[int]) -> list[int] | None:
    """Try to completely factor |n| over the given primes.

    Returns exponent vector if successful, None if cofactor remains.
    The first entry is the sign exponent (1 if n < 0, 0 otherwise).
    """
    exponents = [0] * len(primes)
    temp = n

    # Handle sign
    if temp < 0:
        exponents[0] = 1
        temp = -temp

    for i, p in enumerate(primes):
        if p == -1:
            continue
        while temp % p == 0:
            temp //= p
            exponents[i] += 1

    if temp == 1:
        return exponents
    return None


def _gaussian_elimination_gf2(matrix: list[list[int]]) -> list[list[int]]:
    """Find null space vectors of a binary matrix (mod 2).

    Returns list of dependency vectors (which rows combine to zero mod 2).
    """
    if not matrix:
        return []

    nrows = len(matrix)
    ncols = len(matrix[0])

    # Augment with identity to track row operations
    aug = [row[:] + [1 if i == j else 0 for j in range(nrows)]
           for i, row in enumerate(matrix)]

    # Reduce mod 2
    for i in range(len(aug)):
        for j in range(len(aug[i])):
            aug[i][j] %= 2

    pivot_col = 0
    pivot_rows = []

    for col in range(ncols):
        if pivot_col >= nrows:
            break
        # Find pivot
        found = None
        for row in range(pivot_col, nrows):
            if aug[row][col] % 2 == 1:
                found = row
                break
        if found is None:
            continue

        # Swap
        aug[pivot_col], aug[found] = aug[found], aug[pivot_col]
        pivot_rows.append(pivot_col)

        # Eliminate
        for row in range(nrows):
            if row != pivot_col and aug[row][col] % 2 == 1:
                for k in range(len(aug[row])):
                    aug[row][k] = (aug[row][k] + aug[pivot_col][k]) % 2

        pivot_col += 1

    # Find free rows (those not used as pivots)
    null_vectors = []
    pivot_set = set(pivot_rows)
    for row in range(nrows):
        if row not in pivot_set and any(aug[row][ncols + j] for j in range(nrows)):
            # This row gives a dependency
            vec = [aug[row][ncols + j] for j in range(nrows)]
            null_vectors.append(vec)

    return null_vectors


class QuadraticSieve:
    """Standard Quadratic Sieve implementation."""

    def __init__(self, n: int, bound: int | None = None,
                 sieve_range: int | None = None):
        self.n = n
        self.fb = StandardFactorBase(n, bound)
        self.sieve_range = sieve_range or max(self.fb.B * 4, 10000)
        self.relations: list[tuple[int, int, list[int]]] = []
        self.stats = {
            "sieve_evaluations": 0,
            "smooth_found": 0,
            "total_divisions": 0,
        }

    def sieve(self) -> list[tuple[int, int, list[int]]]:
        """Run the sieve and collect smooth relations."""
        sqrt_n = isqrt(self.n)
        if sqrt_n * sqrt_n == self.n:
            return []  # Perfect square

        primes = self.fb.primes
        M = self.sieve_range

        # Build sieve array using log approximation
        sieve_log = [0.0] * (2 * M + 1)

        for idx, p in enumerate(primes):
            if p == -1 or p < 2:
                continue
            logp = log(p)
            roots = tonelli_shanks(self.n % p, p)
            for r in roots:
                start = (r - (sqrt_n % p) + p) % p
                for i in range(start, 2 * M + 1, p):
                    sieve_log[i] += logp

        # Expected size of Q(x)
        expected = log(max(2 * sqrt_n * M, 2))
        threshold = expected * 0.8

        # Collect smooth candidates
        for i in range(2 * M + 1):
            if sieve_log[i] < threshold:
                continue

            x = i - M
            val = (sqrt_n + x) ** 2 - self.n
            if val == 0:
                continue
            self.stats["sieve_evaluations"] += 1

            exponents = _trial_divide(val, primes)
            if exponents is not None:
                self.relations.append((x, val, exponents))
                self.stats["smooth_found"] += 1

            if len(self.relations) > len(primes) + 10:
                break

        return self.relations

    def factor(self) -> tuple[int, int] | None:
        """Full QS pipeline: sieve -> matrix -> factor."""
        self.sieve()

        needed = self.fb.size() + 1
        if len(self.relations) < needed:
            return None

        # Build exponent matrix (mod 2)
        matrix = [[e % 2 for e in rel[2]] for rel in self.relations]
        null_vectors = _gaussian_elimination_gf2(matrix)

        sqrt_n = isqrt(self.n)

        for vec in null_vectors:
            # Combine relations indicated by this null vector
            x_product = 1
            y_squared_exponents = [0] * len(self.fb.primes)

            for i, bit in enumerate(vec):
                if bit:
                    rel_x, rel_val, rel_exp = self.relations[i]
                    x_product = (x_product * (sqrt_n + rel_x)) % self.n
                    for j, e in enumerate(rel_exp):
                        y_squared_exponents[j] += e

            # Compute y = product of primes^(exp/2)
            y = 1
            for j, e in enumerate(y_squared_exponents):
                p = self.fb.primes[j]
                if p == -1:
                    continue
                y = (y * powmod(p, e // 2, self.n)) % self.n

            x = x_product % self.n
            g = gcd(abs(x - y), self.n)
            if 1 < g < self.n:
                return (g, self.n // g)

        return None


class SexagesimalQuadraticSieve:
    """Quadratic Sieve with sexagesimal preprocessing.

    Key modifications:
    1. Tiered factor base
    2. Regularity prefilter (tier-0 = free smooth relations)
    3. Tiered prime ordering in sieve
    """

    def __init__(self, n: int, bound: int | None = None,
                 sieve_range: int | None = None):
        self.n = n
        self.fb = SexagesimalFactorBase(n, bound)
        self.sieve_range = sieve_range or max(self.fb.B * 4, 10000)
        self.relations: list[tuple[int, int, list[int]]] = []
        self.stats = {
            "sieve_evaluations": 0,
            "smooth_found": 0,
            "smooth_by_tier": {},
            "total_divisions": 0,
            "prefilter_saves": 0,
        }

    def sieve(self) -> list[tuple[int, int, list[int]]]:
        """Modified sieve with sexagesimal preprocessing."""
        sqrt_n = isqrt(self.n)
        if sqrt_n * sqrt_n == self.n:
            return []

        primes = self.fb.all_primes_with_sign()
        M = self.sieve_range

        # Phase 0: Regularity prefilter
        prefiltered = set()
        for x_offset in range(-M, M + 1):
            val = (sqrt_n + x_offset) ** 2 - self.n
            if val == 0:
                continue
            rc = RegularityClass(abs(val))
            if rc.is_regular:
                exponents = _trial_divide(val, primes)
                if exponents is not None:
                    self.relations.append((x_offset, val, exponents))
                    self.stats["smooth_found"] += 1
                    self.stats["prefilter_saves"] += 1
                    tier = 0
                    self.stats["smooth_by_tier"][tier] = \
                        self.stats["smooth_by_tier"].get(tier, 0) + 1
                    prefiltered.add(x_offset)

        # Phase 1: Standard sieve with tiered prime ordering
        sieve_log = [0.0] * (2 * M + 1)
        for idx, p in enumerate(primes):
            if p == -1 or p < 2:
                continue
            logp = log(p)
            roots = tonelli_shanks(self.n % p, p)
            for r in roots:
                start = (r - (sqrt_n % p) + p) % p
                for i in range(start, 2 * M + 1, p):
                    sieve_log[i] += logp

        expected = log(max(2 * sqrt_n * M, 2))
        threshold = expected * 0.8

        for i in range(2 * M + 1):
            if sieve_log[i] < threshold:
                continue
            x = i - M
            if x in prefiltered:
                continue

            val = (sqrt_n + x) ** 2 - self.n
            if val == 0:
                continue
            self.stats["sieve_evaluations"] += 1

            exponents = _trial_divide(val, primes)
            if exponents is not None:
                self.relations.append((x, val, exponents))
                self.stats["smooth_found"] += 1
                tier = RegularityClass(abs(val)).regularity_tier
                self.stats["smooth_by_tier"][tier] = \
                    self.stats["smooth_by_tier"].get(tier, 0) + 1

            if len(self.relations) > len(primes) + 10:
                break

        return self.relations

    def factor(self) -> tuple[int, int] | None:
        """Full sexagesimal QS pipeline."""
        self.sieve()

        needed = self.fb.size() + 2
        if len(self.relations) < needed:
            return None

        primes = self.fb.all_primes_with_sign()
        matrix = [[e % 2 for e in rel[2]] for rel in self.relations]
        null_vectors = _gaussian_elimination_gf2(matrix)

        sqrt_n = isqrt(self.n)

        for vec in null_vectors:
            x_product = 1
            y_squared_exponents = [0] * len(primes)

            for i, bit in enumerate(vec):
                if bit:
                    rel_x, rel_val, rel_exp = self.relations[i]
                    x_product = (x_product * (sqrt_n + rel_x)) % self.n
                    for j, e in enumerate(rel_exp):
                        y_squared_exponents[j] += e

            y = 1
            for j, e in enumerate(y_squared_exponents):
                p = primes[j]
                if p == -1:
                    continue
                y = (y * powmod(p, e // 2, self.n)) % self.n

            x = x_product % self.n
            g = gcd(abs(x - y), self.n)
            if 1 < g < self.n:
                return (g, self.n // g)

        return None
