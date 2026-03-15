"""Babylonian Smooth-Power GCD Cascade — cuneiform-native factoring.

Deeply rooted in the Babylonian sexagesimal number system.

Mathematical foundation:
    The Babylonians computed in base 60 = 2^2 * 3 * 5. Their "regular
    numbers" (those with finite base-60 reciprocals) are exactly the
    5-smooth numbers: 2^a * 3^b * 5^c.

    This technique exploits 5-smooth structure for factoring: instead of
    exponentiating by ALL primes (Pollard p-1), exponentiate exclusively
    by the BABYLONIAN PRIMES {2, 3, 5} to extreme powers.

Cuneiform contributions:
    1. Babylonian exponent ladder: systematically covers all 5-smooth
       orders by sequential exponentiation: first 2^A, then 3^B, then 5^C.
       Catches factors where ord_p(g) is 5-smooth.
    2. Base-60 power orbit: separately tests g^(60^k) — the natural
       "Babylonian iteration" — which probes orders dividing 60^k.
    3. Multi-base with Babylonian-significant starting values: uses
       bases like 60, 360, 720 (Babylonian round numbers) alongside
       small primes.
    4. Irregular prime extension: after the smooth cascade, multiply
       by small non-Babylonian primes (7, 11, 13, ...) to catch
       "almost-smooth" orders.

    Key difference from Pollard p-1: standard p-1 with bound B requires
    ALL prime factors of (p-1) to be <= B. This method requires only that
    ord_p(g) be 5-smooth (or almost-smooth). Since ord_p(g) is a DIVISOR
    of (p-1), not necessarily (p-1) itself, this catches cases where p-1
    has large prime factors but g's order doesn't.

Complexity: O(A + B + C) exponentiations per base, where A, B, C are
    the max powers of 2, 3, 5. With max_power=100, this probes all
    5-smooth orders up to 2^100 * 3^100 * 5^100 ~ 10^97.
"""

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent))

from cuneiform.core.accel import gcd, isqrt, powmod, is_probable_prime


# Bases include Babylonian-significant numbers (multiples of 60) alongside
# small primes.  The variety of starting points maximises the chance that
# at least one base has a 5-smooth order mod an unknown factor p.
_BASE_CANDIDATES = [
    2, 3, 5, 6, 7, 10, 11, 12, 13, 15, 17, 19, 23, 29,
    30, 31, 37, 41, 43, 47,
    60, 120, 180, 240, 360, 720,
]

# Small primes NOT dividing 60 — used in the "irregular" extension phase
# to catch orders that are *almost* 5-smooth.
_IRREGULAR_PRIMES = [7, 11, 13, 17, 19, 23, 29, 31]

# GCD batch size: accumulate this many (val - 1) products before checking.
_BATCH_SIZE = 10


