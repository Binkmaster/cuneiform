"""RatTriangle — triangle solver using rational trigonometry.

Solves any triangle using only exact rational operations.
No sin. No cos. No arctan. No pi. No approximation.
"""

from __future__ import annotations

from cuneiform.core.rational import SexaRational
from .point import RatPoint
from .line import RatLine, GeometryError
from .quadrance import Quadrance
from .spread import Spread
from .laws import (
    verify_pythagoras,
    verify_spread_law,
    verify_cross_law,
    verify_triple_spread,
    solve_cross_law_for_spread,
    solve_spread_law,
)


class RatTriangle:
    """A triangle defined by three RatPoints.

    All operations are exact rational arithmetic.
    """

    __slots__ = ("A", "B", "C", "Q_a", "Q_b", "Q_c", "s_A", "s_B", "s_C")

    def __init__(self, A: RatPoint, B: RatPoint, C: RatPoint):
        if A.collinear(B, C):
            raise GeometryError("Points are collinear — not a triangle")

        self.A, self.B, self.C = A, B, C

        # Quadrances of sides (named by opposite vertex)
        self.Q_a = Quadrance.between(B, C)  # opposite A
        self.Q_b = Quadrance.between(A, C)  # opposite B
        self.Q_c = Quadrance.between(A, B)  # opposite C

        # Spreads at each vertex
        self.s_A = solve_cross_law_for_spread(self.Q_b, self.Q_c, self.Q_a)
        self.s_B = solve_cross_law_for_spread(self.Q_a, self.Q_c, self.Q_b)
        self.s_C = solve_cross_law_for_spread(self.Q_a, self.Q_b, self.Q_c)

    def is_right(self) -> bool:
        """Does this triangle have a spread of exactly 1?"""
        return (self.s_A.is_right() or
                self.s_B.is_right() or
                self.s_C.is_right())

    def right_vertex(self) -> str | None:
        """Which vertex has spread 1? Returns 'A', 'B', 'C', or None."""
        if self.s_A.is_right():
            return "A"
        if self.s_B.is_right():
            return "B"
        if self.s_C.is_right():
            return "C"
        return None

    def verify_all_laws(self) -> dict[str, bool]:
        """Check applicable laws. All should return True for a valid triangle."""
        results = {}

        # Spread law: s_A/Q_a = s_B/Q_b
        results["spread_law_AB"] = verify_spread_law(
            self.s_A, self.Q_a, self.s_B, self.Q_b)
        results["spread_law_BC"] = verify_spread_law(
            self.s_B, self.Q_b, self.s_C, self.Q_c)

        # Cross law for each vertex
        results["cross_law_A"] = verify_cross_law(
            self.Q_b, self.Q_c, self.Q_a, self.s_A)
        results["cross_law_B"] = verify_cross_law(
            self.Q_a, self.Q_c, self.Q_b, self.s_B)
        results["cross_law_C"] = verify_cross_law(
            self.Q_a, self.Q_b, self.Q_c, self.s_C)

        # Triple spread formula
        results["triple_spread"] = verify_triple_spread(
            self.s_A, self.s_B, self.s_C)

        # Pythagoras (only for right triangles)
        rv = self.right_vertex()
        if rv == "A":
            results["pythagoras"] = verify_pythagoras(
                self.Q_b, self.Q_c, self.Q_a, self.s_A)
        elif rv == "B":
            results["pythagoras"] = verify_pythagoras(
                self.Q_a, self.Q_c, self.Q_b, self.s_B)
        elif rv == "C":
            results["pythagoras"] = verify_pythagoras(
                self.Q_a, self.Q_b, self.Q_c, self.s_C)

        return results

    def area_quadrance_16(self) -> SexaRational:
        """16 * (Area)^2 of the triangle.

        Classical area = (1/2)|a||b|sin(C).
        Rational: 16*A^2 = 2*Qa*Qb + 2*Qb*Qc + 2*Qa*Qc - Qa^2 - Qb^2 - Qc^2

        This is always rational and exact. To get 'area' you'd need a square
        root, which we avoid. The value 16*A^2 is fully sufficient for
        comparison, ordering, and exact computation.
        """
        Qa, Qb, Qc = self.Q_a.value, self.Q_b.value, self.Q_c.value
        return (SexaRational(2) * (Qa * Qb + Qb * Qc + Qa * Qc)
                - Qa ** 2 - Qb ** 2 - Qc ** 2)

    @classmethod
    def from_plimpton_row(cls, row) -> RatTriangle:
        """Construct triangle from a PlimptonRow.

        Places the right angle at the origin:
        A = (0, 0), B = (length, 0), C = (0, width)
        """
        A = RatPoint(SexaRational(0), SexaRational(0))
        B = RatPoint(SexaRational(row.length), SexaRational(0))
        C = RatPoint(SexaRational(0), SexaRational(row.width))
        return cls(A, B, C)

    @classmethod
    def from_triple(cls, a: int, b: int, c: int) -> RatTriangle:
        """Construct right triangle from a Pythagorean triple (a, b, c).

        Places right angle at origin: (0,0), (b,0), (0,a).
        """
        if a * a + b * b != c * c:
            raise GeometryError(f"({a}, {b}, {c}) is not a Pythagorean triple")
        A = RatPoint(SexaRational(0), SexaRational(0))
        B = RatPoint(SexaRational(b), SexaRational(0))
        C = RatPoint(SexaRational(0), SexaRational(a))
        return cls(A, B, C)

    @classmethod
    def solve_QQQ(cls, Q1: Quadrance, Q2: Quadrance,
                  Q3: Quadrance) -> tuple[Spread, Spread, Spread]:
        """Solve triangle given three quadrances (analog of SSS).

        Returns the three spreads.
        """
        s1 = solve_cross_law_for_spread(Q2, Q3, Q1)
        s2 = solve_cross_law_for_spread(Q1, Q3, Q2)
        s3 = solve_cross_law_for_spread(Q1, Q2, Q3)
        return (s1, s2, s3)

    @classmethod
    def solve_QSQ(cls, Q1: Quadrance, s3: Spread,
                  Q2: Quadrance) -> tuple[Quadrance, Spread, Spread]:
        """Solve triangle given Quadrance-Spread-Quadrance (analog of SAS).

        Given Q1, Q2 (adjacent sides) and s3 (included spread),
        returns (Q3, s1, s2).
        """
        # From cross law: (Q1 + Q2 - Q3)^2 = 4*Q1*Q2*(1 - s3)
        # Q3 = Q1 + Q2 - 2*sqrt(Q1*Q2*(1-s3))  or  + 2*sqrt(...)
        from .laws import solve_cross_law_for_quadrance
        Q3_solutions = solve_cross_law_for_quadrance(Q1, Q2, s3)
        if not Q3_solutions:
            raise GeometryError("No valid triangle for given QSQ")
        # Take the solution that gives a valid triangle (positive quadrance)
        Q3 = Q3_solutions[0]
        s1 = solve_cross_law_for_spread(Q2, Q3, Q1)
        s2 = solve_cross_law_for_spread(Q1, Q3, Q2)
        return (Q3, s1, s2)

    def __repr__(self) -> str:
        return (f"RatTriangle(A={self.A}, B={self.B}, C={self.C}, "
                f"Q=({self.Q_a}, {self.Q_b}, {self.Q_c}), "
                f"s=({self.s_A}, {self.s_B}, {self.s_C}))")
