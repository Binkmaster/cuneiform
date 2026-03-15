"""Coppersmith's method (1996).

Finds small roots of polynomials mod N.  The backbone of many RSA attacks:
partial key exposure, small-e broadcast, related messages.  Full version
uses LLL lattice reduction; this is a simplified direct-search variant.

Algorithm
---------
Given an RSA modulus N = p * q and partial knowledge of one factor p:

**Known MSBs:** p ~ p_0 + x where p_0 is the known high-bit approximation
and x is a small unknown correction.  Search delta in [0, X) checking
whether p_0 +/- delta divides N.

**Known LSBs:** p = known_bits + j * 2^k for integer j.  Search j upward
until the candidate exceeds sqrt(N).

Complexity
----------
O(X) trial divisions where X = 2^(unknown bits).  Practical when the
number of unknown bits is small (up to ~20 bits).  A full Coppersmith
implementation with LLL lattice reduction could handle ~N^(1/4) unknown
bits in polynomial time.

When it works best
------------------
- Partial key exposure (leaked MSBs or LSBs of a prime factor).
- Small unknown correction to an approximate factor.
- CTF challenges with contrived partial information.

Note
----
This is a simplified implementation.  A full Coppersmith implementation
requires LLL lattice reduction on shifted polynomials, which could be
added using the cuneiform lattice module in the future.
"""

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent))

from cuneiform.core.accel import gcd, isqrt, powmod, invert
from cuneiform.number_theory.primes import sieve_of_eratosthenes


def factor(n: int, *, known_bits: int | None = None, known_msb: bool = True,
           **kwargs) -> tuple[int, int] | None:
    """Factor *n* using partial knowledge of one prime factor.

    Parameters
    ----------
    n : int
        The RSA modulus (product of two primes).
    known_bits : int | None
        The known portion of one factor.  Interpretation depends on
        *known_msb*.  If ``None``, returns ``None`` (partial knowledge
        is required).
    known_msb : bool
        If ``True`` (default), *known_bits* represents the most-significant
        bits of a factor.  If ``False``, *known_bits* represents the
        least-significant bits.

    Returns
    -------
    tuple[int, int] | None
        A pair (p, q) with p * q == n, or ``None`` if no factor was found
        within the search bound.
    """
    if known_bits is None:
        return None

    bit_length = n.bit_length() // 2  # approximate size of factors

    if known_msb:
        # known_bits are the high bits of p.
        # p = known_bits << unknown_bits + x  where  0 <= x < 2^unknown_bits
        unknown_bits = bit_length - known_bits.bit_length()
        if unknown_bits < 0:
            # known_bits is already at or beyond factor length -- try directly
            unknown_bits = 0

        p_approx = known_bits << unknown_bits
        X = 1 << unknown_bits

        for delta in range(min(X, 1_000_000)):
            p_try = p_approx + delta
            if p_try > 1 and n % p_try == 0:
                return (p_try, n // p_try)
            if delta > 0:
                p_try = p_approx - delta
                if p_try > 1 and n % p_try == 0:
                    return (p_try, n // p_try)
    else:
        # known_bits are the low bits of p.
        # p ≡ known_bits  (mod 2^k)
        k = known_bits.bit_length()
        modulus = 1 << k

        sqrt_n = isqrt(n)
        for j in range(1_000_000):
            p_try = known_bits + j * modulus
            if p_try <= 1:
                continue
            if p_try > sqrt_n:
                break
            if n % p_try == 0:
                return (p_try, n // p_try)

    return None
