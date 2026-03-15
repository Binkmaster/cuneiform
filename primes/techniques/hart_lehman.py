"""Hart's one-line (2012) and Lehman's method (1974).

Hart is heuristic but fast.  Lehman is deterministic O(n^(1/3)).
Both are practical for medium-sized integers.

Hart's One-Line Factorization
-----------------------------
For s = ceil(sqrt(n)), ceil(sqrt(2n)), ceil(sqrt(3n)), ... compute
m = s^2 mod n and check whether m is a perfect square t^2.  If so,
gcd(s - t, n) may yield a non-trivial factor.  Very simple and
surprisingly effective on random composites.

Lehman's Method (1974)
----------------------
After trial division up to n^(1/3), search for integers a, k such that
a^2 - 4kn is a perfect square b^2.  Then gcd(a + b, n) is a factor.
The search range for a is bounded by O(n^(1/6) / sqrt(k)), giving
deterministic O(n^(1/3)) complexity.
"""

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent))

from cuneiform.core.accel import gcd, isqrt


# ---------------------------------------------------------------------------
# Hart's One-Line Factorization
# ---------------------------------------------------------------------------

def factor_hart(n: int, *, max_iterations: int = 1_000_000) -> tuple[int, int] | None:
    """Factor *n* using Hart's one-line method.

    Parameters
    ----------
    n : int
        The integer to factor (must be > 1).
    max_iterations : int
        Maximum number of multipliers to try (default 1 000 000).

    Returns
    -------
    tuple[int, int] | None
        A non-trivial factorisation ``(p, q)`` with ``p * q == n``,
        or ``None`` if no factorisation was found.
    """
    for i in range(1, max_iterations + 1):
        s = isqrt(i * n)
        if s * s < i * n:
            s += 1
        m = (s * s) % n
        t = isqrt(m)
        if t * t == m:
            g = gcd(s - t, n)
            if 1 < g < n:
                return (g, n // g)
    return None


# ---------------------------------------------------------------------------
# Lehman's Method (1974)
# ---------------------------------------------------------------------------

def factor_lehman(n: int) -> tuple[int, int] | None:
    """Factor *n* using Lehman's deterministic O(n^(1/3)) method.

    Parameters
    ----------
    n : int
        The integer to factor (must be > 1).

    Returns
    -------
    tuple[int, int] | None
        A non-trivial factorisation ``(p, q)`` with ``p * q == n``,
        or ``None`` if *n* is prime or 1.
    """
    cbrt_n = int(n ** (1 / 3)) + 1

    # Trial division up to n^(1/3).
    for p in range(2, cbrt_n + 1):
        if n % p == 0:
            return (p, n // p)

    # Lehman's lattice search.
    for k in range(1, cbrt_n + 1):
        sqrt_4kn = isqrt(4 * k * n)
        if sqrt_4kn * sqrt_4kn < 4 * k * n:
            sqrt_4kn += 1
        # Upper bound: sqrt(4kn) + n^(1/6) / (4*sqrt(k))
        limit = sqrt_4kn + max(1, int(n ** (1 / 6) / (4 * isqrt(k) + 1)) + 1)
        for a in range(sqrt_4kn, limit + 1):
            b2 = a * a - 4 * k * n
            b = isqrt(b2)
            if b * b == b2:
                g = gcd(a + b, n)
                if 1 < g < n:
                    return (g, n // g)

    return None


# ---------------------------------------------------------------------------
# Combined entry point
# ---------------------------------------------------------------------------

def factor(n: int, **kwargs) -> tuple[int, int] | None:
    """Factor *n* by trying Hart's method first, then Lehman's.

    Parameters
    ----------
    n : int
        The integer to factor (must be > 1).
    **kwargs
        Passed to :func:`factor_hart` (e.g. ``max_iterations``).

    Returns
    -------
    tuple[int, int] | None
        A non-trivial factorisation ``(p, q)`` with ``p * q == n``,
        or ``None`` if neither method succeeded.
    """
    result = factor_hart(n, **kwargs)
    if result is not None:
        return result
    return factor_lehman(n)
