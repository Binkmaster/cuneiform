"""Equation solving over sexagesimal rationals.

Solves polynomial equations for rational roots, linear systems,
and quadratic equations — all exact.
"""

from __future__ import annotations

from fractions import Fraction

from cuneiform.core.rational import SexaRational
from .ratpoly import RatPoly
from .ratmatrix import RatMatrix


class RatSolve:
    """Equation solver over SexaRational.

    All solutions are exact rationals. If a solution is irrational,
    it won't appear — CUNEIFORM doesn't lie to you with approximations.
    """

    @staticmethod
    def linear(a: SexaRational | int, b: SexaRational | int) -> SexaRational | None:
        """Solve ax + b = 0. Returns x = -b/a, or None if a = 0."""
        if isinstance(a, int):
            a = SexaRational(a)
        if isinstance(b, int):
            b = SexaRational(b)
        if a == SexaRational(0):
            return None
        return SexaRational(0) - b / a

    @staticmethod
    def quadratic(a: SexaRational | int, b: SexaRational | int,
                  c: SexaRational | int) -> list[SexaRational]:
        """Solve ax² + bx + c = 0 for rational roots.

        Returns 0, 1, or 2 roots. Only returns exact rationals —
        if the discriminant is not a perfect square, returns empty.
        """
        if isinstance(a, int):
            a = SexaRational(a)
        if isinstance(b, int):
            b = SexaRational(b)
        if isinstance(c, int):
            c = SexaRational(c)

        if a == SexaRational(0):
            sol = RatSolve.linear(b, c)
            return [sol] if sol is not None else []

        disc = b * b - SexaRational(4) * a * c
        if disc < SexaRational(0):
            return []

        # Check if discriminant is a perfect rational square
        disc_frac = disc.as_fraction
        num_sq = _isqrt_exact(abs(disc_frac.numerator))
        den_sq = _isqrt_exact(abs(disc_frac.denominator))

        if num_sq is None or den_sq is None:
            return []  # Irrational roots — not representable

        sqrt_disc = SexaRational(Fraction(num_sq, den_sq))
        two_a = SexaRational(2) * a

        r1 = (SexaRational(0) - b + sqrt_disc) / two_a
        r2 = (SexaRational(0) - b - sqrt_disc) / two_a

        if r1 == r2:
            return [r1]
        return sorted([r1, r2], key=lambda r: float(r))

    @staticmethod
    def polynomial_roots(poly: RatPoly) -> list[SexaRational]:
        """Find all rational roots of a polynomial."""
        return poly.rational_roots()

    @staticmethod
    def linear_system(A: RatMatrix, b: list[SexaRational | int]) -> list[SexaRational]:
        """Solve Ax = b. Exact."""
        return A.solve(b)

    @staticmethod
    def polynomial_from_equation(coeffs: list[SexaRational | int]) -> list[SexaRational]:
        """Solve a_n x^n + ... + a_1 x + a_0 = 0 for rational roots.

        coeffs: [a_0, a_1, ..., a_n] (constant term first).
        """
        return RatPoly(coeffs).rational_roots()


def _isqrt_exact(n: int) -> int | None:
    """Integer square root if n is a perfect square, else None."""
    if n < 0:
        return None
    if n == 0:
        return 0
    # Newton's method for integer sqrt
    x = n
    y = (x + 1) // 2
    while y < x:
        x = y
        y = (x + n // x) // 2
    if x * x == n:
        return x
    return None
