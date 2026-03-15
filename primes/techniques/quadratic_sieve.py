"""Quadratic Sieve (QS) factoring wrapper.

Algorithm
---------
The Quadratic Sieve finds pairs (x, y) such that x^2 = y^2 (mod n),
then checks gcd(x - y, n) for a non-trivial factor.  It does this by
sieving polynomial values Q(x) = (x + isqrt(n))^2 - n for B-smooth
numbers, collecting enough relations to build a dependency in GF(2),
and combining relations to produce a congruence of squares.

This module wraps two cuneiform implementations:
  - ``QuadraticSieve``              -- standard QS
  - ``SexagesimalQuadraticSieve``   -- QS with a sexagesimal (base-60)
    tiered factor base and regularity pre-filter

Complexity
----------
Sub-exponential: L_n[1/2, 1] -- the fastest known algorithm for numbers
up to roughly 100 digits.  Beyond that the General Number Field Sieve
(GNFS) is faster.

When it works best
------------------
- The most general-purpose factoring method for numbers in the 50--100
  digit range.
- No assumptions about factor structure (unlike ECM, Fermat, or Wiener).
- Pure-Python implementation is practical up to ~80-bit semiprimes;
  larger targets need a compiled sieve.
"""

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent))

from cuneiform.core.accel import gcd, isqrt, powmod, invert, is_probable_prime, HAS_GMPY2
from cuneiform.number_theory.primes import sieve_of_eratosthenes, is_prime


def factor(
    n: int,
    *,
    bound: int | None = None,
    sieve_range: int | None = None,
    sexagesimal: bool = True,
) -> tuple[int, int] | None:
    """Factor *n* using the Quadratic Sieve.

    Parameters
    ----------
    n : int
        The integer to factor (must be composite and > 1).
    bound : int | None
        Smoothness bound for the factor base.  When ``None`` the sieve
        auto-computes an appropriate value from the size of *n*.
    sieve_range : int | None
        Half-width of the sieve interval.  When ``None`` the sieve
        chooses a default proportional to the bound.
    sexagesimal : bool
        If ``True`` (default), use the ``SexagesimalQuadraticSieve``
        with its tiered factor base and regularity pre-filter.
        Otherwise use the standard ``QuadraticSieve``.

    Returns
    -------
    tuple[int, int] | None
        A pair (p, q) with p * q == n, or ``None`` if the sieve did
        not find enough relations to produce a factorisation.
    """
    from cuneiform.number_theory.sieve import QuadraticSieve, SexagesimalQuadraticSieve

    kwargs: dict = {}
    if bound is not None:
        kwargs["bound"] = bound
    if sieve_range is not None:
        kwargs["sieve_range"] = sieve_range

    if sexagesimal:
        qs = SexagesimalQuadraticSieve(n, **kwargs)
    else:
        qs = QuadraticSieve(n, **kwargs)

    return qs.factor()
