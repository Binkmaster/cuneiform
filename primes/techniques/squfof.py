"""SQUFOF (Shanks, ~1975), O(n^(1/4)) time, O(1) space, very practical for numbers up to ~60 digits.

Square Form Factorization works by iterating the continued fraction expansion
of sqrt(k*n) until a perfect-square quadratic form Q_i is encountered on an
even step.  A reverse walk then recovers a non-trivial factor via gcd.

The multiplier k is drawn from a small set of primes (and 1) to increase the
chance of hitting a proper square form quickly.
"""

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent))

from cuneiform.core.accel import gcd, isqrt


_DEFAULT_MULTIPLIERS = [1, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]


def factor(
    n: int,
    *,
    max_iterations: int = 100_000,
    multipliers: list[int] | None = None,
) -> tuple[int, int] | None:
    """Factor *n* using Shanks' SQUFOF algorithm.

    Parameters
    ----------
    n : int
        The integer to factor (must be composite and > 1).
    max_iterations : int
        Maximum continued-fraction steps per multiplier.
    multipliers : list[int] | None
        Multipliers to try.  Defaults to small primes and 1.

    Returns
    -------
    tuple[int, int] | None
        A pair (p, n // p) with 1 < p < n, or None if no factor was found.
    """
    if multipliers is None:
        multipliers = _DEFAULT_MULTIPLIERS

    # SQUFOF is practical only for numbers up to ~60 digits (~200 bits).
    # Beyond that the CF expansion is too slow; bail immediately.
    if n.bit_length() > 200:
        return None

    for k in multipliers:
        result = _squfof_one(n, k, max_iterations)
        if result is not None:
            return result

    return None


def _squfof_one(
    n: int, k: int, max_iterations: int
) -> tuple[int, int] | None:
    """Run SQUFOF with a single multiplier *k*."""
    D = k * n
    sqrt_D = isqrt(D)

    # If D is a perfect square the CF is degenerate — skip.
    if sqrt_D * sqrt_D == D:
        return None

    # --- Initialise the forward continued-fraction walk ---
    P_prev = sqrt_D
    Q_prev = 1
    Q_curr = D - P_prev * P_prev

    if Q_curr == 0:
        return None

    # --- Forward cycle: hunt for a perfect-square Q on an even step ---
    for i in range(1, max_iterations + 1):
        b = (sqrt_D + P_prev) // Q_curr
        P_curr = b * Q_curr - P_prev
        Q_next = Q_prev + b * (P_prev - P_curr)

        # Check on even steps whether Q_curr is a perfect square.
        if i % 2 == 0:
            s = isqrt(Q_curr)
            if s * s == Q_curr:
                # Found a square form — launch the reverse cycle.
                f = _reverse_cycle(n, D, sqrt_D, P_prev, s)
                if f is not None:
                    return f

        # Advance
        P_prev = P_curr
        Q_prev = Q_curr
        Q_curr = Q_next

    return None


def _reverse_cycle(
    n: int, D: int, sqrt_D: int, P_sq: int, S: int
) -> tuple[int, int] | None:
    """Given a square form with root *S* found at P value *P_sq*, walk the
    reverse continued fraction until a period is detected and extract a factor.
    """
    b0 = (sqrt_D + P_sq) // S
    P_rev = b0 * S - P_sq
    Q_rev_prev = S
    Q_rev = (D - P_rev * P_rev) // S

    # Iterate the reverse CF until P stabilises.
    for _ in range(100_000):
        b = (sqrt_D + P_rev) // Q_rev
        P_new = b * Q_rev - P_rev
        Q_new = Q_rev_prev + b * (P_rev - P_new)

        if P_new == P_rev:
            f = gcd(n, P_rev)
            if 1 < f < n:
                return (f, n // f)
            return None

        P_rev = P_new
        Q_rev_prev = Q_rev
        Q_rev = Q_new

    return None
