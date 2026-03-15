"""Heuristic GCD bombardment for integer factorization.

Tests gcd(n, v) for a variety of number-theoretic sequences, hoping that one
of them shares a non-trivial common factor with n. The sequences tested are:

    1. Factorials:   gcd(k! +/- 1, n) for k in {100, 200, 500, 999}
    2. Powers of 60: gcd(60^k - 1, n) for k = 1..200
    3. Fibonacci:    gcd(Fib(k), n) for k = 1000, 2000, ..., 10000

When it works best:
    - If one of p or q divides a term in these sequences, the gcd reveals it.
    - Fibonacci GCD is related to Pisano periods: gcd(Fib(k), n) is non-trivial
      when the Pisano period of p (or q) divides k.
    - Powers of 60 connect to the sexagesimal / Babylonian theme: if the
      multiplicative order of 60 mod p divides k, then p | (60^k - 1).
    - Factorials relate to Pollard p-1: if p-1 | k!, then p | (a^{k!} - 1).
    - Very cheap to run; always worth trying before heavier methods.
"""

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent))

from cuneiform.core.accel import gcd, isqrt, powmod, invert, is_probable_prime, HAS_GMPY2
from cuneiform.number_theory.primes import sieve_of_eratosthenes, is_prime


def factor(n: int, **kwargs) -> tuple[int, int] | None:
    """Factor n by testing gcd with special number-theoretic sequences.

    Parameters
    ----------
    n : int
        The integer to factor (must be > 1 and composite).

    Returns
    -------
    tuple[int, int] | None
        A pair (p, n // p) if a factor is found, or None.
    """
    # --- Factorials: gcd(k! +/- 1, n) ---
    factorial = 1
    checkpoint_ks = {100, 200, 500, 999}
    for k in range(1, 1000):
        factorial = (factorial * k) % n
        if k in checkpoint_ks:
            for offset in (-1, 1):
                g = gcd(factorial + offset, n)
                if 1 < g < n:
                    return (g, n // g)

    # --- Powers of 60: gcd(60^k - 1, n) ---
    for k in range(1, 201):
        val = powmod(60, k, n) - 1
        g = gcd(val, n)
        if 1 < g < n:
            return (g, n // g)

    # --- Fibonacci numbers mod n: check every 1000th term ---
    fib_a, fib_b = 0, 1
    for k in range(1, 10001):
        fib_a, fib_b = fib_b, (fib_a + fib_b) % n
        if k % 1000 == 0:
            g = gcd(fib_a, n)
            if 1 < g < n:
                return (g, n // g)

    return None
