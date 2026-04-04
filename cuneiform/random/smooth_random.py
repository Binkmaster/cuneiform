"""Generate random regular (5-smooth) numbers.

In Babylonian mathematics, regular numbers — those whose only prime
factors are 2, 3, and 5 — are special because they have terminating
sexagesimal reciprocals. This module generates random regular numbers,
useful for constructing problems that "work out nicely" on a clay tablet.
"""

from __future__ import annotations

from fractions import Fraction

from cuneiform.core import Sexa
from .generator import SexaRandom


class SmoothRandom:
    """Generate random 5-smooth (regular) numbers.

    Builds random regular numbers by choosing random exponents for
    the prime factors 2, 3, and 5, then forming 2^a * 3^b * 5^c.

    Example::

        sr = SmoothRandom(seed=7)
        n = sr.regular()          # e.g. Sexa(7200) = 2^5 * 3^2 * 5^2
        r = sr.reciprocal_pair()  # (n, 1/n) both terminating in base 60
    """

    def __init__(self, seed: int | None = None, *, max_exp: int = 8):
        self._rng = SexaRandom(seed=seed)
        self._max_exp = max_exp

    def regular(self, max_exp: int | None = None) -> Sexa:
        """Generate a random regular (5-smooth) number.

        Exponents for 2, 3, 5 are each drawn uniformly from [0, max_exp].
        The result is always >= 1.
        """
        mx = max_exp if max_exp is not None else self._max_exp
        a = self._rng.randint(0, mx)
        b = self._rng.randint(0, mx)
        c = self._rng.randint(0, mx)
        val = (2 ** a) * (3 ** b) * (5 ** c)
        return Sexa(val)

    def reciprocal_pair(self, max_exp: int | None = None) -> tuple[Sexa, Sexa]:
        """Generate a regular number and its exact sexagesimal reciprocal.

        Both n and 1/n have terminating base-60 expansions.
        """
        n = self.regular(max_exp)
        recip = Sexa._from_frac(Fraction(1, int(n._frac)))
        return n, recip

    def regular_fraction(self, max_exp: int | None = None) -> Sexa:
        """Generate a random Sexa in (0, 1) that is regular.

        Produces n/m where both n < m are regular numbers.
        """
        mx = max_exp if max_exp is not None else self._max_exp
        # Generate two distinct regular numbers, return smaller/larger
        a = self.regular(mx)
        b = self.regular(mx)
        lo, hi = (a, b) if a._frac < b._frac else (b, a)
        if hi._frac == 0:
            # Degenerate: both zero exponents gave 1,1 → return 1/2
            return Sexa._from_frac(Fraction(1, 2))
        if lo._frac == hi._frac:
            # Same number → return 1/2 as a safe fallback
            return Sexa._from_frac(Fraction(1, 2))
        return Sexa._from_frac(lo._frac / hi._frac)

    def tablet_problem(self, max_exp: int | None = None) -> dict:
        """Generate a random "tablet-friendly" multiplication problem.

        Returns two regular factors and their product — the kind of
        exercise a Babylonian scribe student would practice.
        """
        a = self.regular(max_exp)
        b = self.regular(max_exp)
        product = Sexa._from_frac(a._frac * b._frac)
        return {
            "factor_a": a,
            "factor_b": b,
            "product": product,
            "display": f"{a} × {b} = {product}",
        }
