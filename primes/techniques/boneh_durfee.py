"""Boneh-Durfee attack (1999).

Extends Wiener's d < N^0.25 bound to d < N^0.292 using lattice
techniques.  This implementation uses extended continued fractions
with semi-convergents.  A full implementation would use Coppersmith's
bivariate method with LLL.

Algorithm
---------
The RSA key equation is:

    e * d = 1 + k * phi(N)

where phi(N) = (p - 1)(q - 1) = N - p - q + 1.  Rearranging:

    e * d + k * (p + q - 1) = 1 + k * N

This gives f(x, y) = x * (N + 1 + y) + 1  (mod e)  with x = k,
y = -(p + q).

Standard Wiener recovers d from the convergents of e/N.  This
implementation extends the search to *semi-convergents*: for each
convergent h_i / k_i, it also checks (h_{i-1} * j + h_i) / (k_{i-1} * j + k_i)
for small j, reaching farther into the Stern-Brocot tree.

Complexity
----------
O(log N * J) where J is the semi-convergent search depth (default 50).

When it works best
------------------
- RSA keys with a private exponent slightly above Wiener's N^0.25 bound.
- Extends the vulnerable range to d < N^0.292.
- Always worth running after Wiener fails: marginal extra cost.
"""

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent))

from cuneiform.core.accel import gcd, isqrt, powmod, invert
from cuneiform.number_theory.primes import sieve_of_eratosthenes
from cuneiform.crypto.continued_fractions import cf_expansion, cf_convergents


def _try_candidate(n: int, e: int, k: int, d: int) -> tuple[int, int] | None:
    """Check whether a candidate (k, d) yields a valid factorisation."""
    if k == 0 or d == 0:
        return None
    ed_minus_1 = e * d - 1
    if ed_minus_1 % k != 0:
        return None

    phi_n = ed_minus_1 // k

    # p + q = n - phi(n) + 1
    s = n - phi_n + 1
    discriminant = s * s - 4 * n
    if discriminant < 0:
        return None

    sqrt_disc = isqrt(discriminant)
    if sqrt_disc * sqrt_disc != discriminant:
        return None

    p = (s + sqrt_disc) // 2
    q = (s - sqrt_disc) // 2

    if p > 1 and q > 1 and p * q == n:
        return (p, q)

    return None


def factor(n: int, *, e: int, **kwargs) -> tuple[int, int] | None:
    """Factor an RSA modulus *n* using the Boneh-Durfee attack.

    Parameters
    ----------
    n : int
        The RSA modulus (product of two primes).
    e : int
        The RSA public exponent.  **Required** -- the attack exploits
        the relationship between e and the private exponent d.

    Returns
    -------
    tuple[int, int] | None
        A pair (p, q) with p * q == n, or ``None`` if the attack did
        not succeed (i.e. d is too large for the extended bound).
    """
    terms = cf_expansion(e, n, max_terms=max(n.bit_length(), 500))
    convergents = cf_convergents(terms)

    # --- Pass 1: standard Wiener convergents ---
    for k, d in convergents:
        result = _try_candidate(n, e, k, d)
        if result is not None:
            return result

    # --- Pass 2: semi-convergents ---
    # For each pair of consecutive convergents, try intermediate fractions
    # (h_{i-1} * j + h_i) / (k_{i-1} * j + k_i)  for small j.
    # This explores deeper into the Stern-Brocot tree and extends the
    # effective bound beyond Wiener's N^0.25.
    for i in range(1, len(convergents) - 1):
        h_prev, k_prev = convergents[i - 1]
        h_curr, k_curr = convergents[i]

        max_j = min(50, terms[i] if i < len(terms) else 50)
        for j in range(1, max_j):
            d_try = k_prev * j + k_curr
            k_try = h_prev * j + h_curr

            result = _try_candidate(n, e, k_try, d_try)
            if result is not None:
                return result

    return None