def factor(n: int, *, num_bases: int = 20, max_power: int = 100) -> tuple[int, int] | None:
    """Factor *n* using the Babylonian smooth-power GCD cascade.

    Parameters
    ----------
    n : int
        The integer to factor (must be composite and > 1).
    num_bases : int
        How many starting bases to try before giving up.
    max_power : int
        Maximum exponent for each Babylonian prime in the ladder.
        The method probes 5-smooth orders up to 2^max_power *
        3^max_power * 5^max_power.

    Returns
    -------
    tuple[int, int] | None
        A pair (p, n // p) with 1 < p < n, or None if no factor was found.
    """
    # ---- Trivial / edge cases ----
    if n < 2:
        return None
    for small in (2, 3, 5):
        if n % small == 0 and n != small:
            return (small, n // small)
    s = isqrt(n)
    if s * s == n:
        return (s, s)
    if is_probable_prime(n):
        return None

    # ---- Main multi-base loop ----
    for base_idx in range(num_bases):
        g = _choose_base(n, base_idx)
        if g is None:
            continue

        # If the base itself shares a factor with n, we're done.
        d = gcd(g, n)
        if 1 < d < n:
            return (d, n // d)
        if d == n:
            continue

        result = _babylon_cascade(g, n, max_power)
        if result is not None:
            return result

    return None


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _choose_base(n: int, index: int) -> int | None:
    """Return a candidate base, or None to skip this index."""
    g = _BASE_CANDIDATES[index % len(_BASE_CANDIDATES)]
    d = gcd(g, n)
    if d == n:
        return None
    if 1 < d < n:
        # g shares a non-trivial factor — caller will extract it.
        return g
    return g


def _babylon_cascade(g: int, n: int, max_power: int) -> tuple[int, int] | None:
    """Run the full Babylonian cascade for a single base *g*."""

    # Phase 1 — powers of 2: val = g^(2^a)
    val, result = _exponentiate_prime_phase(g, 2, max_power, n)
    if result is not None:
        return result

    # Phase 2 — powers of 3 on top: val = g^(2^A * 3^b)
    val_after_2 = val
    val, result = _exponentiate_prime_phase(val_after_2, 3, max_power, n)
    if result is not None:
        return result

    # Phase 3 — powers of 5 on top: val = g^(2^A * 3^B * 5^c)
    val_after_23 = val
    val, result = _exponentiate_prime_phase(val_after_23, 5, max_power, n)
    if result is not None:
        return result

    # Phase 4 — base-60 orbit: val60 = g^(60^k)
    result = _base60_orbit(g, n, max_power * 3)
    if result is not None:
        return result

    # Phase 5 — irregular prime extension
    # Multiply the fully-cascaded value (and the 60-orbit value) by small
    # non-Babylonian primes to catch almost-smooth orders.
    for extra_prime in _IRREGULAR_PRIMES:
        val_extra = powmod(val, extra_prime, n)
        d = gcd(val_extra - 1, n)
        if 1 < d < n:
            return (d, n // d)

    return None


def _exponentiate_prime_phase(
    base_val: int, prime: int, max_exp: int, n: int
) -> tuple[int, tuple[int, int] | None]:
    """Repeatedly raise *base_val* to *prime*, checking GCD in batches.

    Returns (final_val, result) where *result* is a factor pair or None.
    """
    val = base_val
    product = 1

    for e in range(1, max_exp + 1):
        val = powmod(val, prime, n)
        product = (product * (val - 1)) % n

        if e % _BATCH_SIZE == 0:
            d = gcd(product, n)
            if 1 < d < n:
                return val, (d, n // d)
            if d == n:
                # Overshot somewhere in this batch — backtrack step-by-step
                result = _backtrack(base_val, prime, e - _BATCH_SIZE + 1, e, n)
                if result is not None:
                    return val, result
                # All trivial (every intermediate gcd was n) — continue
            product = 1
            base_val = val  # update for potential backtracking

    # Flush remaining product
    if product != 1:
        d = gcd(product, n)
        if 1 < d < n:
            return val, (d, n // d)
        if d == n:
            start = max_exp - (max_exp % _BATCH_SIZE) + 1
            result = _backtrack(base_val, prime, start, max_exp, n)
            if result is not None:
                return val, result

    return val, None


def _backtrack(
    base_val: int, prime: int, start_exp: int, end_exp: int, n: int
) -> tuple[int, int] | None:
    """Re-check individual exponents in [start_exp, end_exp] after an overshoot."""
    val = base_val
    for _ in range(start_exp, end_exp + 1):
        val = powmod(val, prime, n)
        d = gcd(val - 1, n)
        if 1 < d < n:
            return (d, n // d)
    return None


def _base60_orbit(g: int, n: int, steps: int) -> tuple[int, int] | None:
    """Compute g^(60^k) for k = 1 .. *steps*, checking GCD in batches."""
    val = g
    product = 1

    for k in range(1, steps + 1):
        val = powmod(val, 60, n)
        product = (product * (val - 1)) % n

        if k % _BATCH_SIZE == 0:
            d = gcd(product, n)
            if 1 < d < n:
                return (d, n // d)
            if d == n:
                # Backtrack through the batch individually
                v = g if k == _BATCH_SIZE else _recompute_val60(g, k - _BATCH_SIZE, n)
                for _ in range(k - _BATCH_SIZE + 1, k + 1):
                    v = powmod(v, 60, n)
                    d2 = gcd(v - 1, n)
                    if 1 < d2 < n:
                        return (d2, n // d2)
            product = 1

    # Flush
    if product != 1:
        d = gcd(product, n)
        if 1 < d < n:
            return (d, n // d)

    return None


def _recompute_val60(g: int, steps: int, n: int) -> int:
    """Recompute g^(60^steps) mod n from scratch (for backtracking)."""
    val = g
    for _ in range(steps):
        val = powmod(val, 60, n)
    return val


# ------------------------------------------------------------------
# Quick self-test
# ------------------------------------------------------------------
if __name__ == "__main__":
    # A semiprime where p-1 has large prime factors but ord_2(p) is 5-smooth.
    # p = 2^4 * 3^2 * 5 * q + 1 where q is a large prime — but ord_2(p) may
    # still be a 5-smooth divisor of p-1.
    test_cases = [
        (61 * 53, "small: 61 * 53 = 3233"),
        (1009 * 1013, "medium: 1009 * 1013 = 1022117"),
        (104729 * 104743, "larger: 104729 * 104743"),
        # p = 2^6 * 3^3 * 5^2 + 1 = 43201, which is prime;
        # ord_2(p) divides p-1 = 2^6 * 3^3 * 5^2 (entirely 5-smooth!)
        (43201 * 99991, "crafted: 43201 * 99991 (p-1 is 5-smooth)"),
    ]

    for n, desc in test_cases:
        result = factor(n)
        status = "OK" if result is not None else "FAIL"
        print(f"[{status}] {desc}: factor({n}) = {result}")
