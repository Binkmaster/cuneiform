"""Fermat's difference-of-squares factoring method.

Algorithm
---------
Express n = a^2 - b^2 = (a + b)(a - b).  Start with a = isqrt(n) + 1 and
increment a, checking at each step whether b^2 = a^2 - n is a perfect square.
If it is, both (a + b) and (a - b) are non-trivial factors of n (assuming
n is not a perfect square and b > 0).

Complexity
----------
O(|p - q|) iterations where p and q are the two factors.  The method
converges quickly when the factors are close to sqrt(n) and is hopeless
when they differ by much more than n^{1/4}.

When it works best
------------------
- Semiprimes where p and q are nearly equal (e.g. |p - q| < 10^6).
- Quick pre-check before moving to heavier sub-exponential methods.
- Always O(1) for perfect squares (caught as a degenerate case).
"""

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent))

from cuneiform.core.accel import gcd, isqrt, powmod, invert, is_probable_prime, HAS_GMPY2
from cuneiform.number_theory.primes import sieve_of_eratosthenes, is_prime


def factor(n: int, *, iterations: int = 1_000_000) -> tuple[int, int] | None:
    """Factor *n* using Fermat's difference-of-squares method.

    Parameters
    ----------
    n : int
        The integer to factor (must be > 1 and odd).
    iterations : int
        Maximum number of candidate values of *a* to try.

    Returns
    -------
    tuple[int, int] | None
        A pair (a + b, a - b) such that their product equals *n*,
        or ``None`` if no factorisation was found within the iteration
        budget.
    """
    a = isqrt(n)
    if a * a == n:
        # Perfect square — immediate factorisation.
        return (a, a)
    a += 1

    for _ in range(iterations):
        b2 = a * a - n
        b = isqrt(b2)
        if b * b == b2:
            p = a + b
            q = a - b
            if q > 1:
                return (p, q)
        a += 1

    return None
