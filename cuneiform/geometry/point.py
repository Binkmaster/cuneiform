"""RatPoint — exact rational coordinates in 2D."""

from __future__ import annotations

from fractions import Fraction

from cuneiform.core.rational import SexaRational


class RatPoint:
    """A point in 2D with exact SexaRational coordinates.

    No floats. No approximation. Ever.
    """

    __slots__ = ("x", "y")

    def __init__(self, x: SexaRational | int, y: SexaRational | int):
        self.x = x if isinstance(x, SexaRational) else SexaRational(x)
        self.y = y if isinstance(y, SexaRational) else SexaRational(y)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RatPoint):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def __repr__(self) -> str:
        return f"RatPoint({self.x}, {self.y})"

    def __str__(self) -> str:
        return f"({self.x}, {self.y})"

    def collinear(self, b: RatPoint, c: RatPoint) -> bool:
        """Test collinearity using exact rational arithmetic.

        Three points are collinear iff the signed area determinant is zero:
        | x_a  y_a  1 |
        | x_b  y_b  1 | = 0
        | x_c  y_c  1 |
        """
        det = (self.x * (b.y - c.y) +
               b.x * (c.y - self.y) +
               c.x * (self.y - b.y))
        return det == SexaRational(0)

    def midpoint(self, other: RatPoint) -> RatPoint:
        """Exact midpoint. Always rational."""
        return RatPoint(
            (self.x + other.x) / SexaRational(2),
            (self.y + other.y) / SexaRational(2),
        )
