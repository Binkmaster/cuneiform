"""Pollard's p-1 factoring method (two-stage).

Complexity: Stage 1 costs O(pi(B1) * log(n)) modular exponentiations.
Stage 2 adds O(pi(B2) - pi(B1)) modular exponentiations with batched GCD.

When it works best:
    - Finds a prime factor p when p-1 is B1-smooth (all prime power divisors
      of p-1 are at most B1).
    - Stage 2 extends the reach: succeeds if p-1 has at most one prime
      factor between B1 and B2, with the rest at most B1.
    - Cheap and effective against primes with smooth p-1 (e.g., factors of
      Cunningham numbers). Useless against RSA primes, which are specifically
      chosen so that p-1 has a large prime factor.
"""

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent))

from cuneiform.core.accel import gcd, isqrt, powmod, invert, is_probable_prime, HAS_GMPY2
from cuneiform.number_theory.primes import sieve_of_eratosthenes, is_prime


def factor(n: int, *, B1: int = 500_000, B2: int = 5_000_000) -> tuple[int, int] | None:
    """Factor n using the two-stage Pollard p-1 method.

    Parameters
    ----------
    n : int
        The integer to factor (must be composite and > 1).
    B1 : int
        Smoothness bound for stage 1. Primes (and their powers) up to B1
        are accumulated into the exponent.
    B2 : int
        Smoothness bound for stage 2. Individual primes in (B1, B2) are
        tested with batched GCD.

    Returns
    -------
    tuple[int, int] | None
        A pair (p, n // p) with 1 < p < n, or None if no factor was found.
    """
    # ------------------------------------------------------------------
    # Stage 1: compute a = 2^(product of p^e for p <= B1) mod n
    # ------------------------------------------------------------------
    primes = sieve_of_eratosthenes(B1)

    a = 2
    for p in primes:
        # Raise p to the largest power pe such that pe <= B1
        pe = p
        while pe * p <= B1:
            pe *= p
        a = powmod(a, pe, n)

    g = gcd(a - 1, n)
    if 1 < g < n:
        return (g, n // g)

    # If g == n the base was unlucky; if g == 1 we continue to stage 2.
    if g == n:
        return None

    # ------------------------------------------------------------------
    # Stage 2: check individual primes in (B1, B2) with batched GCD
    # ------------------------------------------------------------------
    stage2_primes = sieve_of_eratosthenes(min(B2, B1 + 2_000_000))

    product = 1
    batch_size = 500
    count = 0

    for p in stage2_primes:
        if p <= B1:
            continue
        ap = powmod(a, p, n)
        product = (product * (ap - 1)) % n
        count += 1

        if count % batch_size == 0:
            g2 = gcd(product, n)
            if 1 < g2 < n:
                return (g2, n // g2)
            if g2 == n:
                # Backtrack: test primes in this batch individually
                for p2 in stage2_primes:
                    if p2 <= p - batch_size or p2 > p:
                        continue
                    if p2 <= B1:
                        continue
                    g3 = gcd(powmod(a, p2, n) - 1, n)
                    if 1 < g3 < n:
                        return (g3, n // g3)
                # All trivial — reset accumulator
                product = 1

    # Final GCD for any leftover product
    g2 = gcd(product, n)
    if 1 < g2 < n:
        return (g2, n // g2)

    return None
