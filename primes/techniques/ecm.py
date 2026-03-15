"""Elliptic Curve Method (ECM) factoring wrapper.

Algorithm
---------
ECM works by performing arithmetic on a random elliptic curve modulo n.
If the group order modulo one of n's prime factors is B1-smooth, the
point multiplication will hit the point at infinity modulo that factor,
revealing it via a GCD.  Multiple random curves are tried (each has an
independent, random group order).

This module wraps the cuneiform ECM implementations:
  - ``ECM``          -- standard random-curve ECM
  - ``PlimptonECM``  -- curves derived from Plimpton-322 Pythagorean triples

Complexity
----------
Heuristic sub-exponential: L_p[1/2, sqrt(2)] where p is the smallest
prime factor.  Practical for factors up to ~50 digits with appropriate
bounds.

When it works best
------------------
- Medium-sized factors (20--50 digits) where QS/GNFS are overkill.
- When you can afford many curves: each curve is an independent trial.
- Falls off sharply once the smallest factor exceeds ~60 digits.
"""

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent))

from cuneiform.core.accel import gcd, isqrt, powmod, invert, is_probable_prime, HAS_GMPY2
from cuneiform.number_theory.primes import sieve_of_eratosthenes, is_prime


def factor(n: int, *, curves: int = 100, B1: int = 50_000) -> tuple[int, int] | None:
    """Factor *n* using the Elliptic Curve Method.

    Parameters
    ----------
    n : int
        The integer to factor (must be composite and > 1).
    curves : int
        Total number of curves to try (split between standard and
        Plimpton-derived curves).
    B1 : int
        Stage-1 smoothness bound.

    Returns
    -------
    tuple[int, int] | None
        A pair (p, n // p) where p is a non-trivial factor of *n*,
        or ``None`` if no factor was found.
    """
    from cuneiform.number_theory.ecm import ECM, PlimptonECM

    half = max(curves // 2, 1)

    # Standard ECM with random curves.
    ecm = ECM(n, B1=B1, curves=half)
    result = ecm.factor()
    if result is not None:
        p = result[0]
        return (p, n // p)

    # Plimpton-322-derived curves.
    pecm = PlimptonECM(n, B1=B1, curves=curves - half)
    result = pecm.factor()
    if result is not None:
        p = result[0]
        return (p, n // p)

    return None
