"""Geometric constructions — perpendicular, parallel, circumcenter, etc.

All constructions are exact rational. No approximation.
"""

from __future__ import annotations

from cuneiform.core.rational import SexaRational
from .point import RatPoint
from .line import RatLine, GeometryError
from .quadrance import Quadrance


def perpendicular_through(line: RatLine, point: RatPoint) -> RatLine:
    """Exact perpendicular to line through point.

    If line is ax + by + c = 0, perpendicular direction is (a, b)
    so perpendicular line is bx - ay + d = 0 passing through point.
    d = -(b*px - a*py) = a*py - b*px
    """
    a_new = line.b
    b_new = -line.a
    c_new = line.a * point.y - line.b * point.x
    return RatLine(a_new, b_new, c_new)


def parallel_through(line: RatLine, point: RatPoint) -> RatLine:
    """Exact parallel to line through point.

    Same direction (a, b), different offset: ax + by + c' = 0
    c' = -(a*px + b*py)
    """
    c_new = -(line.a * point.x + line.b * point.y)
    return RatLine(line.a, line.b, c_new)


def foot_of_perpendicular(line: RatLine, point: RatPoint) -> RatPoint:
    """Exact foot of perpendicular from point to line.

    This is the intersection of line with perpendicular_through(line, point).
    """
    perp = perpendicular_through(line, point)
    return line.intersection(perp)


def midpoint(A: RatPoint, B: RatPoint) -> RatPoint:
    """Exact midpoint. Trivially rational."""
    return A.midpoint(B)


def perpendicular_bisector(A: RatPoint, B: RatPoint) -> RatLine:
    """Perpendicular bisector of segment AB.

    Passes through midpoint of AB, perpendicular to AB.
    """
    mid = midpoint(A, B)
    ab = RatLine.through_points(A, B)
    return perpendicular_through(ab, mid)


def circumcenter(A: RatPoint, B: RatPoint, C: RatPoint) -> RatPoint:
    """Exact circumcenter of triangle. Always rational for rational vertices.

    Intersection of perpendicular bisectors of any two sides.
    """
    pb_ab = perpendicular_bisector(A, B)
    pb_ac = perpendicular_bisector(A, C)
    return pb_ab.intersection(pb_ac)


def circumquadrance(A: RatPoint, B: RatPoint, C: RatPoint) -> Quadrance:
    """Circumquadrance (circumradius squared) of triangle ABC."""
    O = circumcenter(A, B, C)
    return Quadrance.between(O, A)


def reflect_point(point: RatPoint, line: RatLine) -> RatPoint:
    """Exact reflection of point across line.

    Reflection = 2 * foot_of_perpendicular - point
    """
    foot = foot_of_perpendicular(line, point)
    rx = SexaRational(2) * foot.x - point.x
    ry = SexaRational(2) * foot.y - point.y
    return RatPoint(rx, ry)


def altitude_foot(A: RatPoint, B: RatPoint, C: RatPoint) -> RatPoint:
    """Foot of altitude from A to line BC."""
    bc = RatLine.through_points(B, C)
    return foot_of_perpendicular(bc, A)


def orthocenter(A: RatPoint, B: RatPoint, C: RatPoint) -> RatPoint:
    """Exact orthocenter. Rational for rational vertices.

    Intersection of two altitudes.
    """
    bc = RatLine.through_points(B, C)
    ac = RatLine.through_points(A, C)
    alt_a = perpendicular_through(bc, A)
    alt_b = perpendicular_through(ac, B)
    return alt_a.intersection(alt_b)


def centroid(A: RatPoint, B: RatPoint, C: RatPoint) -> RatPoint:
    """Exact centroid (intersection of medians)."""
    return RatPoint(
        (A.x + B.x + C.x) / SexaRational(3),
        (A.y + B.y + C.y) / SexaRational(3),
    )


def quadrance_to_line(point: RatPoint, line: RatLine) -> Quadrance:
    """Quadrance (squared distance) from point to line.

    Q = (ax + by + c)^2 / (a^2 + b^2)
    """
    num = (line.a * point.x + line.b * point.y + line.c) ** 2
    denom = line.a ** 2 + line.b ** 2
    return Quadrance(num / denom)
