"""Polynomials over sexagesimal rationals.

Exact polynomial arithmetic: add, subtract, multiply, divide with remainder,
GCD, evaluation, composition. No floating point. No approximation.
"""

from __future__ import annotations

from fractions import Fraction
from math import gcd as _gcd

from cuneiform.core.rational import SexaRational


class RatPoly:
    """A polynomial with SexaRational coefficients.

    Coefficients are stored least-significant first:
    coeffs[i] is the coefficient of x^i.

    The zero polynomial has coeffs = [SexaRational(0)].
    """

    __slots__ = ("coeffs",)

    def __init__(self, coeffs: list[SexaRational | int | Fraction] | None = None):
        if coeffs is None or len(coeffs) == 0:
            self.coeffs = [SexaRational(0)]
        else:
            self.coeffs = [
                c if isinstance(c, SexaRational) else SexaRational(c)
                for c in coeffs
            ]
        self._strip()

    def _strip(self):
        """Remove trailing zero coefficients (but keep at least one)."""
        while len(self.coeffs) > 1 and self.coeffs[-1] == SexaRational(0):
            self.coeffs.pop()

    @classmethod
    def from_roots(cls, roots: list[SexaRational | int]) -> RatPoly:
        """Build polynomial from its roots: (x - r1)(x - r2)..."""
        result = cls([SexaRational(1)])
        for r in roots:
            r = r if isinstance(r, SexaRational) else SexaRational(r)
            # Multiply by (x - r)
            result = result * cls([SexaRational(0) - r, SexaRational(1)])
        return result

    @classmethod
    def monomial(cls, degree: int, coeff: SexaRational | int = 1) -> RatPoly:
        """Create a monomial: coeff * x^degree."""
        c = coeff if isinstance(coeff, SexaRational) else SexaRational(coeff)
        coeffs = [SexaRational(0)] * degree + [c]
        return cls(coeffs)

    @property
    def degree(self) -> int:
        """Degree of the polynomial. Zero polynomial has degree 0."""
        return len(self.coeffs) - 1

    @property
    def is_zero(self) -> bool:
        return len(self.coeffs) == 1 and self.coeffs[0] == SexaRational(0)

    @property
    def leading_coefficient(self) -> SexaRational:
        return self.coeffs[-1]

    def evaluate(self, x: SexaRational | int) -> SexaRational:
        """Evaluate polynomial at x using Horner's method. Exact."""
        if isinstance(x, int):
            x = SexaRational(x)
        result = SexaRational(0)
        for c in reversed(self.coeffs):
            result = result * x + c
        return result

    def __call__(self, x: SexaRational | int) -> SexaRational:
        return self.evaluate(x)

    def __add__(self, other: RatPoly) -> RatPoly:
        n = max(len(self.coeffs), len(other.coeffs))
        result = []
        for i in range(n):
            a = self.coeffs[i] if i < len(self.coeffs) else SexaRational(0)
            b = other.coeffs[i] if i < len(other.coeffs) else SexaRational(0)
            result.append(a + b)
        return RatPoly(result)

    def __sub__(self, other: RatPoly) -> RatPoly:
        n = max(len(self.coeffs), len(other.coeffs))
        result = []
        for i in range(n):
            a = self.coeffs[i] if i < len(self.coeffs) else SexaRational(0)
            b = other.coeffs[i] if i < len(other.coeffs) else SexaRational(0)
            result.append(a - b)
        return RatPoly(result)

    def __mul__(self, other: RatPoly) -> RatPoly:
        if self.is_zero or other.is_zero:
            return RatPoly()
        n = len(self.coeffs) + len(other.coeffs) - 1
        result = [SexaRational(0)] * n
        for i, a in enumerate(self.coeffs):
            for j, b in enumerate(other.coeffs):
                result[i + j] = result[i + j] + a * b
        return RatPoly(result)

    def __neg__(self) -> RatPoly:
        return RatPoly([-c for c in self.coeffs])

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RatPoly):
            return NotImplemented
        return self.coeffs == other.coeffs

    def __hash__(self) -> int:
        return hash(tuple(self.coeffs))

    def scale(self, s: SexaRational | int) -> RatPoly:
        """Multiply all coefficients by scalar s."""
        if isinstance(s, int):
            s = SexaRational(s)
        return RatPoly([c * s for c in self.coeffs])

    def divmod(self, other: RatPoly) -> tuple[RatPoly, RatPoly]:
        """Polynomial division with remainder.

        Returns (quotient, remainder) such that self = quotient * other + remainder
        and degree(remainder) < degree(other).
        """
        if other.is_zero:
            raise ZeroDivisionError("Polynomial division by zero")

        remainder = list(self.coeffs)
        divisor = other.coeffs
        deg_d = len(divisor) - 1
        deg_r = len(remainder) - 1

        if deg_r < deg_d:
            return RatPoly(), RatPoly(remainder)

        quotient = [SexaRational(0)] * (deg_r - deg_d + 1)
        lead_inv = SexaRational(1) / divisor[-1]

        for i in range(deg_r - deg_d, -1, -1):
            if len(remainder) - 1 < i + deg_d:
                continue
            coeff = remainder[i + deg_d] * lead_inv
            quotient[i] = coeff
            for j in range(deg_d + 1):
                remainder[i + j] = remainder[i + j] - coeff * divisor[j]

        return RatPoly(quotient), RatPoly(remainder)

    def __floordiv__(self, other: RatPoly) -> RatPoly:
        q, _ = self.divmod(other)
        return q

    def __mod__(self, other: RatPoly) -> RatPoly:
        _, r = self.divmod(other)
        return r

    def gcd(self, other: RatPoly) -> RatPoly:
        """GCD via Euclidean algorithm. Result is monic (leading coeff = 1)."""
        a, b = self, other
        while not b.is_zero:
            _, r = a.divmod(b)
            a, b = b, r
        # Make monic
        if not a.is_zero:
            lc = a.leading_coefficient
            a = a.scale(SexaRational(1) / lc)
        return a

    def derivative(self) -> RatPoly:
        """Algebraic derivative. Purely formal — no limits needed."""
        if len(self.coeffs) <= 1:
            return RatPoly()
        new_coeffs = [
            SexaRational(i) * self.coeffs[i]
            for i in range(1, len(self.coeffs))
        ]
        return RatPoly(new_coeffs)

    def antiderivative(self, constant: SexaRational | int = 0) -> RatPoly:
        """Algebraic antiderivative with explicit constant term."""
        c0 = constant if isinstance(constant, SexaRational) else SexaRational(constant)
        new_coeffs = [c0]
        for i, c in enumerate(self.coeffs):
            new_coeffs.append(c / SexaRational(i + 1))
        return RatPoly(new_coeffs)

    def compose(self, other: RatPoly) -> RatPoly:
        """Compute self(other(x)) — polynomial composition."""
        result = RatPoly()
        power = RatPoly([SexaRational(1)])
        for c in self.coeffs:
            result = result + power.scale(c)
            power = power * other
        return result

    def rational_roots(self) -> list[SexaRational]:
        """Find all rational roots using the rational root theorem.

        For polynomial a_n x^n + ... + a_0, any rational root p/q
        (in lowest terms) has p | a_0 and q | a_n.
        """
        if self.is_zero:
            return []

        a0 = self.coeffs[0].as_fraction
        an = self.leading_coefficient.as_fraction

        if a0 == Fraction(0):
            # 0 is a root; factor it out and recurse
            roots = [SexaRational(0)]
            # Find multiplicity
            reduced = self
            while not reduced.is_zero and reduced.coeffs[0] == SexaRational(0):
                # Shift coefficients down (divide by x)
                reduced = RatPoly(reduced.coeffs[1:])
            roots.extend(reduced.rational_roots())
            return roots

        # Divisors of |a0.numerator| / divisors of |an.numerator|
        p_divs = _divisors(abs(a0.numerator))
        q_divs = _divisors(abs(an.numerator))

        # Also account for denominators
        p_divs_den = _divisors(abs(a0.denominator)) if a0.denominator != 1 else {1}
        q_divs_den = _divisors(abs(an.denominator)) if an.denominator != 1 else {1}

        candidates = set()
        for p in p_divs:
            for q in q_divs:
                for pd in p_divs_den:
                    for qd in q_divs_den:
                        # candidate = (p * qd) / (q * pd)
                        num = p * qd
                        den = q * pd
                        candidates.add(Fraction(num, den))
                        candidates.add(Fraction(-num, den))

        roots = []
        for c in candidates:
            sr = SexaRational(c)
            if self.evaluate(sr) == SexaRational(0):
                roots.append(sr)

        return sorted(roots, key=lambda r: float(r))

    def __repr__(self) -> str:
        if self.is_zero:
            return "RatPoly(0)"
        terms = []
        for i, c in enumerate(self.coeffs):
            if c == SexaRational(0):
                continue
            if i == 0:
                terms.append(str(c))
            elif i == 1:
                if c == SexaRational(1):
                    terms.append("x")
                elif c == SexaRational(-1):
                    terms.append("-x")
                else:
                    terms.append(f"{c}*x")
            else:
                if c == SexaRational(1):
                    terms.append(f"x^{i}")
                elif c == SexaRational(-1):
                    terms.append(f"-x^{i}")
                else:
                    terms.append(f"{c}*x^{i}")
        return "RatPoly(" + " + ".join(terms) + ")" if terms else "RatPoly(0)"


def _divisors(n: int) -> set[int]:
    """All positive divisors of n."""
    if n == 0:
        return {1}
    n = abs(n)
    divs = set()
    for i in range(1, int(n**0.5) + 1):
        if n % i == 0:
            divs.add(i)
            divs.add(n // i)
    return divs
