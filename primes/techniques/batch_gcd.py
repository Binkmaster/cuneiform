"""Batch GCD (Heninger et al., 2012).

Finds shared prime factors across large sets of RSA moduli.  Used to
factor 0.2% of all HTTPS RSA keys in "Mining Your Ps and Qs".
O(n log^2 n) for n moduli.

Algorithm
---------
Build a product tree of all moduli, then compute remainder trees to
efficiently find GCDs between every pair.  For each modulus n_i, compute

    g = gcd( (product mod n_i^2) // n_i,  n_i )

If 1 < g < n_i, then g is a shared prime factor of n_i.

When it works best
------------------
- Large batches of RSA moduli generated with weak entropy (shared primes).
- Network-scale audits of TLS certificates, SSH host keys, etc.
- Not useful against a single modulus in isolation.
"""

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent))

from cuneiform.core.accel import gcd, isqrt, powmod, invert
from cuneiform.number_theory.primes import sieve_of_eratosthenes


def _product_tree(values: list[int]) -> list[list[int]]:
    """Build a product tree from a list of integers.

    Returns a list of levels, where level 0 is the input values and
    the last level contains a single element: the product of all values.
    """
    tree = [list(values)]
    while len(tree[-1]) > 1:
        level = tree[-1]
        tree.append([
            level[i] * level[i + 1] if i + 1 < len(level) else level[i]
            for i in range(0, len(level), 2)
        ])
    return tree


def _remainder_tree(product_tree: list[list[int]], n: int) -> list[int]:
    """Compute remainders of *n* modulo each leaf via a top-down remainder tree.

    Returns a list of remainders, one per leaf in *product_tree[0]*.
    """
    remainders: list[list[int]] = [None] * len(product_tree)  # type: ignore[list-item]
    remainders[-1] = [n % product_tree[-1][0]]
    for i in range(len(product_tree) - 2, -1, -1):
        remainders[i] = []
        for j in range(len(product_tree[i])):
            remainders[i].append(remainders[i + 1][j // 2] % product_tree[i][j])
    return remainders[0]


def factor_batch(moduli: list[int]) -> dict[int, tuple[int, int]]:
    """Find shared prime factors across a list of semiprimes.

    Parameters
    ----------
    moduli : list[int]
        A list of RSA moduli (or semiprimes) to check for shared factors.

    Returns
    -------
    dict[int, tuple[int, int]]
        Maps the index of each factorable modulus to its factor pair (p, q).
    """
    if len(moduli) < 2:
        return {}

    P = _product_tree(moduli)
    product = P[-1][0]

    results: dict[int, tuple[int, int]] = {}
    for i, n_i in enumerate(moduli):
        if n_i <= 1:
            continue
        n_sq = n_i * n_i
        r = product % n_sq
        g = gcd(r // n_i, n_i)
        if 1 < g < n_i:
            q = n_i // g
            results[i] = (g, q)

    return results


def factor(n: int, *, others: list[int] | None = None, **kwargs) -> tuple[int, int] | None:
    """Factor *n* by checking for a shared prime with other moduli.

    Parameters
    ----------
    n : int
        The semiprime to factor.
    others : list[int] | None
        Other moduli to check against.  If ``None``, returns ``None``
        immediately (batch GCD needs at least one other modulus).

    Returns
    -------
    tuple[int, int] | None
        A pair (p, q) with p * q == n, or ``None`` if no shared factor
        was found.
    """
    if others is None:
        return None

    for m in others:
        g = gcd(n, m)
        if 1 < g < n:
            return (g, n // g)

    return None
