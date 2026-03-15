"""Pollard's rho factoring with Brent's improvement and batched GCD.

Complexity: O(n^(1/4)) expected iterations to find the smallest prime factor p,
since the birthday-paradox cycle length in Z/pZ is O(sqrt(p)).

When it works best:
    - Excellent general-purpose method for factors up to ~60 bits.
    - No memory overhead (unlike baby-step/giant-step).
    - Batched GCD (every 1000 steps) amortises the cost of gcd calls.
    - For balanced semiprimes with >80-bit factors, the expected iteration
      count exceeds practical limits; use ECM or sub-exponential methods.
"""

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent))

from cuneiform.core.accel import gcd, isqrt, powmod, invert, is_probable_prime, HAS_GMPY2
from cuneiform.number_theory.primes import sieve_of_eratosthenes, is_prime


def factor(n: int, *, iterations: int = 5_000_000) -> tuple[int, int] | None:
    """Factor n using Pollard's rho with Brent's cycle detection.

    Parameters
    ----------
    n : int
        The integer to factor (must be composite and > 1).
    iterations : int
        Maximum number of pseudo-random steps before giving up.

    Returns
    -------
    tuple[int, int] | None
        A pair (p, n // p) with 1 < p < n, or None if no factor was found.
    """
    x = 2
    y = 2
    c = 1
    d = 1

    # Batched GCD accumulator
    product = 1
    batch = 1000

    # Checkpoint for backtracking on trivial gcd(product, n) == n
    x_save, y_save = x, y

    for i in range(1, iterations + 1):
        if i % batch == 1:
            x_save, y_save = x, y

        # Floyd/Brent: x takes one step, y takes two
        x = (x * x + c) % n
        y = (y * y + c) % n
        y = (y * y + c) % n

        diff = x - y if x > y else y - x
        if diff == 0:
            # Trivial cycle — restart with a new polynomial
            c += 1
            x = y = 2
            x_save = y_save = 2
            product = 1
            continue

        product = (product * diff) % n

        if i % batch == 0:
            d = gcd(product, n)
            if d == n:
                # Backtrack: replay this batch with individual GCDs
                x2, y2 = x_save, y_save
                for _j in range(batch):
                    x2 = (x2 * x2 + c) % n
                    y2 = (y2 * y2 + c) % n
                    y2 = (y2 * y2 + c) % n
                    d2 = gcd(abs(x2 - y2), n)
                    if 1 < d2 < n:
                        return (d2, n // d2)
                # Entire batch was trivial — new polynomial
                c += 1
                x = y = 2
                x_save = y_save = 2
                product = 1
                continue
            if 1 < d < n:
                return (d, n // d)
            product = 1

    return None
