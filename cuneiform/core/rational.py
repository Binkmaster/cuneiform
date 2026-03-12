"""Exact rational arithmetic with sexagesimal regularity awareness.

Wraps Python's Fraction with knowledge of whether a number has a terminating
sexagesimal (base-60) expansion.
"""

from __future__ import annotations

from fractions import Fraction
from functools import total_ordering

from .smooth import is_smooth, smooth_exponents, extract_smooth_part


@total_ordering
class SexaRational:
    """A rational number aware of its sexagesimal regularity.

    Every SexaRational has an exact Fraction value and knows whether
    it has a terminating sexagesimal expansion.
    """

    __slots__ = ("_frac",)

    def __init__(self, numerator: int | Fraction = 0, denominator: int = 1):
        if isinstance(numerator, Fraction):
            self._frac = numerator
        elif isinstance(numerator, SexaRational):
            self._frac = numerator._frac
        else:
            self._frac = Fraction(numerator, denominator)

    @classmethod
    def _from_frac(cls, f: Fraction) -> SexaRational:
        """Fast constructor from an already-built Fraction."""
        obj = object.__new__(cls)
        obj._frac = f
        return obj

    @property
    def numerator(self) -> int:
        return self._frac.numerator

    @property
    def denominator(self) -> int:
        return self._frac.denominator

    @property
    def as_fraction(self) -> Fraction:
        return self._frac

    @property
    def is_regular(self) -> bool:
        """Denominator is 5-smooth (terminates in base-60)."""
        return is_smooth(self._frac.denominator)

    @property
    def regularity_class(self) -> int:
        """Largest prime factor of the denominator.

        2, 3, or 5 = fully regular.
        7+ = irregular.
        Returns 1 for integer values (denominator = 1).
        """
        d = self._frac.denominator
        if d == 1:
            return 1
        largest = 1
        for p in (2, 3, 5):
            while d % p == 0:
                d //= p
                largest = max(largest, p)
        if d == 1:
            return largest
        # d still has factors > 5; find the largest
        temp = d
        f = 7
        while f * f <= temp:
            while temp % f == 0:
                largest = max(largest, f)
                temp //= f
            f += 2
        if temp > 1:
            largest = max(largest, temp)
        return largest

    @property
    def smooth_order(self) -> tuple[int, int, int]:
        """Returns (a, b, c) where denominator = 2^a * 3^b * 5^c.

        Only valid for regular numbers. Raises ValueError otherwise.
        """
        exp = smooth_exponents(self._frac.denominator)
        if exp is None:
            raise ValueError(
                f"Denominator {self._frac.denominator} is not 5-smooth"
            )
        return exp

    # Arithmetic -- all exact, returning SexaRational

    def __add__(self, other: SexaRational | int) -> SexaRational:
        other = self._coerce(other)
        return SexaRational._from_frac(self._frac + other._frac)

    def __radd__(self, other: int) -> SexaRational:
        return SexaRational._from_frac(Fraction(other) + self._frac)

    def __sub__(self, other: SexaRational | int) -> SexaRational:
        other = self._coerce(other)
        return SexaRational._from_frac(self._frac - other._frac)

    def __rsub__(self, other: int) -> SexaRational:
        return SexaRational._from_frac(Fraction(other) - self._frac)

    def __mul__(self, other: SexaRational | int) -> SexaRational:
        other = self._coerce(other)
        return SexaRational._from_frac(self._frac * other._frac)

    def __rmul__(self, other: int) -> SexaRational:
        return SexaRational._from_frac(Fraction(other) * self._frac)

    def __truediv__(self, other: SexaRational | int) -> SexaRational:
        other = self._coerce(other)
        if other._frac == 0:
            raise ZeroDivisionError("Division by zero")
        return SexaRational._from_frac(self._frac / other._frac)

    def __rtruediv__(self, other: int) -> SexaRational:
        if self._frac == 0:
            raise ZeroDivisionError("Division by zero")
        return SexaRational._from_frac(Fraction(other) / self._frac)

    def __mod__(self, other: SexaRational | int) -> SexaRational:
        other = self._coerce(other)
        return SexaRational._from_frac(self._frac % other._frac)

    def __pow__(self, exp: int) -> SexaRational:
        return SexaRational._from_frac(self._frac ** exp)

    def __neg__(self) -> SexaRational:
        return SexaRational._from_frac(-self._frac)

    def __abs__(self) -> SexaRational:
        return SexaRational._from_frac(abs(self._frac))

    def __pos__(self) -> SexaRational:
        return self

    # Comparison

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SexaRational):
            return self._frac == other._frac
        if isinstance(other, (int, Fraction)):
            return self._frac == other
        return NotImplemented

    def __lt__(self, other: SexaRational | int) -> bool:
        other = self._coerce(other)
        return self._frac < other._frac

    def __hash__(self) -> int:
        return hash(self._frac)

    def __bool__(self) -> bool:
        return self._frac != 0

    def __float__(self) -> float:
        return float(self._frac)

    def __int__(self) -> int:
        return int(self._frac)

    def __repr__(self) -> str:
        if self._frac.denominator == 1:
            return f"SexaRational({self._frac.numerator})"
        return f"SexaRational({self._frac.numerator}/{self._frac.denominator})"

    def __str__(self) -> str:
        if self._frac.denominator == 1:
            return str(self._frac.numerator)
        return f"{self._frac.numerator}/{self._frac.denominator}"

    @staticmethod
    def _coerce(other) -> SexaRational:
        if isinstance(other, SexaRational):
            return other
        if isinstance(other, int):
            return SexaRational(other)
        if isinstance(other, Fraction):
            return SexaRational._from_frac(other)
        raise TypeError(f"Cannot coerce {type(other)} to SexaRational")
