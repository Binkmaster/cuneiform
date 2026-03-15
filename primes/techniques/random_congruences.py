"""Random witness search for non-trivial square roots of 1 mod n.

For a composite n = p * q, the equation x^2 = 1 (mod n) has four solutions:
+/- 1 and two non-trivial roots that reveal the factorization via gcd. This
technique picks random bases a and computes a^{(n-1)/2} mod n. If the result
is neither 1 nor n-1, it is a non-trivial square root of a^{n-1} mod n, and
gcd(val +/- 1, n) may reveal a factor.

When it works best:
    - For numbers where n-1 has useful algebraic structure.
    - If n is a Carmichael number (passes Fermat test but is composite),
      this can still find factors through square-root witnesses.
    - For true RSA semiprimes (p, q both large primes), the probability of
      a random a yielding a non-trivial square root of 1 is approximately
      1/2 per attempt when the Jacobi symbol analysis is favorable. However,
      a^{(n-1)/2} mod n lands on +/- 1 with overwhelming probability for
      well-chosen RSA primes, making success very unlikely per attempt.
    - Deterministic seed ensures reproducibility across runs.
"""

import sys
import random

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent))

from cuneiform.core.accel import gcd, isqrt, powmod, invert, is_probable_prime, HAS_GMPY2
from cuneiform.number_theory.primes import sieve_of_eratosthenes, is_prime


def factor(n: int, *, attempts: int = 100_000, seed: int = 42) -> tuple[int, int] | None:
    """Factor n by searching for non-trivial square roots of 1 mod n.

    Parameters
    ----------
    n : int
        The integer to factor (must be > 1, odd, and composite).
    attempts : int
        Number of random bases to try.
    seed : int
        Seed for the PRNG (deterministic by default).

    Returns
    -------
    tuple[int, int] | None
        A pair (p, n // p) if a factor is found, or None.
    """
    rng = random.Random(seed)
    half_order = (n - 1) // 2

    for _ in range(attempts):
        a = rng.randint(2, n - 2)
        val = powmod(a, half_order, n)

        if val == 1 or val == n - 1:
            continue

        # val is a non-trivial result; check if it reveals a factor
        g = gcd(val - 1, n)
        if 1 < g < n:
            return (g, n // g)

        g = gcd(val + 1, n)
        if 1 < g < n:
            return (g, n // g)

    return None
