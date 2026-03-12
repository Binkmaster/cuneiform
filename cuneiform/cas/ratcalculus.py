"""Wildberger's algebraic calculus — derivatives without limits.

The derivative of a polynomial is a purely algebraic operation.
No epsilon-delta. No infinity. No real numbers. It works over any field,
including the sexagesimal rationals.
"""

from __future__ import annotations

from cuneiform.core.rational import SexaRational
from .ratpoly import RatPoly


class AlgebraicDerivative:
    """Algebraic differentiation and integration of polynomials.

    Wraps RatPoly with a calculus-oriented API. All operations are
    purely algebraic — no limits, no infinitesimals.
    """

    __slots__ = ("poly",)

    def __init__(self, coefficients: list[SexaRational | int] | RatPoly):
        if isinstance(coefficients, RatPoly):
            self.poly = coefficients
        else:
            self.poly = RatPoly(coefficients)

    @property
    def coeffs(self) -> list[SexaRational]:
        return self.poly.coeffs

    @property
    def degree(self) -> int:
        return self.poly.degree

    def derivative(self, order: int = 1) -> AlgebraicDerivative:
        """Algebraic derivative. Iterable for higher orders."""
        result = self.poly
        for _ in range(order):
            result = result.derivative()
        return AlgebraicDerivative(result)

    def antiderivative(self, constant: SexaRational | int = 0) -> AlgebraicDerivative:
        """Algebraic antiderivative with explicit constant.

        No '+C'. If you want a constant, provide it explicitly.
        This is the algebraic philosophy: be explicit about everything.
        """
        return AlgebraicDerivative(self.poly.antiderivative(constant))

    def evaluate(self, x: SexaRational | int) -> SexaRational:
        """Evaluate at a rational point. Exact."""
        return self.poly.evaluate(x)

    def definite_integral(self, a: SexaRational | int,
                          b: SexaRational | int) -> SexaRational:
        """Definite integral from a to b.

        Computed as F(b) - F(a) where F is the antiderivative.
        Purely algebraic. Exact. No Riemann sums. No limits.
        """
        F = self.poly.antiderivative()
        return F.evaluate(b) - F.evaluate(a)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, AlgebraicDerivative):
            return self.poly == other.poly
        return NotImplemented

    def __repr__(self) -> str:
        return f"AlgebraicDerivative({self.poly})"


class RationalTaylorSeries:
    """Taylor expansion as a FINITE polynomial approximation.

    Classical Taylor series: infinite sum, convergence questions.
    CUNEIFORM Taylor: compute N terms as a polynomial over SexaRational.
    The result is FINITE and EXACT — a known polynomial approximation.

    All derivatives must be provided as exact SexaRationals.
    For transcendental functions, this means you're working with
    rational APPROXIMATIONS to the derivatives — which CUNEIFORM
    makes explicit rather than hiding.
    """

    __slots__ = ("_derivatives", "_center", "_terms", "_poly")

    def __init__(self, function_derivatives: list[SexaRational | int],
                 center: SexaRational | int = 0,
                 terms: int | None = None):
        """
        function_derivatives: [f(a), f'(a), f''(a), ...] at the center.
        center: the expansion point a.
        terms: how many terms to use (default: all provided derivatives).
        """
        self._derivatives = [
            d if isinstance(d, SexaRational) else SexaRational(d)
            for d in function_derivatives
        ]
        self._center = center if isinstance(center, SexaRational) else SexaRational(center)
        self._terms = terms if terms is not None else len(self._derivatives)
        self._terms = min(self._terms, len(self._derivatives))
        self._poly = self._build_polynomial()

    def _build_polynomial(self) -> RatPoly:
        """Build the Taylor polynomial.

        T_n(x) = sum_{k=0}^{n-1} f^(k)(a)/k! * (x-a)^k
        """
        # Build (x - a) as a polynomial
        x_minus_a = RatPoly([-self._center, SexaRational(1)])

        result = RatPoly()
        factorial = SexaRational(1)
        power = RatPoly([SexaRational(1)])  # (x-a)^0 = 1

        for k in range(self._terms):
            if k > 0:
                factorial = factorial * SexaRational(k)
            coeff = self._derivatives[k] / factorial
            result = result + power.scale(coeff)
            power = power * x_minus_a

        return result

    @property
    def polynomial(self) -> RatPoly:
        """The Taylor polynomial as an exact rational polynomial."""
        return self._poly

    def evaluate(self, x: SexaRational | int) -> SexaRational:
        """Evaluate the Taylor polynomial at x."""
        return self._poly.evaluate(x)

    def error_bound(self, x: SexaRational | int,
                    max_next_derivative: SexaRational | int) -> SexaRational:
        """Lagrange remainder bound: |R_n(x)| <= M |x-a|^n / n!

        max_next_derivative: bound M on |f^(n)(t)| for t between a and x.
        This must be provided by the user — CUNEIFORM doesn't guess.
        """
        if isinstance(x, int):
            x = SexaRational(x)
        if isinstance(max_next_derivative, int):
            max_next_derivative = SexaRational(max_next_derivative)

        n = self._terms
        diff = x - self._center
        if diff < SexaRational(0):
            diff = SexaRational(0) - diff

        power = diff ** n
        factorial = SexaRational(1)
        for k in range(1, n + 1):
            factorial = factorial * SexaRational(k)

        return max_next_derivative * power / factorial

    def __repr__(self) -> str:
        return (f"RationalTaylorSeries(center={self._center}, "
                f"terms={self._terms}, poly={self._poly})")
