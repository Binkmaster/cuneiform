"""5-smooth number theory & regular numbers.

5-smooth numbers (also called regular numbers or Hamming numbers) are integers
whose only prime factors are 2, 3, and 5. These are the 'native' numbers of
sexagesimal arithmetic -- the numbers whose reciprocals terminate in base 60.
"""

from __future__ import annotations

import heapq
from math import gcd


def is_smooth(n: int) -> bool:
    """Check if n is 5-smooth (regular). n must be positive."""
    if n <= 0:
        raise ValueError(f"is_smooth requires positive integer, got {n}")
    for p in (2, 3, 5):
        while n % p == 0:
            n //= p
    return n == 1


def smooth_exponents(n: int) -> tuple[int, int, int] | None:
    """Return (a, b, c) where n = 2^a * 3^b * 5^c, or None if not 5-smooth."""
    if n <= 0:
        return None
    a = b = c = 0
    while n % 2 == 0:
        a += 1
        n //= 2
    while n % 3 == 0:
        b += 1
        n //= 3
    while n % 5 == 0:
        c += 1
        n //= 5
    if n != 1:
        return None
    return (a, b, c)


def extract_smooth_part(n: int) -> tuple[int, int]:
    """Factor n into (smooth_part, cofactor) where smooth_part is the largest
    5-smooth divisor and cofactor has no factors of 2, 3, or 5.
    n = smooth_part * cofactor."""
    if n <= 0:
        raise ValueError(f"extract_smooth_part requires positive integer, got {n}")
    cofactor = n
    for p in (2, 3, 5):
        while cofactor % p == 0:
            cofactor //= p
    smooth_part = n // cofactor
    return (smooth_part, cofactor)


class SmoothNumber:
    """A 5-smooth (regular) number: n = 2^a * 3^b * 5^c.

    These are the numbers whose reciprocals terminate in base 60.
    """

    __slots__ = ("a", "b", "c", "_value")

    def __init__(self, a: int = 0, b: int = 0, c: int = 0):
        if a < 0 or b < 0 or c < 0:
            raise ValueError("Exponents must be non-negative")
        self.a = a
        self.b = b
        self.c = c
        self._value = (2 ** a) * (3 ** b) * (5 ** c)

    @classmethod
    def from_int(cls, n: int) -> SmoothNumber:
        """Create from an integer. Raises ValueError if not 5-smooth."""
        exp = smooth_exponents(n)
        if exp is None:
            raise ValueError(f"{n} is not 5-smooth")
        return cls(*exp)

    @property
    def value(self) -> int:
        return self._value

    @property
    def exponents(self) -> tuple[int, int, int]:
        return (self.a, self.b, self.c)

    def reciprocal_pair(self, power: int = None) -> SmoothNumber:
        """The Babylonian reciprocal: find m such that self * m = 60^k.

        If power is given, computes 60^power / self.
        Otherwise finds the smallest k such that 60^k / self is an integer.
        """
        if power is not None:
            # 60^power = 2^(2*power) * 3^power * 5^power
            ra = 2 * power - self.a
            rb = power - self.b
            rc = power - self.c
            if ra < 0 or rb < 0 or rc < 0:
                raise ValueError(
                    f"60^{power} is not divisible by {self.value}"
                )
            return SmoothNumber(ra, rb, rc)

        # Find smallest k: need 2k >= a, k >= b, k >= c
        k = max((self.a + 1) // 2, self.b, self.c)
        # Verify 2k >= a
        while 2 * k < self.a:
            k += 1
        return SmoothNumber(2 * k - self.a, k - self.b, k - self.c)

    def __mul__(self, other: SmoothNumber) -> SmoothNumber:
        return SmoothNumber(self.a + other.a, self.b + other.b, self.c + other.c)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SmoothNumber):
            return self._value == other._value
        if isinstance(other, int):
            return self._value == other
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._value)

    def __lt__(self, other: SmoothNumber) -> bool:
        return self._value < other._value

    def __le__(self, other: SmoothNumber) -> bool:
        return self._value <= other._value

    def __repr__(self) -> str:
        return f"SmoothNumber(2^{self.a} * 3^{self.b} * 5^{self.c} = {self._value})"

    def __int__(self) -> int:
        return self._value


def generate_smooth_numbers(limit: int) -> list[SmoothNumber]:
    """Generate all 5-smooth numbers up to limit using a min-heap merge."""
    if limit < 1:
        return []

    result = []
    seen = {1}
    heap = [1]

    while heap:
        n = heapq.heappop(heap)
        if n > limit:
            break
        result.append(SmoothNumber.from_int(n))
        for p in (2, 3, 5):
            m = n * p
            if m <= limit and m not in seen:
                seen.add(m)
                heapq.heappush(heap, m)

    return result


def smooth_in_range(start: int, end: int) -> list[SmoothNumber]:
    """Find all 5-smooth numbers in [start, end]."""
    all_smooth = generate_smooth_numbers(end)
    return [s for s in all_smooth if s.value >= start]


def near_smooth(n: int, tolerance: int = 1) -> list[tuple[int, int]]:
    """Find numbers near n that are 'almost' 5-smooth.

    Returns (number, cofactor) pairs where the number is within 10% of n
    and the cofactor (non-smooth part) has at most `tolerance` prime factors > 5.
    """
    results = []
    margin = max(n // 10, 10)
    for candidate in range(max(1, n - margin), n + margin + 1):
        smooth_part, cofactor = extract_smooth_part(candidate)
        # Count prime factors of cofactor
        if cofactor == 1:
            results.append((candidate, cofactor))
            continue
        # Simple prime factor count
        temp = cofactor
        factor_count = 0
        d = 7
        while d * d <= temp and factor_count <= tolerance:
            while temp % d == 0:
                factor_count += 1
                temp //= d
            d += 2
        if temp > 1:
            factor_count += 1
        if factor_count <= tolerance:
            results.append((candidate, cofactor))

    return results
