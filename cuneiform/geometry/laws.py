"""The Five Fundamental Laws of Rational Trigonometry.
(Wildberger, "Divine Proportions", 2005)

These replace Pythagorean theorem, law of sines, law of cosines, and
angle sum = 180. Every law operates ONLY on rational quantities.
No irrationals. No transcendentals. No approximation.
"""

from __future__ import annotations

from fractions import Fraction

from cuneiform.core.rational import SexaRational
from .quadrance import Quadrance
from .spread import Spread
from .line import GeometryError


# ---- Verification functions (check if a law holds) ----

def verify_triple_quad(Q1: Quadrance, Q2: Quadrance, Q3: Quadrance) -> bool:
    """TRIPLE QUAD FORMULA — Tests collinearity.

    Three points A1, A2, A3 are collinear if and only if:
    (Q1 + Q2 + Q3)^2 = 2(Q1^2 + Q2^2 + Q3^2)

    where Q1 = Q(A2,A3), Q2 = Q(A1,A3), Q3 = Q(A1,A2).
    """
    s = Q1.value + Q2.value + Q3.value
    lhs = s * s
    rhs = SexaRational(2) * (Q1.value ** 2 + Q2.value ** 2 + Q3.value ** 2)
    return lhs == rhs


def verify_pythagoras(Q1: Quadrance, Q2: Quadrance, Q3: Quadrance,
                      s: Spread) -> bool:
    """PYTHAGORAS' THEOREM (Rational form).

    If s = 1 (perpendicular), then Q1 + Q2 = Q3
    (where Q3 is the quadrance opposite the right spread).
    """
    if s.value != SexaRational(1):
        return False
    return Q1.value + Q2.value == Q3.value


def verify_spread_law(s1: Spread, Q1: Quadrance,
                      s2: Spread, Q2: Quadrance) -> bool:
    """SPREAD LAW — Rational analog of the Law of Sines.

    s1/Q1 = s2/Q2  =>  s1 * Q2 = s2 * Q1
    """
    return s1.value * Q2.value == s2.value * Q1.value


def verify_cross_law(Q1: Quadrance, Q2: Quadrance, Q3: Quadrance,
                     s3: Spread) -> bool:
    """CROSS LAW — Rational analog of the Law of Cosines.

    (Q1 + Q2 - Q3)^2 = 4 * Q1 * Q2 * (1 - s3)

    where s3 is the spread opposite Q3.
    """
    lhs = (Q1.value + Q2.value - Q3.value) ** 2
    rhs = SexaRational(4) * Q1.value * Q2.value * (SexaRational(1) - s3.value)
    return lhs == rhs


def verify_triple_spread(s1: Spread, s2: Spread, s3: Spread) -> bool:
    """TRIPLE SPREAD FORMULA — Rational analog of "angles sum to 180 degrees".

    (s1 + s2 + s3)^2 = 2(s1^2 + s2^2 + s3^2) + 4*s1*s2*s3
    """
    s_sum = s1.value + s2.value + s3.value
    lhs = s_sum * s_sum
    rhs = (SexaRational(2) * (s1.value ** 2 + s2.value ** 2 + s3.value ** 2) +
           SexaRational(4) * s1.value * s2.value * s3.value)
    return lhs == rhs


# ---- Solver functions (derive unknowns from knowns) ----

def solve_cross_law_for_spread(Q1: Quadrance, Q2: Quadrance,
                               Q3: Quadrance) -> Spread:
    """Given three quadrances, compute the spread opposite Q3.

    s3 = 1 - (Q1 + Q2 - Q3)^2 / (4 * Q1 * Q2)
    """
    if Q1.value == SexaRational(0) or Q2.value == SexaRational(0):
        raise GeometryError("Cannot compute spread with zero quadrance")
    num = (Q1.value + Q2.value - Q3.value) ** 2
    denom = SexaRational(4) * Q1.value * Q2.value
    s = SexaRational(1) - num / denom
    return Spread(s)


def solve_spread_law(s1: Spread, Q1: Quadrance,
                     Q2: Quadrance) -> Spread:
    """Given s1, Q1, and Q2, find s2.

    s1/Q1 = s2/Q2  =>  s2 = s1 * Q2 / Q1
    """
    if Q1.value == SexaRational(0):
        raise GeometryError("Cannot solve spread law with zero quadrance")
    return Spread(s1.value * Q2.value / Q1.value)


