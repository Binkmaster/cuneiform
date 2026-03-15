"""Wiener's continued-fraction attack on RSA.

Algorithm
---------
Given an RSA public key (n, e), compute the continued-fraction expansion
of e/n.  Each convergent k/d is a candidate for the fraction
(e*d - 1) / phi(n).  When k and d are correct:

    phi(n) = (e*d - 1) / k

From phi(n) and n the factors are recovered via the quadratic formula:

    p + q = n - phi(n) + 1
    p * q = n

    discriminant = (p + q)^2 - 4*n
    p, q = ((p+q) +/- sqrt(discriminant)) / 2

Complexity
----------
O(log n) convergents to check.  Each check is dominated by one
integer square-root and a few multiplications -- effectively free.

When it works best
------------------
- Only when the RSA private exponent d < n^{1/4} / 3 (Wiener's bound).
- Typical RSA keys with e = 65537 are immune because d is large.
- Targets RSA instances with intentionally or accidentally small d
  (e.g., performance-optimised keys, CTF challenges).
- Always worth running: negligible cost, devastating when it applies.
"""

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent))

from cuneiform.core.accel import gcd, isqrt, powmod, invert, is_probable_prime, HAS_GMPY2
from cuneiform.number_theory.primes import sieve_of_eratosthenes, is_prime
from cuneiform.crypto.continued_fractions import cf_expansion, cf_convergents


def factor(n: int, *, e: int = 65537) -> tuple[int, int] | None:
    """Factor an RSA modulus *n* using Wiener's continued-fraction attack.

    Parameters
    ----------
    n : int
        The RSA modulus (product of two primes).
    e : int
        The RSA public exponent.  This parameter is **required** for
        the attack to work -- it defaults to the common value 65537
        but must match the actual public exponent of the target key.

    Returns
    -------
    tuple[int, int] | None
        A pair (p, q) with p * q == n, or ``None`` if the attack did
        not succeed (i.e. d is too large for Wiener's bound).
    """
    terms = cf_expansion(e, n, max_terms=max(n.bit_length(), 200))
    convergents = cf_convergents(terms)

    for k, d in convergents:
        if k == 0 or d == 0:
            continue

        # Check divisibility: phi(n) = (e*d - 1) / k must be an integer.
        ed_minus_1 = e * d - 1
        if ed_minus_1 % k != 0:
            continue

        phi_n = ed_minus_1 // k

        # From phi(n) recover p and q via the quadratic formula.
        # p + q = n - phi(n) + 1 = s
        s = n - phi_n + 1
        discriminant = s * s - 4 * n
        if discriminant < 0:
            continue

        sqrt_disc = isqrt(discriminant)
        if sqrt_disc * sqrt_disc != discriminant:
            continue

        p = (s + sqrt_disc) // 2
        q = (s - sqrt_disc) // 2

        if p > 1 and q > 1 and p * q == n:
            return (p, q)

    return None
