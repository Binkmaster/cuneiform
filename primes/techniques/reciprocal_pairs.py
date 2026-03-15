"""Babylonian reciprocal pair analysis for integer factorization.

In the Babylonian sexagesimal system, "regular" numbers (those whose only prime
factors are 2, 3, and 5) have finite reciprocal expansions. This technique
exploits that property: for each 5-smooth number x coprime to n, we compute
x_inv = x^{-1} mod n and test whether gcd(x + x_inv, n) or gcd(x - x_inv, n)
reveals a non-trivial factor.

The intuition is that if n = p * q, then x^{-1} mod n encodes information about
both x^{-1} mod p and x^{-1} mod q via CRT. The sum and difference of x and
x^{-1} can collapse that structure, leaking a factor through gcd.

When it works best:
    - Small semiprimes where the factor space is constrained enough that
      regular-number inverses may collide with algebraic structure.
    - Conceptually unique to this project: a Babylonian mathematical approach
      to modern factoring.
    - Very unlikely to crack large RSA moduli, but an elegant heuristic.
"""

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent))

from cuneiform.core.accel import gcd, isqrt, powmod, invert, is_probable_prime, HAS_GMPY2
from cuneiform.number_theory.primes import sieve_of_eratosthenes, is_prime


def _generate_regular_numbers(limit: int) -> list[int]:
    """Generate all 5-smooth (regular) numbers less than `limit`, sorted."""
    results = []
    a = 1
    while a < limit:
        b = a
        while b < limit:
            c = b
            while c < limit:
                results.append(c)
                c *= 5
            b *= 3
        a *= 2
    results.sort()
    return results


def factor(n: int, *, limit: int = 10_000, max_pairs: int = 200) -> tuple[int, int] | None:
    """Factor n using Babylonian reciprocal pair analysis.

    Parameters
    ----------
    n : int
        The integer to factor (must be > 1 and composite).
    limit : int
        Upper bound for generating 5-smooth (regular) numbers.
    max_pairs : int
        Maximum number of reciprocal pairs to test.

    Returns
    -------
    tuple[int, int] | None
        A pair (p, n // p) if a factor is found, or None.
    """
    regular_numbers = _generate_regular_numbers(limit)

    # Filter to those coprime to n and greater than 1
    coprime = [x for x in regular_numbers if x > 1 and gcd(x, n) == 1]

    # Check if any regular number itself divides n (trivial factor)
    for x in regular_numbers:
        if x > 1:
            g = gcd(x, n)
            if 1 < g < n:
                return (g, n // g)

    tested = 0
    for x in coprime:
        if tested >= max_pairs:
            break
        tested += 1

        x_inv = invert(x, n)

        # Check sum: gcd(x + x_inv, n)
        g = gcd((x + x_inv) % n, n)
        if 1 < g < n:
            return (g, n // g)

        # Check difference: gcd(x - x_inv, n)
        g = gcd((x - x_inv) % n, n)
        if 1 < g < n:
            return (g, n // g)

    return None
