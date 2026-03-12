"""Quadrance — rational replacement for distance.

Quadrance = (distance)². Always rational for rational points.
We measure area-of-squares instead of length-of-sides: same
information, no irrationals.
"""

from __future__ import annotations

from functools import total_ordering

from cuneiform.core.rational import SexaRational
from .point import RatPoint


@total_ordering
class Quadrance:
    """Quadrance between two points = (distance)².

    Q(A, B) = (x_b - x_a)² + (y_b - y_a)²

    Comparison still works: Q(A,B) < Q(A,C) iff d(A,B) < d(A,C).
    """

    __slots__ = ("value",)

    def __init__(self, value: SexaRational | int):
        if isinstance(value, int):
            value = SexaRational(value)
        self.value = value

    @classmethod
    def between(cls, p1: RatPoint, p2: RatPoint) -> Quadrance:
        """Compute quadrance between two rational points."""
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        return cls(dx * dx + dy * dy)

    def is_zero(self) -> bool:
        return self.value == SexaRational(0)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Quadrance):
            return self.value == other.value
        return NotImplemented

    def __lt__(self, other: Quadrance) -> bool:
        return self.value < other.value

    def __hash__(self) -> int:
        return hash(self.value)

    def __add__(self, other: Quadrance) -> Quadrance:
        return Quadrance(self.value + other.value)

    def __sub__(self, other: Quadrance) -> Quadrance:
        return Quadrance(self.value - other.value)

    def __repr__(self) -> str:
        return f"Q({self.value})"
