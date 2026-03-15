"""Rational Sieve.

Historical predecessor to NFS and QS. Simpler but less efficient --
f(x) values are larger than in QS. Included for completeness and
pedagogical value. Complexity: L(n)^1 (subexponential but worse than
QS's L(n)^(1/sqrt(2))).
"""

import math
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent))

from cuneiform.core.accel import gcd, isqrt, powmod, invert
from cuneiform.number_theory.primes import sieve_of_eratosthenes


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _trial_factor(x: int, primes: list[int]) -> list[int] | None:
    """Try to fully factor *x* over *primes*.

    Returns an exponent vector if *x* is smooth, else ``None``.
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


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def factor(
    n: int,
    *,
    bound: int | None = None,
    sieve_range: int = 100_000,
) -> tuple[int, int] | None:
    """Factor *n* using the Rational Sieve.

    The rational sieve finds smooth values of f(x) = x^2 - n by sieving
    over rational integers.  It is essentially a simplified version of QS
    that does not exploit the quadratic polynomial structure, so f(x) values
    grow larger and smoothness is less likely.

    Parameters
    ----------
    n : int
        The integer to factor (must be composite and > 1).
    bound : int | None
        Smoothness bound B for the factor base.  When ``None`` (default),
        B is chosen automatically as ``exp(0.5 * sqrt(ln(n) * ln(ln(n))))``.
    sieve_range : int
        Number of x values to check starting from ceil(sqrt(n)) + 1
        (default: 100,000).

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
        ln_ln_n = math.log(ln_n) if ln_n > 1 else 1.0
        bound = max(100, int(math.exp(0.7 * math.sqrt(ln_n * ln_ln_n))))
        bound = min(bound, 100_000)

    # --- build factor base ---
    factor_base = sieve_of_eratosthenes(bound)
    if not factor_base:
        return None

    fb_len = len(factor_base)
    # +1 for the sign column (f(x) can be negative in theory, but x > sqrt(n)
    # means f(x) > 0; we still track sign for robustness)
    fb_size = fb_len + 1
    needed = fb_size + 1

    # Precompute log values for the sieve
    log_primes = [math.log(p) for p in factor_base]
    log_threshold = math.log(max(2, bound)) * 0.6

    # --- sieve f(x) = x^2 - n for x in [s+1, s+sieve_range] ---
    x_start = s + 1

    # Step 1: Initialize sieve array with log(f(x)) estimates for threshold
    # Step 2: For each prime p in factor base, sieve multiples
    # Step 3: Collect candidates that pass the log threshold

    # We use a log-based sieve.  sieve_log[i] accumulates log(p) for each
    # prime p that divides f(x_start + i).
    sieve_log = [0.0] * sieve_range

    for fi in range(fb_len):
        p = factor_base[fi]
        logp = log_primes[fi]

        # f(x) = x^2 - n ≡ 0 (mod p)  =>  x^2 ≡ n (mod p)
        # Find square roots of n mod p (if they exist)
        n_mod_p = n % p
        if p == 2:
            if n_mod_p % 2 == 0:
                roots = [0]
            else:
                roots = [1]
        else:
            # Euler criterion
            if powmod(n_mod_p, (p - 1) // 2, p) != 1:
                if n_mod_p % p == 0:
                    roots = [0]
                else:
                    continue  # n is not a QR mod p
            else:
                # Tonelli-Shanks for sqrt(n) mod p
                r = _tonelli_shanks_simple(n_mod_p, p)
                if r is None:
                    continue
                roots = [r, p - r]
                if roots[0] == roots[1]:
                    roots = [r]

        for r in roots:
            # f(x) ≡ 0 (mod p) when x ≡ r (mod p)
            # First x >= x_start with x ≡ r (mod p):
            offset = (r - (x_start % p) + p) % p
            j = offset
            while j < sieve_range:
                sieve_log[j] += logp
                j += p

    # --- collect smooth relations ---
    relations: list[tuple[int, list[int]]] = []

    for i in range(sieve_range):
        # Quick log-threshold check
        x = x_start + i
        fx = x * x - n
        if fx <= 0:
            continue

        # Estimate: we want sum of logs of prime factors to be close to log(fx)
        log_fx = math.log(fx) if fx > 1 else 0.0
        if sieve_log[i] < log_fx - log_threshold:
            continue

        # Trial divide
        val = fx
        sign_exp = 0  # f(x) > 0 for x > sqrt(n)

        exps = _trial_factor(val, factor_base)
        if exps is not None:
            full_exps = [sign_exp] + exps
            relations.append((x % n, full_exps))
            if len(relations) >= needed:
                break

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

        # a = product of x values mod n
        a_val = 1
        for idx in involved:
            a_val = (a_val * relations[idx][0]) % n

        # Sum exponent vectors
        combined_exps = [0] * fb_size
        for idx in involved:
            for j in range(fb_size):
                combined_exps[j] += relations[idx][1][j]

        # b = sqrt of the product of f(x) values (mod n)
        b_val = 1
        for j in range(1, fb_size):
            half_exp = combined_exps[j] // 2
            if half_exp > 0:
                b_val = (b_val * powmod(factor_base[j - 1], half_exp, n)) % n

        # Check gcd(a - b, n)
        d = gcd(abs(a_val - b_val) % n, n)
        if 1 < d < n:
            return (d, n // d)

        d = gcd((a_val + b_val) % n, n)
        if 1 < d < n:
            return (d, n // d)

    return None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _tonelli_shanks_simple(n: int, p: int) -> int | None:
    """Compute a square root of *n* mod *p*.

    Returns r with r^2 ≡ n (mod p), or ``None`` if no root exists.
    """
    if p == 2:
        return n % 2
    if n % p == 0:
        return 0
    if powmod(n, (p - 1) // 2, p) != 1:
        return None
    if p % 4 == 3:
        return powmod(n, (p + 1) // 4, p)

    # Factor p-1 = Q * 2^S
    Q, S = p - 1, 0
    while Q % 2 == 0:
        Q //= 2
        S += 1

    z = 2
    while powmod(z, (p - 1) // 2, p) != p - 1:
        z += 1

    M = S
    c = powmod(z, Q, p)
    t = powmod(n, Q, p)
    R = powmod(n, (Q + 1) // 2, p)

    while True:
        if t == 0:
            return 0
        if t == 1:
            return R
        i = 1
        temp = (t * t) % p
        while temp != 1:
            temp = (temp * temp) % p
            i += 1
        b = c
        for _ in range(M - i - 1):
            b = (b * b) % p
        M = i
        c = (b * b) % p
        t = (t * c) % p
        R = (R * b) % p