def solve_cross_law_for_quadrance(Q1: Quadrance, Q2: Quadrance,
                                  s3: Spread) -> list[Quadrance]:
    """Given two quadrances and the opposite spread, find Q3.

    (Q1 + Q2 - Q3)^2 = 4*Q1*Q2*(1 - s3)
    Let k = 4*Q1*Q2*(1 - s3)
    Q3 = Q1 + Q2 -/+ sqrt(k)

    sqrt(k) must be rational for exact solution.
    Returns up to 2 solutions.
    """
    k = SexaRational(4) * Q1.value * Q2.value * (SexaRational(1) - s3.value)

    sqrt_k = _exact_rational_sqrt(k)
    if sqrt_k is None:
        raise GeometryError(
            "No exact rational solution — the square root is irrational. "
            "Triangle is not constructible in the rational framework."
        )

    base = Q1.value + Q2.value
    solutions = []
    for sign_sqrt in [sqrt_k, -sqrt_k]:
        val = base - sign_sqrt
        if val >= SexaRational(0):
            solutions.append(Quadrance(val))
    return solutions


def solve_triple_spread(s1: Spread, s2: Spread) -> list[Spread]:
    """Given two spreads of a triangle, find the third.

    (s1 + s2 + s3)^2 = 2(s1^2 + s2^2 + s3^2) + 4*s1*s2*s3

    Expanding and collecting in s3:
    s3^2 - 2(s1 + s2)*s3 + (s1 + s2)^2
        = 2*s1^2 + 2*s2^2 + 2*s3^2 + 4*s1*s2*s3

    Rearranging:
    s3^2(1 - 2) + s3(-2(s1+s2) - 4*s1*s2) + (s1+s2)^2 - 2*s1^2 - 2*s2^2 = 0
    -s3^2 + s3(-2(s1+s2) - 4*s1*s2) + 2*s1*s2 = 0 ... wait, let me redo.

    Let me expand carefully:
    (s1 + s2 + s3)^2 = s1^2 + s2^2 + s3^2 + 2*s1*s2 + 2*s1*s3 + 2*s2*s3
    RHS = 2*s1^2 + 2*s2^2 + 2*s3^2 + 4*s1*s2*s3

    So: s1^2 + s2^2 + s3^2 + 2*s1*s2 + 2*s1*s3 + 2*s2*s3
      = 2*s1^2 + 2*s2^2 + 2*s3^2 + 4*s1*s2*s3

    Rearrange: 0 = s1^2 + s2^2 + s3^2 - 2*s1*s2 - 2*s1*s3 - 2*s2*s3 + 4*s1*s2*s3

    In s3: s3^2 + s3(-2*s1 - 2*s2 + 4*s1*s2) + (s1^2 + s2^2 - 2*s1*s2) = 0
    i.e.:  s3^2 + s3*(-2*(s1+s2) + 4*s1*s2) + (s1 - s2)^2 = 0

    Quadratic: A=1, B = -2(s1+s2) + 4*s1*s2, C = (s1-s2)^2
    """
    A = SexaRational(1)
    B = SexaRational(-2) * (s1.value + s2.value) + SexaRational(4) * s1.value * s2.value
    C = (s1.value - s2.value) ** 2

    discriminant = B * B - SexaRational(4) * A * C
    if discriminant < SexaRational(0):
        return []

    sqrt_disc = _exact_rational_sqrt(discriminant)
    if sqrt_disc is None:
        raise GeometryError("No exact rational solution for triple spread")

    solutions = []
    for sign in [SexaRational(1), SexaRational(-1)]:
        val = (-B + sign * sqrt_disc) / (SexaRational(2) * A)
        if SexaRational(0) <= val <= SexaRational(1):
            solutions.append(Spread(val))

    return solutions


def _exact_rational_sqrt(value: SexaRational) -> SexaRational | None:
    """Compute exact rational square root, or None if irrational.

    For value = p/q, sqrt = sqrt(p)/sqrt(q), both must be perfect squares.
    """
    if value < SexaRational(0):
        return None
    if value == SexaRational(0):
        return SexaRational(0)

    frac = value.as_fraction
    p, q = frac.numerator, frac.denominator

    sp = _isqrt_exact(p)
    sq = _isqrt_exact(q)
    if sp is None or sq is None:
        return None
    return SexaRational(sp, sq)


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
