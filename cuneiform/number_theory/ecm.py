"""Elliptic Curve Method — standard and Plimpton-derived curve selection.

ECM (Lenstra 1987) finds factors by computing n!*P on random elliptic curves
mod n. CUNEIFORM's variant: select curves using Plimpton 322 triples.
"""

from __future__ import annotations

from math import gcd, isqrt, log
import random

from .primes import sieve_of_eratosthenes


def _ec_add(P: tuple, Q: tuple, a: int, n: int) -> tuple | None:
    """Add two points on y^2 = x^3 + ax + b (mod n).

    Returns None if we found a factor of n (gcd hit).
    Returns (0, 0) for point at infinity.
    """
    if P == (0, 0):
        return Q
    if Q == (0, 0):
        return P

    x1, y1 = P
    x2, y2 = Q

    if x1 == x2:
        if (y1 + y2) % n == 0:
            return (0, 0)  # point at infinity
        # Doubling
        denom = (2 * y1) % n
        g = gcd(denom, n)
        if 1 < g < n:
            return None  # Found factor!
        if g == n:
            return (0, 0)
        inv = pow(denom, -1, n)
        lam = ((3 * x1 * x1 + a) * inv) % n
    else:
        denom = (x2 - x1) % n
        g = gcd(denom, n)
        if 1 < g < n:
            return None  # Found factor!
        if g == n:
            return (0, 0)
        inv = pow(denom, -1, n)
        lam = ((y2 - y1) * inv) % n

    x3 = (lam * lam - x1 - x2) % n
    y3 = (lam * (x1 - x3) - y1) % n
    return (x3, y3)


def _ec_mul(k: int, P: tuple, a: int, n: int) -> tuple | int:
    """Scalar multiplication k*P on curve y^2 = x^3 + ax + b (mod n).

    Returns point, or integer factor if found.
    """
    if k == 0:
        return (0, 0)

    result = (0, 0)  # identity
    current = P

    while k > 0:
        if k & 1:
            result = _ec_add(result, current, a, n)
            if result is None:
                return None  # Signal factor found
        current = _ec_add(current, current, a, n)
        if current is None:
            return None
        k >>= 1

    return result


class ECM:
    """Standard Elliptic Curve Method for factoring."""

    def __init__(self, n: int, B1: int | None = None, B2: int | None = None,
                 curves: int = 20):
        self.n = n
        self.B1 = B1 or self._default_B1(n)
        self.B2 = B2 or self.B1 * 50
        self.max_curves = curves
        self.stats = {"curves_tried": 0, "factor_found_at_curve": 0}

    @staticmethod
    def _default_B1(n: int) -> int:
        bits = n.bit_length()
        if bits <= 32:
            return 250
        if bits <= 48:
            return 1000
        if bits <= 64:
            return 5000
        return 10000

    def _stage1(self, P: tuple, a: int) -> tuple | int:
        """Stage 1: compute prod(p^e for p<=B1) * P."""
        primes = sieve_of_eratosthenes(self.B1)
        Q = P
        for p in primes:
            # Compute p^e where p^e <= B1
            pe = p
            while pe * p <= self.B1:
                pe *= p
            Q = _ec_mul(pe, Q, a, self.n)
            if Q is None:
                return None  # Factor found
            if isinstance(Q, int):
                return Q
        return Q

    def factor(self) -> tuple[int, int] | None:
        """Try multiple random curves."""
        for _ in range(self.max_curves):
            self.stats["curves_tried"] += 1

            # Random curve: pick random point, compute curve parameter
            x0 = random.randint(1, self.n - 1)
            y0 = random.randint(1, self.n - 1)
            a = random.randint(1, self.n - 1)
            # b = y0^2 - x0^3 - a*x0 (mod n), curve passes through (x0, y0)

            P = (x0, y0)
            result = self._stage1(P, a)

            if result is None:
                # _ec_add returned None — means gcd found factor
                # We need to re-run more carefully to extract the factor
                # Simplified: try random points near the curve
                for trial in range(10):
                    x0 = random.randint(1, self.n - 1)
                    y0 = random.randint(1, self.n - 1)
                    P2 = (x0, y0)
                    primes = sieve_of_eratosthenes(min(self.B1, 500))
                    Q = P2
                    for p in primes:
                        pe = p
                        while pe * p <= self.B1:
                            pe *= p
                        old_Q = Q
                        Q = _ec_mul(pe, Q, a, self.n)
                        if Q is None:
                            # The gcd that caused failure
                            # Try to extract it from the last doubling
                            g = gcd(2 * old_Q[1], self.n) if old_Q != (0, 0) else 1
                            if 1 < g < self.n:
                                self.stats["factor_found_at_curve"] = self.stats["curves_tried"]
                                return (g, self.n // g)
                            break
                continue

        return None


class PlimptonECM(ECM):
    """ECM with curve selection guided by Plimpton 322 triples.

    Uses Pythagorean triples to generate curves with structured starting points.
    The triples have 5-smooth structure built in, which may correlate with
    group order divisibility properties.
    """

    def __init__(self, n: int, B1: int | None = None, B2: int | None = None,
                 curves: int = 20):
        super().__init__(n, B1, B2, curves)
        self._plimpton_curves = None

    def _get_plimpton_triples(self) -> list[tuple[int, int, int]]:
        """Get triples from extended Plimpton table."""
        if self._plimpton_curves is None:
            from cuneiform.tablet.plimpton322 import Plimpton322
            tablet = Plimpton322()
            rows = tablet.extended(max_regular=250)
            self._plimpton_curves = [row.triple for row in rows]
        return self._plimpton_curves

    def factor(self) -> tuple[int, int] | None:
        """Try Plimpton-derived curves first, then random."""
        triples = self._get_plimpton_triples()

        for idx, (w, l, d) in enumerate(triples[:self.max_curves]):
            self.stats["curves_tried"] += 1

            # Map triple to curve: use (w, l) as starting point
            x0 = w % self.n
            y0 = l % self.n
            if x0 == 0 or y0 == 0:
                continue

            # Curve parameter from triple structure
            # a = (y0^2 - x0^3) / x0 mod n (ensures point is on curve)
            x0_inv = pow(x0, -1, self.n) if gcd(x0, self.n) == 1 else None
            if x0_inv is None:
                g = gcd(x0, self.n)
                if 1 < g < self.n:
                    self.stats["factor_found_at_curve"] = self.stats["curves_tried"]
                    return (g, self.n // g)
                continue

            a = ((y0 * y0 - x0 * x0 * x0) * x0_inv) % self.n
            P = (x0, y0)

            result = self._stage1(P, a)

            if result is None:
                # Factor likely found — extract it
                primes = sieve_of_eratosthenes(min(self.B1, 200))
                Q = P
                for p in primes:
                    pe = p
                    while pe * p <= self.B1:
                        pe *= p
                    old_Q = Q
                    Q = _ec_mul(pe, Q, a, self.n)
                    if Q is None:
                        # Try to get the factor
                        if old_Q != (0, 0):
                            for component in old_Q:
                                g = gcd(component, self.n)
                                if 1 < g < self.n:
                                    self.stats["factor_found_at_curve"] = self.stats["curves_tried"]
                                    return (g, self.n // g)
                        break

        # Fall back to random curves
        return super().factor()
