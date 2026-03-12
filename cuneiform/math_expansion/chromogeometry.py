"""Chromogeometry — Wildberger's three-fold geometry.

Three quadratic forms on the plane:
- Blue (Euclidean):   Q_b = dx² + dy²
- Red (relativistic):  Q_r = dx² - dy²
- Green (relativistic): Q_g = 2·dx·dy

All three obey the same rational trigonometry laws, with different
notions of "perpendicular" and "spread". This is the first
computational implementation of chromogeometry with exact arithmetic.
"""

from __future__ import annotations

from enum import Enum
from fractions import Fraction

from cuneiform.core.rational import SexaRational


class Color(Enum):
    """The three chromogeometric colors."""
    BLUE = "blue"      # Euclidean
    RED = "red"        # Relativistic (Minkowski-like)
    GREEN = "green"    # Relativistic (null-like)


class ChromoPoint:
    """A point in the chromogeometric plane.

    The same point, but quadrance/spread depend on which color geometry.
    """

    __slots__ = ("x", "y")

    def __init__(self, x: Fraction | int, y: Fraction | int):
        self.x = Fraction(x)
        self.y = Fraction(y)

    def __repr__(self) -> str:
        return f"ChromoPoint({self.x}, {self.y})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ChromoPoint):
            return self.x == other.x and self.y == other.y
        return NotImplemented

    def __hash__(self) -> int:
        return hash((self.x, self.y))


class ChromoQuadrance:
    """Quadrance under a specific color geometry."""

    __slots__ = ("value", "color")

    def __init__(self, value: Fraction, color: Color):
        self.value = value
        self.color = color

    def __repr__(self) -> str:
        return f"Q_{self.color.value}({self.value})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ChromoQuadrance):
            return self.value == other.value and self.color == other.color
        return NotImplemented


class ChromoSpread:
    """Spread under a specific color geometry."""

    __slots__ = ("value", "color")

    def __init__(self, value: Fraction, color: Color):
        self.value = value
        self.color = color

    def __repr__(self) -> str:
        return f"s_{self.color.value}({self.value})"


class ChromoGeometry:
    """Chromogeometric computations in all three color geometries.

    Given the same points/lines, computes quadrances and spreads
    under blue, red, and green metrics. Demonstrates the three-fold
    symmetry that Wildberger discovered.
    """

    @staticmethod
    def quadrance(p1: ChromoPoint, p2: ChromoPoint,
                  color: Color) -> ChromoQuadrance:
        """Compute quadrance between two points in a given color.

        Blue:  Q = dx² + dy²  (standard Euclidean)
        Red:   Q = dx² - dy²  (Minkowski-like)
        Green: Q = 2·dx·dy    (null/isotropic)
        """
        dx = p2.x - p1.x
        dy = p2.y - p1.y

        if color == Color.BLUE:
            q = dx * dx + dy * dy
        elif color == Color.RED:
            q = dx * dx - dy * dy
        elif color == Color.GREEN:
            q = Fraction(2) * dx * dy
        else:
            raise ValueError(f"Unknown color: {color}")

        return ChromoQuadrance(q, color)

    @staticmethod
    def spread_from_quadrances(Q_opp: ChromoQuadrance,
                               Q_adj1: ChromoQuadrance,
                               Q_adj2: ChromoQuadrance) -> ChromoSpread:
        """Compute spread from three quadrances using the Cross Law.

        s = 1 - (Q1 + Q2 - Q3)² / (4·Q1·Q2)

        This formula works identically in all three color geometries.
        """
        color = Q_opp.color
        Q1, Q2, Q3 = Q_adj1.value, Q_adj2.value, Q_opp.value
        if Q1 == 0 or Q2 == 0:
            return ChromoSpread(Fraction(0), color)
        num = Q1 + Q2 - Q3
        s = Fraction(1) - (num * num) / (Fraction(4) * Q1 * Q2)
        return ChromoSpread(s, color)

    @classmethod
    def analyze_triangle(cls, A: ChromoPoint, B: ChromoPoint,
                         C: ChromoPoint) -> dict:
        """Analyze a triangle in all three color geometries.

        Returns quadrances and spreads for each color, demonstrating
        the chromogeometric relationships.
        """
        result = {}
        for color in Color:
            Q_a = cls.quadrance(B, C, color)  # opposite A
            Q_b = cls.quadrance(A, C, color)  # opposite B
            Q_c = cls.quadrance(A, B, color)  # opposite C

            s_A = cls.spread_from_quadrances(Q_a, Q_b, Q_c)
            s_B = cls.spread_from_quadrances(Q_b, Q_a, Q_c)
            s_C = cls.spread_from_quadrances(Q_c, Q_a, Q_b)

            # Verify triple spread formula: (s1+s2+s3)² = 2(s1²+s2²+s3²) + 4·s1·s2·s3
            s1, s2, s3 = s_A.value, s_B.value, s_C.value
            lhs = (s1 + s2 + s3) ** 2
            rhs = 2 * (s1**2 + s2**2 + s3**2) + 4 * s1 * s2 * s3

            result[color.value] = {
                "quadrances": (Q_a, Q_b, Q_c),
                "spreads": (s_A, s_B, s_C),
                "triple_spread_holds": lhs == rhs,
            }

        # The chromogeometric identity: Q_blue · Q_red · Q_green relationships
        # For each side: Q_blue² = Q_red² + Q_green²  (Pythagoras of quadratic forms)
        chromo_checks = []
        for i in range(3):
            Qb = result["blue"]["quadrances"][i].value
            Qr = result["red"]["quadrances"][i].value
            Qg = result["green"]["quadrances"][i].value
            # The key identity: Q_blue² = Q_red² + Q_green²
            chromo_checks.append(Qb * Qb == Qr * Qr + Qg * Qg)

        result["chromo_pythagoras"] = chromo_checks

        return result
