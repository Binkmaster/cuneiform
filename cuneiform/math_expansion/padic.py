"""p-adic connections to sexagesimal regularity.

The sexagesimal approach has kinship with p-adic numbers: in both,
"closeness" relates to divisibility rather than magnitude. A number
is "close to zero" in the p-adic world when it's highly divisible by p.
In CUNEIFORM, a number is "regular" when it's highly divisible by 2, 3, 5.

This module formalizes the connection between:
- 2-adic, 3-adic, and 5-adic valuations
- CUNEIFORM regularity classification
- Sexagesimal termination properties
"""

from __future__ import annotations

from fractions import Fraction


class PAdicValuation:
    """Compute p-adic valuations (how many times p divides n).

    The p-adic valuation v_p(n) is the exponent of p in the
    prime factorization of n. v_p(0) = infinity (represented as None).
    """

    def __init__(self, p: int):
        if p < 2:
            raise ValueError("p must be at least 2")
        self.p = p

    def __call__(self, n: int) -> int | None:
        """Compute v_p(n) — the p-adic valuation of n."""
        if n == 0:
            return None  # infinity
        n = abs(n)
        v = 0
        while n % self.p == 0:
            v += 1
            n //= self.p
        return v

    def of_fraction(self, f: Fraction) -> int | None:
        """v_p(a/b) = v_p(a) - v_p(b)."""
        va = self(f.numerator)
        vb = self(f.denominator)
        if va is None:
            return None
        if vb is None:
            return None  # shouldn't happen for valid Fraction
        return va - vb

    def padic_norm(self, n: int) -> Fraction:
        """|n|_p = p^(-v_p(n))."""
        v = self(n)
        if v is None:
            return Fraction(0)
        return Fraction(1, self.p ** v)

    def is_padic_integer(self, f: Fraction) -> bool:
        """f is a p-adic integer iff v_p(f) >= 0."""
        v = self.of_fraction(f)
        return v is not None and v >= 0


class Sexa5AdicConnection:
    """The 5-adic (actually (2,3,5)-adic) connection to sexagesimal regularity.

    A fraction a/b terminates in base 60 iff b is 5-smooth (only
    factors 2, 3, 5). This is equivalent to saying:

    For ALL primes p > 5: v_p(b) = 0

    Or equivalently: the fraction is simultaneously a p-adic integer
    for all primes p > 5.

    This gives a p-adic characterization of sexagesimal regularity.
    """

    def __init__(self):
        self.v2 = PAdicValuation(2)
        self.v3 = PAdicValuation(3)
        self.v5 = PAdicValuation(5)

    def regularity_vector(self, n: int) -> tuple[int | None, int | None, int | None]:
        """The (2,3,5)-adic valuation vector of n.

        This is the fundamental invariant in CUNEIFORM's framework.
        A number n is regular iff its cofactor (after removing 2,3,5)
        is 1 — which means these three valuations completely determine n.
        """
        return (self.v2(n), self.v3(n), self.v5(n))

    def sexa_distance(self, a: int, b: int) -> Fraction:
        """Sexagesimal distance between a and b.

        Defined as: d_60(a,b) = max(|a-b|_2, |a-b|_3, |a-b|_5)

        Two numbers are "close" in sexagesimal sense when their
        difference is highly divisible by 2, 3, and 5 simultaneously.
        This is the natural ultrametric for the sexagesimal world.
        """
        diff = abs(a - b)
        if diff == 0:
            return Fraction(0)
        norms = [
            self.v2.padic_norm(diff),
            self.v3.padic_norm(diff),
            self.v5.padic_norm(diff),
        ]
        return max(norms)

    def termination_criterion(self, f: Fraction) -> dict:
        """Analyze whether f terminates in base 60 using p-adic theory.

        f = a/b terminates in base 60 iff for all primes p > 5,
        v_p(b) = 0. Equivalently, b is 5-smooth.
        """
        denom = f.denominator
        # Check smoothness via p-adic valuations
        remaining = denom
        for p in (2, 3, 5):
            while remaining % p == 0:
                remaining //= p

        terminates = remaining == 1

        return {
            "fraction": f,
            "denominator": denom,
            "v2_denom": self.v2(denom),
            "v3_denom": self.v3(denom),
            "v5_denom": self.v5(denom),
            "cofactor": remaining,
            "terminates_base_60": terminates,
            "padic_reason": (
                "All prime valuations of denominator are in {2,3,5}"
                if terminates else
                f"Denominator has prime factor(s) > 5 (cofactor={remaining})"
            ),
        }

    def regularity_spectrum(self, n: int) -> dict:
        """Full p-adic spectrum analysis of n.

        Shows how n looks from the perspective of each small prime,
        connecting CUNEIFORM regularity to the broader p-adic world.
        """
        primes = [2, 3, 5, 7, 11, 13]
        vals = {}
        for p in primes:
            v = PAdicValuation(p)
            vals[p] = {
                "valuation": v(n),
                "norm": float(v.padic_norm(n)),
                "in_smooth_group": p <= 5,
            }

        # Regularity = looking only at primes 2,3,5
        cofactor = n
        for p in (2, 3, 5):
            while cofactor % p == 0:
                cofactor //= p

        return {
            "n": n,
            "valuations": vals,
            "is_regular": cofactor == 1,
            "cofactor": cofactor,
            "regularity_vector": self.regularity_vector(n),
        }
