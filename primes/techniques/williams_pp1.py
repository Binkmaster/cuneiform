"""Williams' p+1 factoring method using Lucas sequences.

Complexity: O(pi(B) * log(B) * log(n)) modular multiplications per seed,
for a total of O(|seeds| * pi(B) * log(B) * log(n)).

When it works best:
    - Finds a prime factor p when p+1 is B-smooth (all prime power divisors
      of p+1 are at most B).
    - Complementary to Pollard p-1: together they cover both p-1 and p+1
      smoothness.
    - Multiple seeds are tried because the method only works when the
      Jacobi symbol (D/p) = -1 for the discriminant D = seed^2 - 4.
      Since we don't know p, we try several seeds to increase the
      probability of hitting the right quadratic residue class.
    - Like p-1, it is ineffective against RSA primes (which have neither
      smooth p-1 nor smooth p+1 by design).
"""

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent))

from cuneiform.core.accel import gcd, isqrt, powmod, invert, is_probable_prime, HAS_GMPY2
from cuneiform.number_theory.primes import sieve_of_eratosthenes, is_prime


def factor(
    n: int,
    *,
    B: int = 500_000,
    seeds: list[int] | None = None,
) -> tuple[int, int] | None:
    """Factor n using Williams' p+1 method with Lucas sequences.

    Parameters
    ----------
    n : int
        The integer to factor (must be composite and > 1).
    B : int
        Smoothness bound. Primes (and their prime powers) up to B are
        used to drive the Lucas sequence.
    seeds : list[int] | None
        Starting values for the Lucas sequence. Each seed s defines the
        recurrence V_0 = 2, V_1 = s, V_k = s*V_{k-1} - V_{k-2} (mod n).
        Defaults to [3, 5, 7, 11, 13, 17].

    Returns
    -------
    tuple[int, int] | None
        A pair (p, n // p) with 1 < p < n, or None if no factor was found.
    """
    if seeds is None:
        seeds = [3, 5, 7, 11, 13, 17]

    primes = sieve_of_eratosthenes(B)

    for seed in seeds:
        v = seed

        for p in primes:
            # Compute the largest prime power pe with pe <= B
            pe = p
            while pe * p <= B:
                pe *= p

            # Compute V_{pe} from V = v using the doubling formulas:
            #   V_{2k}   = V_k^2 - 2         (mod n)
            #   V_{2k+1} = V_k * V_{k+1} - v (mod n)
            # Process the binary expansion of pe (skip the leading '1' bit).
            v_k = v
            v_k1 = (v * v - 2) % n

            for bit in bin(pe)[3:]:  # skip '0b1'
                if bit == '0':
                    v_k1 = (v_k * v_k1 - v) % n
                    v_k = (v_k * v_k - 2) % n
                else:
                    v_k = (v_k * v_k1 - v) % n
                    v_k1 = (v_k1 * v_k1 - 2) % n

            v = v_k

        g = gcd(v - 2, n)
        if 1 < g < n:
            return (g, n // g)

    return None
