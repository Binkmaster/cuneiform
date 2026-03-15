"""Sexagesimal Continued Fraction Factoring — a cuneiform-native technique.

The deepest integration of Babylonian mathematics with modern factoring.

Mathematical foundation:
    Standard CFRAC expands sqrt(N) as a regular continued fraction with natural
    partial quotients. This technique modifies the CF by rounding each
    partial quotient to the NEAREST 5-SMOOTH NUMBER — the "regular numbers"
    of Babylonian base-60 arithmetic.

    In cuneiform mathematics, 5-smooth numbers (2^a * 3^b * 5^c) are the
    numbers with finite reciprocals in base 60. The Babylonian scribes
    organized their entire arithmetic around these numbers. This technique
    applies that principle to factoring.

Cuneiform contributions:
    1. Sexagesimal quotient rounding: partial quotients are biased toward
       5-smooth values, changing the path through the CF lattice.
    2. Hybrid relation collection: gathers smooth relations from BOTH the
       sexagesimal and standard CF expansions simultaneously.
    3. Uses cuneiform's smooth-number infrastructure and regularity
       classification to guide the factoring process.

    The hypothesis: sexagesimal rounding creates convergent numerators A_i
    whose squares A_i^2 mod N have different (potentially more favorable)
    smoothness distributions than standard CFRAC.

Complexity: Same as standard CFRAC ~L(n)^sqrt(2), but with potentially
    different constant factors due to the sexagesimal bias.
"""

import bisect
import math
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent))

from cuneiform.core.accel import gcd, isqrt, powmod
from cuneiform.number_theory.primes import sieve_of_eratosthenes


# ---------------------------------------------------------------------------
# Precomputed 5-smooth number table for fast nearest-smooth lookup
# ---------------------------------------------------------------------------

def _build_smooth_table(limit: int) -> list[int]:
    """Generate all 5-smooth numbers up to *limit*, sorted."""
    result = []
    v2 = 1
    while v2 <= limit:
        v23 = v2
        while v23 <= limit:
            v235 = v23
            while v235 <= limit:
                result.append(v235)
                v235 *= 5
            v23 *= 3
        v2 *= 2
    result.sort()
    return result


# Cache: table of 5-smooth numbers up to some ceiling
_SMOOTH_CACHE: list[int] = []
_SMOOTH_CACHE_LIMIT: int = 0


def _nearest_smooth(a: int) -> int:
    """Find the 5-smooth number nearest to *a* (>= 1)."""
    global _SMOOTH_CACHE, _SMOOTH_CACHE_LIMIT

    if a <= 1:
        return 1

    needed = 2 * a + 10
    if needed > _SMOOTH_CACHE_LIMIT:
        _SMOOTH_CACHE = _build_smooth_table(needed)
        _SMOOTH_CACHE_LIMIT = needed

    idx = bisect.bisect_left(_SMOOTH_CACHE, a)
    best = _SMOOTH_CACHE[0]
    best_dist = abs(a - best)
    for ci in (idx - 1, idx, idx + 1):
        if 0 <= ci < len(_SMOOTH_CACHE):
            dist = abs(a - _SMOOTH_CACHE[ci])
            if dist < best_dist:
                best = _SMOOTH_CACHE[ci]
                best_dist = dist

    return best if best >= 1 else 1


# ---------------------------------------------------------------------------
# Legendre symbol
# ---------------------------------------------------------------------------

