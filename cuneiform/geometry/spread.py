"""Spread — rational replacement for angle.

Spread between two lines = (sin theta)². Always rational for rational lines.
  s = 0: parallel lines
  s = 1: perpendicular lines
  s = 1/2: 45 degrees (but we don't use angles)
  s = 1/4: 30 degrees
  s = 3/4: 60 degrees
"""

from __future__ import annotations

from functools import total_ordering

from cuneiform.core.rational import SexaRational
from .point import RatPoint
from .line import RatLine


@total_ordering
class Spread:
    """Spread between two lines = sin^2(theta).

    Spread doesn't distinguish supplementary angles (30 and 150 both have
    spread 1/4). This is a feature for practical geometry.
    """

    __slots__ = ("value",)

    def __init__(self, value: SexaRational | int):
        if isinstance(value, int):
            value = SexaRational(value)
        self.value = value

    @classmethod
    def between_lines(cls, l1: RatLine, l2: RatLine) -> Spread:
        """Compute spread between two lines. Always exact."""
        cross = l1.a * l2.b - l2.a * l1.b
        norm1 = l1.a * l1.a + l1.b * l1.b
        norm2 = l2.a * l2.a + l2.b * l2.b
        s = (cross * cross) / (norm1 * norm2)
        return cls(s)

    @classmethod
    def from_sides(cls, Q_opposite: "Quadrance",
                   Q_adj1: "Quadrance", Q_adj2: "Quadrance") -> Spread:
        """Compute spread from three quadrances using the Cross Law.

        The spread opposite Q_opposite in a triangle with quadrances
        Q_adj1, Q_adj2, Q_opposite:
        s = 1 - (Q_adj1 + Q_adj2 - Q_opposite)^2 / (4 * Q_adj1 * Q_adj2)
        """
        num = Q_adj1.value + Q_adj2.value - Q_opposite.value
        denom = SexaRational(4) * Q_adj1.value * Q_adj2.value
        s = SexaRational(1) - (num * num) / denom
        return cls(s)

    @classmethod
    def from_pythagorean_triple(cls, a: int, b: int, c: int) -> Spread:
        """Spread from a Pythagorean triple (a, b, c) where a^2 + b^2 = c^2.

        The spread at the vertex opposite side 'a' is a^2/c^2.
        Always exact. Always rational.
        """
        return cls(SexaRational(a * a, c * c))

    def is_right(self) -> bool:
        """Spread of 1 = perpendicular."""
        return self.value == SexaRational(1)

    def is_parallel(self) -> bool:
        """Spread of 0 = parallel."""
        return self.value == SexaRational(0)

    def classical_angle_approx(self) -> float:
        """Approximate angle in degrees. USES FLOATS — only for display."""
        import math
        return math.degrees(math.asin(math.sqrt(float(self.value))))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Spread):
            return self.value == other.value
        return NotImplemented

    def __lt__(self, other: Spread) -> bool:
        return self.value < other.value

    def __hash__(self) -> int:
        return hash(self.value)

    def __repr__(self) -> str:
        return f"s({self.value})"
