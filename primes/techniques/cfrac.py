"""CFRAC (Morrison & Brillhart, 1975).

First subexponential factoring algorithm. Complexity ~L(n)^sqrt(2).
Largely obsoleted by QS but historically important and simpler to implement.

Uses the continued fraction expansion of sqrt(n) to find smooth relations.
Each convergent numerator A_i satisfies A_{i-1}^2 ≡ (-1)^i * Q_i (mod n),
so smooth Q_i values yield congruences of squares after combining via
Gaussian elimination over GF(2).
"""

import math
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent))

from cuneiform.core.accel import gcd, isqrt, powmod
from cuneiform.number_theory.primes import sieve_of_eratosthenes


def _legendre(a: int, p: int) -> int:
    """Compute the Legendre symbol (a/p) using Euler's criterion."""
    if p == 2:
        return a % 2
    val = powmod(a % p, (p - 1) // 2, p)
    if val == p - 1:
        return -1
    return val  # 0 or 1


def _trial_factor(x: int, primes: list[int]) -> list[int] | None:
    """Try to fully factor *x* over *primes*.

    Returns an exponent vector (one entry per prime) if *x* is smooth
    over the factor base, or ``None`` if a cofactor remains.
    """
    exponents = [0] * len(primes)
    remainder = x
    for i, p in enumerate(primes):
        while remainder % p == 0:
            remainder //= p
            exponents[i] += 1
    if remainder != 1:
        return None
    return exponents


def _gauss_elim_gf2(
    matrix: list[list[int]], history: list[list[int]]
) -> list[list[int]]:
    """Row-reduce *matrix* over GF(2), tracking row combinations in *history*.

    Returns a list of *history* rows corresponding to zero rows in the
    reduced matrix (i.e. linear dependencies).
    """
    nrows = len(matrix)
    ncols = len(matrix[0]) if nrows else 0
    pivot_row = 0

    for col in range(ncols):
        found = -1
        for row in range(pivot_row, nrows):
            if matrix[row][col]:
                found = row
                break
        if found == -1:
            continue

        matrix[pivot_row], matrix[found] = matrix[found], matrix[pivot_row]
        history[pivot_row], history[found] = history[found], history[pivot_row]

        for row in range(nrows):
            if row != pivot_row and matrix[row][col]:
                matrix[row] = [a ^ b for a, b in zip(matrix[row], matrix[pivot_row])]
                history[row] = [a ^ b for a, b in zip(history[row], history[pivot_row])]

        pivot_row += 1

    deps = []
    for i in range(nrows):
        if not any(matrix[i]):
            deps.append(history[i])
    return deps


def factor(
    n: int,
    *,
    bound: int | None = None,
    max_terms: int = 1_000_000,
) -> tuple[int, int] | None:
    """Factor *n* using the continued fraction (CFRAC) method.

    Parameters
    ----------
    n : int
        The integer to factor (must be composite and > 1).
    bound : int | None
        Smoothness bound B for the factor base.  When ``None`` (default),
        B is chosen automatically as ``exp(0.5 * sqrt(ln(n) * ln(ln(n))))``.
    max_terms : int
        Maximum number of continued fraction terms to expand (default:
        1,000,000).

    Returns
    -------
    tuple[int, int] | None
        A pair (p, n // p) with 1 < p < n, or ``None`` if no factor was found.
    """
    # --- trivial / small checks ---
    if n < 4:
        return None
    g = gcd(n, 6)
    if 1 < g < n:
        return (g, n // g)

    # Check for perfect square
    s = isqrt(n)
    if s * s == n:
        return (s, s)

    # --- smoothness bound ---
    if bound is None:
        ln_n = math.log(n)
        ln_ln_n = math.log(ln_n)
        bound = max(10, int(math.exp(0.5 * math.sqrt(ln_n * ln_ln_n))))

    # --- build factor base ---
    # Include only primes p where n is a quadratic residue mod p (or p divides n).
    # Index 0 in the exponent vector represents the sign (-1).
    all_primes = sieve_of_eratosthenes(bound)
    factor_base: list[int] = []
    for p in all_primes:
        leg = _legendre(n, p)
        if leg == 0 or leg == 1:
            factor_base.append(p)

    if not factor_base:
        return None

    # fb_size includes the -1 entry for sign
    fb_size = len(factor_base) + 1  # +1 for the -1 sign column
    needed = fb_size + 1  # need more relations than factor base size

    # --- continued fraction expansion of sqrt(n) ---
    # Standard CF recurrence for sqrt(n):
    #   a0 = floor(sqrt(n))
    #   P_0 = 0, Q_0 = 1
    #   a_i = floor((a0 + P_i) / Q_i)
    #   P_{i+1} = a_i * Q_i - P_i
    #   Q_{i+1} = Q_{i_prev} + a_i * (P_i - P_{i+1})
    #
    # Convergent numerators (mod n):
    #   A_{-1} = 1, A_0 = a0
    #   A_i = a_i * A_{i-1} + A_{i-2}  (mod n)
    #
    # Key identity: A_{i-1}^2 ≡ (-1)^i * Q_i (mod n)

    a0 = s  # floor(sqrt(n))

    P_prev = 0
    Q_prev = 1
    P_cur = a0
    Q_cur = n - a0 * a0

    if Q_cur == 0:
        # n is a perfect square — already handled above
        return None

    A_prev2 = 1       # A_{-1}
    A_prev1 = a0      # A_0

    # Collect smooth relations: (A_value_mod_n, exponent_vector)
    # exponent_vector[0] = exponent of -1 (sign), rest = exponents of factor_base primes
    relations: list[tuple[int, list[int]]] = []

    for i in range(1, max_terms + 1):
        a_i = (a0 + P_cur) // Q_cur
        P_next = a_i * Q_cur - P_cur
        Q_next = Q_prev + a_i * (P_cur - P_next)

        # Convergent numerator mod n
        A_cur = (a_i * A_prev1 + A_prev2) % n

        # The remainder to factor is Q_cur (the current partial denominator).
        # A_{i-1}^2 ≡ (-1)^i * Q_i (mod n)
        # So we need to factor Q_cur over the factor base and track the sign.
        q_val = Q_cur
        sign_exp = i % 2  # (-1)^i: odd i means negative, exponent of -1 is 1

        exps = _trial_factor(q_val, factor_base)
        if exps is not None:
            # Prepend the sign exponent
            full_exps = [sign_exp] + exps
            # The A value corresponding to this relation is A_{i-1}
            relations.append((A_prev1 % n, full_exps))
            if len(relations) >= needed:
                break

        # Advance the recurrence
        P_prev = P_cur
        Q_prev = Q_cur
        P_cur = P_next
        Q_cur = Q_next
        A_prev2 = A_prev1
        A_prev1 = A_cur

        # CF expansion of sqrt(n) is periodic; if Q_cur == 1 we've completed
        # a period. This is fine, we just keep going.

    if len(relations) <= fb_size:
        return None

    # --- build exponent matrix mod 2 ---
    num_rels = len(relations)
    matrix = [[e % 2 for e in rel[1]] for rel in relations]
    history = [[1 if i == j else 0 for j in range(num_rels)] for i in range(num_rels)]

    deps = _gauss_elim_gf2(matrix, history)

    # --- try each dependency ---
    for dep in deps:
        involved = [i for i in range(num_rels) if dep[i]]
        if not involved:
            continue

        # a = product of A values mod n
        a = 1
        for idx in involved:
            a = (a * relations[idx][0]) % n

        # Sum exponent vectors to get the combined factorisation
        combined_exps = [0] * fb_size
        for idx in involved:
            for j in range(fb_size):
                combined_exps[j] += relations[idx][1][j]

        # b = sqrt of the product of Q values (mod n)
        # combined_exps[0] is the total sign exponent — must be even for a square
        # (guaranteed by GF(2) elimination)
        b = 1
        for j in range(1, fb_size):
            half_exp = combined_exps[j] // 2
            if half_exp > 0:
                b = (b * powmod(factor_base[j - 1], half_exp, n)) % n

        # Check gcd(a - b, n)
        d = gcd(abs(a - b) % n, n)
        if 1 < d < n:
            return (d, n // d)

        # Also try a + b
        d = gcd((a + b) % n, n)
        if 1 < d < n:
            return (d, n // d)

    return None