def _legendre(a: int, p: int) -> int:
    """Compute the Legendre symbol (a/p) using Euler's criterion."""
    if p == 2:
        return a % 2
    val = powmod(a % p, (p - 1) // 2, p)
    if val == p - 1:
        return -1
    return val  # 0 or 1


# ---------------------------------------------------------------------------
# Trial factoring over a factor base
# ---------------------------------------------------------------------------

def _trial_factor_with_sign(
    val: int, sign: int, factor_base: list[int]
) -> list[int] | None:
    """Factor *val* over *factor_base*, return exponent vector or None.

    *factor_base* must have -1 as its first element. *sign* indicates
    whether the original value was negative (-1) or positive (+1).
    """
    if val == 0:
        return None

    exponents = [0] * len(factor_base)

    # Handle sign: index 0 is -1
    if sign < 0:
        exponents[0] = 1

    remaining = val
    for i, p in enumerate(factor_base):
        if p < 2:
            continue  # skip -1
        while remaining % p == 0:
            remaining //= p
            exponents[i] += 1

    if remaining == 1:
        return exponents
    return None  # not smooth


# ---------------------------------------------------------------------------
# GF(2) Gaussian elimination
# ---------------------------------------------------------------------------

def _gauss_elim_gf2(
    matrix: list[list[int]], history: list[list[int]]
) -> list[list[int]]:
    """Row-reduce *matrix* over GF(2), tracking combinations in *history*.

    Returns history rows corresponding to zero rows (linear dependencies).
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
# Factor extraction from dependencies
# ---------------------------------------------------------------------------

def _solve_and_extract(
    n: int,
    relations: list[tuple[int, list[int]]],
    factor_base: list[int],
) -> tuple[int, int] | None:
    """GF(2) elimination on relation exponents, try to extract a factor."""
    fb_size = len(factor_base)
    num_rels = len(relations)

    # Build matrix of exponent vectors mod 2
    matrix = [[e % 2 for e in rel[1]] for rel in relations]
    history = [
        [1 if i == j else 0 for j in range(num_rels)] for i in range(num_rels)
    ]

    deps = _gauss_elim_gf2(matrix, history)

    for dep in deps:
        involved = [i for i in range(num_rels) if dep[i]]
        if len(involved) < 2:
            continue

        # a = product of A values mod n
        a_product = 1
        combined_exp = [0] * fb_size
        for idx in involved:
            a_val, exp_vec = relations[idx]
            a_product = (a_product * a_val) % n
            for j in range(fb_size):
                combined_exp[j] += exp_vec[j]

        # b = sqrt of the product of Q values (mod n)
        b_product = 1
        for j, p in enumerate(factor_base):
            if p == -1:
                continue
            half_exp = combined_exp[j] // 2
            if half_exp > 0:
                b_product = (b_product * powmod(p, half_exp, n)) % n

        # Check gcd(a - b, n) and gcd(a + b, n)
        d = gcd(abs(a_product - b_product) % n, n)
        if 1 < d < n:
            return (d, n // d)
        d = gcd((a_product + b_product) % n, n)
        if 1 < d < n:
            return (d, n // d)

    return None


# ---------------------------------------------------------------------------
# Main factoring routine
# ---------------------------------------------------------------------------

def factor(
    n: int,
    *,
    bound: int | None = None,
    max_terms: int = 500_000,
) -> tuple[int, int] | None:
    """Factor *n* using the sexagesimal continued fraction method.

    Parameters
    ----------
    n : int
        The integer to factor (must be composite and > 1).
    bound : int | None
        Smoothness bound B for the factor base.  When ``None`` (default),
        B is chosen automatically as ``exp(0.5 * sqrt(ln(n) * ln(ln(n))))``.
    max_terms : int
        Maximum number of CF terms to expand (default: 500,000).

    Returns
    -------
    tuple[int, int] | None
        A pair ``(p, n // p)`` with ``1 < p < n``, or ``None`` if no
        factor was found.
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
        ln_n = math.log(n) if n > 1 else 1.0
        ln_ln_n = math.log(ln_n) if ln_n > 1 else 1.0
        # Use a slightly more generous multiplier than standard CFRAC (0.65
        # vs 0.5) because the sexagesimal rounding changes the CF path and
        # we need a larger factor base to compensate.
        bound = max(100, int(math.exp(0.65 * math.sqrt(ln_n * ln_ln_n))))
        bound = min(bound, 100_000)

    # --- build factor base ---
    # Include -1 for sign, then primes p <= bound where n is a QR mod p.
    all_primes = sieve_of_eratosthenes(bound)
    factor_base: list[int] = [-1]  # index 0 = sign
    for p in all_primes:
        leg = _legendre(n, p)
        if leg == 0 or leg == 1:
            factor_base.append(p)

    fb_size = len(factor_base)
    needed = fb_size + 5  # collect a few extra relations for robustness

    # --- continued fraction expansion of sqrt(n) ---
    a0 = s  # floor(sqrt(n))

    P_cur = a0
    Q_prev = 1
    Q_cur = n - a0 * a0

    if Q_cur == 0:
        return None  # perfect square, already handled

    # Convergent numerators (mod n)
    A_prev2 = 1    # A_{-1}
    A_prev1 = a0   # A_0

    # Collect smooth relations: (A_value_mod_n, exponent_vector)
    relations: list[tuple[int, list[int]]] = []

    for i in range(1, max_terms + 1):
        if Q_cur == 0:
            break

        # --- standard partial quotient ---
        a_standard = (a0 + P_cur) // Q_cur

        # --- SEXAGESIMAL TWIST: round to nearest 5-smooth number ---
        a_sexa = _nearest_smooth(a_standard)

        # --- update convergent with sexagesimal quotient ---
        A_sexa = (a_sexa * A_prev1 + A_prev2) % n

        # Compute Q_i = A_sexa^2 mod n (symmetric representative)
        Q_sexa = (A_sexa * A_sexa) % n
        if Q_sexa > n // 2:
            Q_sexa = n - Q_sexa
            sexa_sign = -1
        else:
            sexa_sign = 1

        # Try to factor Q_sexa over factor base
        exps_sexa = _trial_factor_with_sign(Q_sexa, sexa_sign, factor_base)
        if exps_sexa is not None:
            relations.append((A_sexa, exps_sexa))
            if len(relations) >= needed:
                result = _solve_and_extract(n, relations, factor_base)
                if result:
                    return result

        # --- also try with STANDARD quotient (hybrid approach) ---
        A_std = (a_standard * A_prev1 + A_prev2) % n
        if A_std != A_sexa:
            Q_std = (A_std * A_std) % n
            if Q_std > n // 2:
                Q_std = n - Q_std
                std_sign = -1
            else:
                std_sign = 1

            exps_std = _trial_factor_with_sign(Q_std, std_sign, factor_base)
            if exps_std is not None:
                relations.append((A_std, exps_std))
                if len(relations) >= needed:
                    result = _solve_and_extract(n, relations, factor_base)
                    if result:
                        return result

        # --- advance CF state with STANDARD quotient ---
        # (standard quotient maintains the exact CF recurrence)
        P_next = a_standard * Q_cur - P_cur
        Q_next = Q_prev + a_standard * (P_cur - P_next)

        P_cur = P_next
        Q_prev = Q_cur
        Q_cur = Q_next

        # Advance convergent tracking using the sexagesimal convergent
        A_prev2 = A_prev1
        A_prev1 = A_sexa

    # Final attempt if we have enough relations
    if len(relations) > fb_size:
        result = _solve_and_extract(n, relations, factor_base)
        if result:
            return result

    return None


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import time

    tests = [
        ("small",  1009 * 2003),            # 2_021_027
        ("medium", 10007 * 20011),          # 200_290_077
        ("larger", 100003 * 200017),        # 20_003_300_051
    ]

    for label, n in tests:
        print(f"\n--- {label}: n = {n} ---")
        t0 = time.perf_counter()
        result = factor(n)
        elapsed = time.perf_counter() - t0
        if result:
            p, q = result
            assert p * q == n, f"WRONG: {p} * {q} != {n}"
            print(f"  factors: {p} x {q}  ({elapsed:.4f}s)")
        else:
            print(f"  FAILED to factor  ({elapsed:.4f}s)")
