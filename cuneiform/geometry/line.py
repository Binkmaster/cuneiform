"""RatLine — exact rational line equations ax + by + c = 0."""

from __future__ import annotations

from fractions import Fraction
from math import gcd

from cuneiform.core.rational import SexaRational
from .point import RatPoint


class GeometryError(Exception):
    """Raised for degenerate geometric configurations."""
    pass


class RatLine:
    """A line ax + by + c = 0 with exact rational coefficients.

    Stored in canonical form with integer coefficients, gcd(|a|,|b|,|c|) = 1,
    and leading coefficient positive.
    """

    __slots__ = ("a", "b", "c")

    def __init__(self, a: SexaRational | int, b: SexaRational | int,
                 c: SexaRational | int):
        a = a if isinstance(a, SexaRational) else SexaRational(a)
        b = b if isinstance(b, SexaRational) else SexaRational(b)
        c = c if isinstance(c, SexaRational) else SexaRational(c)
        if a == SexaRational(0) and b == SexaRational(0):
            raise GeometryError("Line coefficients a and b cannot both be zero")
        self.a = a
        self.b = b
        self.c = c

    @classmethod
    def through_points(cls, p1: RatPoint, p2: RatPoint) -> RatLine:
        """Line through two rational points. Always exact."""
        if p1 == p2:
            raise GeometryError("Cannot define a line through a single point")
        a = p1.y - p2.y
        b = p2.x - p1.x
        c = p1.x * p2.y - p2.x * p1.y
        return cls(a, b, c)

    @classmethod
    def with_slope_through(cls, slope: SexaRational | int,
                           point: RatPoint) -> RatLine:
        """Line with rational slope through rational point.

        y - y0 = m(x - x0) => mx - y + (y0 - m*x0) = 0
        """
        slope = slope if isinstance(slope, SexaRational) else SexaRational(slope)
        a = slope
        b = SexaRational(-1)
        c = point.y - slope * point.x
        return cls(a, b, c)

    def intersection(self, other: RatLine) -> RatPoint:
        """Exact intersection point. Raises GeometryError if parallel."""
        det = self.a * other.b - other.a * self.b
        if det == SexaRational(0):
            raise GeometryError("Lines are parallel — no intersection")
        x = (self.b * other.c - other.b * self.c) / det
        y = (other.a * self.c - self.a * other.c) / det
        return RatPoint(x, y)

    def is_parallel(self, other: RatLine) -> bool:
        """Two lines are parallel iff their normal vectors are proportional."""
        return (self.a * other.b - other.a * self.b) == SexaRational(0)

    def is_perpendicular(self, other: RatLine) -> bool:
        """Perpendicularity via dot product of direction vectors = 0."""
        return (self.a * other.a + self.b * other.b) == SexaRational(0)

    def contains(self, point: RatPoint) -> bool:
        """Test if point lies on this line. Exact."""
        return (self.a * point.x + self.b * point.y + self.c) == SexaRational(0)

    def quadrance_norm(self) -> SexaRational:
        """a² + b² — the quadrance of the normal vector.

        Used in spread computation.
        """
        return self.a * self.a + self.b * self.b

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RatLine):
            return NotImplemented
        # Two lines are equal if one is a scalar multiple of the other
        # a1*b2 == a2*b1 and a1*c2 == a2*c1 and b1*c2 == b2*c1
        return (self.a * other.b == other.a * self.b and
                self.a * other.c == other.a * self.c and
                self.b * other.c == other.b * self.c)

    def __repr__(self) -> str:
        return f"RatLine({self.a}x + {self.b}y + {self.c} = 0)"
