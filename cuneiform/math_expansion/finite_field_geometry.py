"""Finite field geometry — rational trigonometry over F_p.

Wildberger's rational trigonometry works over ANY field, including
finite fields F_p. Quadrance and spread are defined purely algebraically.
This connects CUNEIFORM's geometric framework to elliptic curve
analysis and coding theory.
"""

from __future__ import annotations

from math import gcd


class FpPoint:
    """A point in the affine plane over F_p."""

    __slots__ = ("x", "y", "p")

    def __init__(self, x: int, y: int, p: int):
        self.x = x % p
        self.y = y % p
        self.p = p

    def __eq__(self, other: object) -> bool:
        if isinstance(other, FpPoint):
            return self.x == other.x and self.y == other.y and self.p == other.p
        return NotImplemented

    def __hash__(self) -> int:
        return hash((self.x, self.y, self.p))

    def __repr__(self) -> str:
        return f"({self.x}, {self.y}) mod {self.p}"


def _mod_inv(a: int, p: int) -> int:
    """Modular inverse using extended Euclidean algorithm."""
    if a % p == 0:
        raise ZeroDivisionError(f"{a} has no inverse mod {p}")
    return pow(a, p - 2, p)


class FiniteFieldGeometry:
    """Rational trigonometry over F_p.

    All operations are exact modular arithmetic. No floats.
    Quadrance and spread are elements of F_p.
    """

    def __init__(self, p: int):
        if p < 3:
            raise ValueError("Need prime p >= 3")
        self.p = p

    def quadrance(self, A: FpPoint, B: FpPoint) -> int:
        """Q(A,B) = (x_B - x_A)² + (y_B - y_A)² mod p."""
        dx = (B.x - A.x) % self.p
        dy = (B.y - A.y) % self.p
        return (dx * dx + dy * dy) % self.p

    def spread_from_quadrances(self, Q_opp: int, Q_adj1: int,
                               Q_adj2: int) -> int | None:
        """Cross law spread: s = 1 - (Q1+Q2-Q3)²/(4·Q1·Q2) mod p."""
        denom = (4 * Q_adj1 * Q_adj2) % self.p
        if denom == 0:
            return None  # Degenerate case
        num = (Q_adj1 + Q_adj2 - Q_opp) % self.p
        inv_denom = _mod_inv(denom, self.p)
        s = (1 - num * num % self.p * inv_denom) % self.p
        return s

    def all_points(self) -> list[FpPoint]:
        """Generate all points in the affine plane F_p²."""
        return [FpPoint(x, y, self.p)
                for x in range(self.p) for y in range(self.p)]

    def count_isotropic_points(self) -> int:
        """Count points (x,y) where x²+y²=0 mod p (null/isotropic).

        These are the "problematic" points in finite field geometry
        where quadrance is zero despite non-zero displacement.
        """
        count = 0
        for x in range(self.p):
            for y in range(self.p):
                if (x * x + y * y) % self.p == 0:
                    count += 1
        return count

    def quadrance_spectrum(self) -> dict[int, int]:
        """Distribution of quadrance values over all point pairs.

        Shows how many pairs of points have each possible quadrance
        value in F_p. In Euclidean geometry, quadrance can be any
        non-negative real. In F_p, it's constrained to {0,...,p-1}.
        """
        spectrum: dict[int, int] = {}
        for x in range(self.p):
            for y in range(self.p):
                q = (x * x + y * y) % self.p
                spectrum[q] = spectrum.get(q, 0) + 1
        return spectrum

    def is_quadratic_residue(self, a: int) -> bool:
        """Check if a is a quadratic residue mod p (Euler's criterion)."""
        if a % self.p == 0:
            return True
        return pow(a, (self.p - 1) // 2, self.p) == 1

    def spread_values(self) -> set[int]:
        """All possible spread values in this finite geometry.

        In F_p, not all elements of the field can occur as spreads.
        The set of achievable spreads tells us about the geometry's
        structure.
        """
        spreads = set()
        points = self.all_points()
        O = FpPoint(0, 0, self.p)
        for A in points:
            if A == O:
                continue
            for B in points:
                if B == O or B == A:
                    continue
                Q_a = self.quadrance(A, B)
                Q_b = self.quadrance(O, B)
                Q_c = self.quadrance(O, A)
                s = self.spread_from_quadrances(Q_a, Q_b, Q_c)
                if s is not None:
                    spreads.add(s)
        return spreads

    def regularity_connection(self) -> dict:
        """Analyze connection between 5-smooth structure and F_p geometry.

        For primes p where p-1 has large 5-smooth part, the geometry
        has special properties related to the multiplicative structure.
        """
        p = self.p
        # Factor out 2, 3, 5 from p-1
        pm1 = p - 1
        smooth_part = 1
        remainder = pm1
        for q in (2, 3, 5):
            while remainder % q == 0:
                smooth_part *= q
                remainder //= q

        return {
            "prime": p,
            "p_minus_1": pm1,
            "smooth_part": smooth_part,
            "cofactor": remainder,
            "smooth_ratio": smooth_part / pm1,
            "isotropic_count": self.count_isotropic_points(),
            "quadrance_spectrum_size": len(self.quadrance_spectrum()),
        }
