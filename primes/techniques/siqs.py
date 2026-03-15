"""SIQS (Contini, 1996).

Self-Initializing Quadratic Sieve -- the fastest QS variant.
Key insight: switch polynomials by sign-flipping one factor of 'a',
updating sieve roots in O(|FB|) instead of full recomputation.
Practical workhorse for 50-100 digit factorizations.
"""

import math
import random
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent))

from cuneiform.core.accel import gcd, isqrt, powmod, invert
from cuneiform.number_theory.primes import sieve_of_eratosthenes


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tonelli_shanks(n: int, p: int) -> int | None:
    """Compute a square root of *n* mod *p* using Tonelli-Shanks.

    Returns an integer r with r^2 ≡ n (mod p), or ``None`` if *n* is
    not a quadratic residue mod *p*.
    """
    if p == 2:
        return n % 2
    # Check Euler criterion
    if powmod(n % p, (p - 1) // 2, p) != 1:
        return None
    if p % 4 == 3:
        return powmod(n % p, (p + 1) // 4, p)

    # Factor out powers of 2 from p-1: p-1 = Q * 2^S
    Q, S = p - 1, 0
    while Q % 2 == 0:
        Q //= 2
        S += 1

    # Find a quadratic non-residue z
    z = 2
    while powmod(z, (p - 1) // 2, p) != p - 1:
        z += 1

    M = S
    c = powmod(z, Q, p)
    t = powmod(n % p, Q, p)
    R = powmod(n % p, (Q + 1) // 2, p)

    while True:
        if t == 0:
            return 0
        if t == 1:
            return R
        # Find least i such that t^(2^i) == 1
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


def _legendre(a: int, p: int) -> int:
    """Compute the Legendre symbol (a/p)."""
    if p == 2:
        return a % 2
    val = powmod(a % p, (p - 1) // 2, p)
    if val == p - 1:
        return -1
    return val  # 0 or 1


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
    sieve_range: int | None = None,
    num_factors_a: int | None = None,
) -> tuple[int, int] | None:
    """Factor *n* using the Self-Initializing Quadratic Sieve (SIQS).

    Parameters
    ----------
    n : int
        The integer to factor (must be composite and > 1).
    bound : int | None
        Smoothness bound for the factor base.  When ``None`` the sieve
        auto-computes an appropriate value from the size of *n*.
    sieve_range : int | None
        Half-width M of the sieve interval [-M, M].  When ``None``
        the sieve chooses a default proportional to the bound.
    num_factors_a : int | None
        Number of primes whose product forms 'a' in each polynomial.
        When ``None``, chosen automatically based on the size of *n*.

    Returns
    -------
    tuple[int, int] | None
        A pair (p, q) with p * q == n, or ``None`` if the sieve did
        not find enough relations to produce a factorisation.
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

    # --- auto-tune parameters ---
    ln_n = math.log(n)
    ln_ln_n = math.log(ln_n) if ln_n > 1 else 1.0

    if bound is None:
        # L(n)^(1/sqrt(2)) heuristic, capped for pure-Python feasibility
        bound = max(200, int(math.exp(0.7 * math.sqrt(ln_n * ln_ln_n))))
        bound = min(bound, 100_000)

    if sieve_range is None:
        sieve_range = max(10_000, bound * 20)

    # --- build factor base ---
    all_primes = sieve_of_eratosthenes(bound)
    factor_base: list[int] = []
    fb_sqrts: list[int] = []  # sqrt(n) mod p for each FB prime

    for p in all_primes:
        leg = _legendre(n, p)
        if leg < 0:
            continue
        if leg == 0:
            # p divides n — immediate factor
            if 1 < p < n:
                return (p, n // p)
            continue
        r = _tonelli_shanks(n, p)
        if r is not None:
            factor_base.append(p)
            fb_sqrts.append(r)

    if not factor_base:
        return None

    fb_len = len(factor_base)
    # +1 for the sign column
    fb_size = fb_len + 1
    needed = fb_size + 1

    # --- choose number of primes in 'a' ---
    if num_factors_a is None:
        digit_count = len(str(n))
        if digit_count < 30:
            num_factors_a = 2
        elif digit_count < 50:
            num_factors_a = 3
        elif digit_count < 70:
            num_factors_a = 4
        else:
            num_factors_a = 5

    # Select a pool of candidate primes for constructing 'a'.
    # We want primes from the middle of the factor base so that 'a' is
    # not too small or too large.  Target: a ≈ sqrt(2n) / M.
    target_a = isqrt(2 * n) // sieve_range
    if target_a < 2:
        target_a = 2

    # Pick primes from the upper portion of the factor base
    min_idx = max(2, fb_len // 4)
    a_pool_indices = list(range(min_idx, fb_len))
    if len(a_pool_indices) < num_factors_a:
        # Not enough primes — fall back to smaller factor count
        num_factors_a = max(1, len(a_pool_indices))

    M = sieve_range

    # Logarithmic threshold for sieve: Q(x) ≈ sqrt(2n)/a at the edges,
    # so log(|Q(x)|) ≈ log(M * sqrt(2n/a_target)).  We accept candidates
    # whose accumulated log is within a tolerance of this expected value.
    log_primes = [math.log(p) for p in factor_base]
    log_tolerance = math.log(max(2, bound)) * 0.8

    # --- collect smooth relations ---
    # relation: (x_value, sign, exponent_vector)
    #   where (a*x + b)^2 - n = a * Q(x) and Q(x) is smooth
    relations: list[tuple[int, list[int]]] = []

    max_polynomials = max(200, needed * 10)

    for _poly_iter in range(max_polynomials):
        if len(relations) >= needed:
            break

        # --- construct polynomial g(x) = (a*x + b)^2 - n ---
        # Choose s distinct primes from the pool for 'a'
        if len(a_pool_indices) < num_factors_a:
            break
        chosen_indices = random.sample(a_pool_indices, num_factors_a)
        chosen_primes = [factor_base[i] for i in chosen_indices]

        a = 1
        for q in chosen_primes:
            a *= q

        # Compute b via CRT: b^2 ≡ n (mod q_i) for each q_i
        # Use Garner's algorithm / CRT
        b_residues = []
        for i, qi in enumerate(chosen_primes):
            ri = _tonelli_shanks(n, qi)
            if ri is None:
                break
            b_residues.append(ri)
        else:
            # CRT to combine: find b such that b ≡ r_i (mod q_i)
            b = 0
            for i, qi in enumerate(chosen_primes):
                # Partial product of all other q_j
                Mi = a // qi
                Mi_inv = invert(Mi, qi)
                if Mi_inv is None:
                    break
                b = (b + b_residues[i] * Mi * Mi_inv) % a
            else:
                # Ensure b^2 ≡ n (mod a)
                if (b * b - n) % a != 0:
                    # Try negative root for one of them
                    b = a - b
                    if (b * b - n) % a != 0:
                        continue

                # Precompute B_j values for self-initialization
                # B_j = b' where b' ≡ sqrt(n) (mod q_j) lifted via CRT
                B_vals = []
                for j, qj in enumerate(chosen_primes):
                    Mj = a // qj
                    Mj_inv = invert(Mj, qj)
                    if Mj_inv is None:
                        break
                    B_vals.append((b_residues[j] * Mj * Mj_inv) % a)
                else:
                    pass  # B_vals computed successfully

                if len(B_vals) != num_factors_a:
                    continue

                # Compute exponent vector for 'a' over factor base.
                # (ax+b)^2 ≡ a*Q(x) (mod n), so we track a*Q(x).
                a_exps = [0] * fb_len
                a_tmp = a
                for fi, p in enumerate(factor_base):
                    while a_tmp % p == 0:
                        a_tmp //= p
                        a_exps[fi] += 1

                # Compute inverse of a mod each factor base prime
                a_inv = []
                for p in factor_base:
                    ai = invert(a % p, p) if a % p != 0 else None
                    a_inv.append(ai)

                # Generate 2^(s-1) polynomials by flipping signs of B_j
                num_b_variants = 1 << (num_factors_a - 1)
                current_b = b

                for variant in range(num_b_variants):
                    if len(relations) >= needed:
                        break

                    if variant > 0:
                        # Self-initialization: flip sign of one B_j
                        # Find which bit changed
                        gray_prev = (variant - 1) ^ ((variant - 1) >> 1)
                        gray_curr = variant ^ (variant >> 1)
                        changed_bit = (gray_prev ^ gray_curr).bit_length() - 1

                        if changed_bit < len(B_vals):
                            if (gray_curr >> changed_bit) & 1:
                                current_b = (current_b - 2 * B_vals[changed_bit]) % a
                            else:
                                current_b = (current_b + 2 * B_vals[changed_bit]) % a

                    # Compute sieve roots for this polynomial
                    # g(x) = a*x^2 + 2*b*x + c  where c = (b^2 - n) / a
                    c_val = (current_b * current_b - n) // a

                    # --- sieve ---
                    # We sieve f(x) = a*x + current_b values, looking for
                    # Q(x) = (a*x + current_b)^2 - n = a*(a*x^2 + 2*current_b*x + c_val)
                    # that are smooth.  Actually we sieve the polynomial
                    # Q(x) = a*x^2 + 2*current_b*x + c_val and look for
                    # a*Q(x) to be smooth (since (ax+b)^2 - n = a*Q(x)).

                    sieve_log = [0.0] * (2 * M)

                    for fi in range(fb_len):
                        p = factor_base[fi]
                        if a_inv[fi] is None:
                            continue
                        r = fb_sqrts[fi]
                        ainv = a_inv[fi]
                        logp = log_primes[fi]

                        # Sieve roots: a*x + b ≡ ±r (mod p)
                        # x ≡ (±r - b) * a^{-1} (mod p)
                        root1 = ((r - current_b) * ainv) % p
                        root2 = ((-r - current_b) * ainv) % p

                        # Sieve from root1 + M offset, root2 + M offset
                        start1 = ((root1 - (-M)) % p)
                        start2 = ((root2 - (-M)) % p)

                        j = start1
                        while j < 2 * M:
                            sieve_log[j] += logp
                            j += p

                        if root1 != root2:
                            j = start2
                            while j < 2 * M:
                                sieve_log[j] += logp
                                j += p

                    # --- trial divide candidates ---
                    for idx in range(2 * M):
                        x = idx - M
                        # Q(x) = a*x^2 + 2*b*x + c
                        Qx = a * x * x + 2 * current_b * x + c_val
                        if Qx == 0:
                            continue

                        val = abs(Qx)
                        # Threshold: accumulated log should be close to log(|Q(x)|)
                        log_Qx = math.log(val) if val > 1 else 0.0
                        if sieve_log[idx] < log_Qx - log_tolerance:
                            continue

                        # We need (ax + b)^2 ≡ n (mod n) with Q(x) smooth
                        # Actually (ax+b)^2 - n = a * Q(x)
                        ax_b = (a * x + current_b) % n

                        sign_exp = 1 if Qx < 0 else 0

                        exps = _trial_factor(val, factor_base)
                        if exps is not None:
                            # Combine a's exponents with Q(x)'s: a*Q(x) is the full product
                            combined = [sign_exp] + [ae + qe for ae, qe in zip(a_exps, exps)]
                            relations.append((ax_b, combined))
                            if len(relations) >= needed:
                                break

                continue  # next polynomial (after inner loop)
        # If CRT failed (break from for-else), try next polynomial
        continue

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

        # a_val = product of (ax + b) values mod n
        a_val = 1
        for idx in involved:
            a_val = (a_val * relations[idx][0]) % n

        # Sum exponent vectors
        combined_exps = [0] * fb_size
        for idx in involved:
            for j in range(fb_size):
                combined_exps[j] += relations[idx][1][j]

        # b_val = sqrt of the product of |Q(x)| values (mod n)
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
