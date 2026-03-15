"""Trial division factoring via prime sieve.

Complexity: O(pi(limit)) trial divisions, where pi(limit) is the number of
primes up to `limit`. Each division is O(1) for machine-word primes against
an arbitrary-precision n.

When it works best:
    - Always run first as a cheap pre-filter.
    - Finds factors up to `limit` (default 1,000,000) instantly.
    - Useless against balanced semiprimes with large factors, but essential
      for stripping small factors before heavier methods.
"""

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent))

from cuneiform.core.accel import gcd, isqrt, powmod, invert, is_probable_prime, HAS_GMPY2
from cuneiform.number_theory.primes import sieve_of_eratosthenes, is_prime


def factor(n: int, *, limit: int = 1_000_000) -> tuple[int, int] | None:
    """Factor n by testing all primes up to `limit`.

    Parameters
    ----------
    n : int
        The integer to factor (must be > 1).
    limit : int
        Upper bound for the prime sieve. Only primes up to this value
        are tested.

    Returns
    -------
    tuple[int, int] | None
        A pair (p, n // p) where p is the smallest prime factor found,
        or None if no prime up to `limit` divides n.
    """
    primes = sieve_of_eratosthenes(limit)
    for p in primes:
        if p * p > n:
            # n is itself prime
            break
        if n % p == 0:
            return (p, n // p)
    return None
