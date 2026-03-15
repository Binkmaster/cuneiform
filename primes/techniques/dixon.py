"""Dixon's random squares factoring method (1981).

The foundational random-squares algorithm that influenced all later
sub-exponential factoring techniques including the Quadratic Sieve (QS)
and the General Number Field Sieve (GNFS).

Complexity: L(n)^(sqrt(2))  where  L(n) = exp(sqrt(ln(n) * ln(ln(n)))).

How it works:
    1. Choose a factor base of small primes up to a smoothness bound B.
    2. Collect B-smooth relations: random x values where x^2 mod n factors
       completely over the factor base.
    3. Once enough relations are gathered (more than |factor_base|), build
       an exponent matrix mod 2 and find a linear dependency via Gaussian
       elimination over GF(2).
    4. Combine the dependent relations to form a^2 ≡ b^2 (mod n), then
       check whether gcd(a - b, n) yields a non-trivial factor.

When it works best:
    - Educational / reference implementation of the random-squares paradigm.
    - Practical for integers up to ~40-50 digits; beyond that the Quadratic
      Sieve supersedes it by generating smooth values more efficiently.
"""

import math
import random
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent))

from cuneiform.core.accel import gcd, isqrt, powmod
from cuneiform.number_theory.primes import sieve_of_eratosthenes


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

    *matrix* is a list of rows, each a list of 0/1 ints.  *history* tracks
    which original rows have been XOR-combined into each current row (same
    dimensions as *matrix* — one entry per original row).

    Returns a list of *history* rows corresponding to zero rows in the
    reduced matrix (i.e. linear dependencies).
    """
    nrows = len(matrix)
    ncols = len(matrix[0]) if nrows else 0
    pivot_row = 0

    for col in range(ncols):
        # Find a pivot in this column at or below pivot_row
        found = -1
        for row in range(pivot_row, nrows):
            if matrix[row][col]:
                found = row
                break
        if found == -1:
            continue

        # Swap pivot into position
        matrix[pivot_row], matrix[found] = matrix[found], matrix[pivot_row]
        history[pivot_row], history[found] = history[found], history[pivot_row]

        # Eliminate this column in all other rows
        for row in range(nrows):
            if row != pivot_row and matrix[row][col]:
                matrix[row] = [a ^ b for a, b in zip(matrix[row], matrix[pivot_row])]
                history[row] = [a ^ b for a, b in zip(history[row], history[pivot_row])]

        pivot_row += 1

    # Collect dependencies: rows that are now all-zero
    deps = []
    for i in range(nrows):
        if not any(matrix[i]):
            deps.append(history[i])
    return deps


def factor(
    n: int,
    *,
    bound: int | None = None,
    max_attempts: int = 1_000_000,
) -> tuple[int, int] | None:
    """Factor *n* using Dixon's random squares method.

    Parameters
    ----------
    n : int
        The integer to factor (must be composite and > 1).
    bound : int | None
        Smoothness bound B for the factor base.  When ``None`` (default),
        B is chosen automatically as ``exp(0.5 * sqrt(ln(n) * ln(ln(n))))``.
    max_attempts : int
        Maximum number of random x values to try when searching for
        smooth relations (default: 1,000,000).

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

    # --- smoothness bound ---
    if bound is None:
        ln_n = math.log(n)
        ln_ln_n = math.log(ln_n)
        bound = max(10, int(math.exp(0.5 * math.sqrt(ln_n * ln_ln_n))))

    factor_base = sieve_of_eratosthenes(bound)
    if not factor_base:
        return None
    fb_len = len(factor_base)
    needed = fb_len + 1  # need more relations than primes

    # --- collect smooth relations ---
    # Each relation: (x, exponent_vector) where x^2 mod n is smooth
    relations: list[tuple[int, list[int]]] = []

    for _ in range(max_attempts):
        x = random.randint(2, n - 1)
        x2 = (x * x) % n
        if x2 == 0:
            # x is a multiple of n (degenerate)
            continue
        exps = _trial_factor(x2, factor_base)
        if exps is not None:
            relations.append((x, exps))
            if len(relations) >= needed:
                break
    else:
        # Not enough smooth relations found
        if len(relations) <= fb_len:
            return None

    # --- build exponent matrix mod 2 ---
    matrix = [[e % 2 for e in rel[1]] for rel in relations]
    num_rels = len(relations)
    # History: identity matrix to track which relations are combined
    history = [[1 if i == j else 0 for j in range(num_rels)] for i in range(num_rels)]

    deps = _gauss_elim_gf2(matrix, history)

    # --- try each dependency ---
    for dep in deps:
        # Collect the relations involved in this dependency
        involved = [i for i in range(num_rels) if dep[i]]
        if not involved:
            continue

        # a = product of x_i mod n
        a = 1
        for i in involved:
            a = (a * relations[i][0]) % n

        # Sum exponent vectors to get the squared product's factorisation
        combined_exps = [0] * fb_len
        for i in involved:
            for j in range(fb_len):
                combined_exps[j] += relations[i][1][j]

        # b = sqrt of the product (each combined exponent must be even)
        b = 1
        for j in range(fb_len):
            half_exp = combined_exps[j] // 2
            if half_exp > 0:
                b = (b * powmod(factor_base[j], half_exp, n)) % n

        # Check gcd(a - b, n)
        d = gcd(abs(a - b) % n, n)
        if 1 < d < n:
            return (d, n // d)

        # Also try a + b
        d = gcd((a + b) % n, n)
        if 1 < d < n:
            return (d, n // d)

    return None
