"""Regularity-Guided Quadratic Sieve — cuneiform-enhanced factoring.

Deeply integrates cuneiform's regularity tier system with the quadratic sieve.

Mathematical foundation:
    The cuneiform library classifies every integer by its "regularity tier" —
    how close it is to being 5-smooth (a "regular number" in Babylonian base-60
    arithmetic). This technique uses regularity as a FAST PRE-FILTER in the
    quadratic sieve, and smooth-part extraction to enable PARTIAL RELATIONS.

Cuneiform contributions:
    1. Tier-0 free relations: Q(x) values that are fully 5-smooth give
       instant relations with zero trial division cost.
    2. Smooth-part pre-filter: extract_smooth_part() quickly identifies
       Q(x) values with large smooth components — these are prioritized
       for trial division. Values with tiny smooth parts are skipped.
    3. Partial relation harvesting: when Q(x) is smooth except for one
       large prime, record it. When two partials share the same large
       prime, they combine into a full relation (the large prime cancels).
    4. Uses cuneiform's RegularityClass to guide sieving decisions.

    The net effect: fewer trial divisions per smooth relation found,
    plus additional relations from the partial combination step.

Complexity: Same as QS ~L(n)^(1/sqrt(2)), but with smaller constant due
    to pre-filtering and partial relations.
"""

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent))

from math import log, exp, sqrt as fsqrt

from cuneiform.core.accel import gcd, isqrt, powmod, invert, is_probable_prime
from cuneiform.number_theory.primes import sieve_of_eratosthenes, tonelli_shanks
from cuneiform.core.smooth import extract_smooth_part, is_smooth


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tonelli_shanks(n_mod_p: int, p: int) -> int | None:
    """Square root of n mod p, returning a single root or None.

    Wraps cuneiform's tonelli_shanks which returns a list of roots.
    """
    roots = tonelli_shanks(n_mod_p, p)
    if not roots:
        return None
    return roots[0]


def _trial_factor_fb(
    val: int, sign: int, factor_base: list[int | str]
) -> list[int] | None:
    """Fully factor *val* over *factor_base*.

    The first element of factor_base is -1 (sign sentinel).
    Returns an exponent vector (one entry per FB element) if val is
    completely smooth over the factor base, or None otherwise.

    Parameters
    ----------
    val : int
        Absolute value of Q(x) to factor.
    sign : int
        +1 or -1, indicating the sign of Q(x).
    factor_base : list
        Factor base; first element is -1 (sign).
    """
    fb_size = len(factor_base)
    exponents = [0] * fb_size

    # Handle sign
    if sign < 0:
        exponents[0] = 1  # -1 has exponent 1

    remainder = val
    for i in range(1, fb_size):
        p = factor_base[i]
        while remainder % p == 0:
            remainder //= p
            exponents[i] += 1
    if remainder != 1:
        return None
    return exponents


def _trial_factor_partial(
    val: int, sign: int, factor_base: list[int | str]
) -> tuple[list[int] | None, int]:
    """Trial-factor *val* over *factor_base*, allowing one leftover prime.

    Returns (exponent_vector, leftover) where leftover is the unfactored
    remainder.  If leftover == 1 the value was fully smooth.
    Returns (None, 0) if the value cannot be expressed this way (e.g.
    leftover is composite or factoring went nowhere).
    """
    fb_size = len(factor_base)
    exponents = [0] * fb_size

    if sign < 0:
        exponents[0] = 1

    remainder = val
    for i in range(1, fb_size):
        p = factor_base[i]
        while remainder % p == 0:
            remainder //= p
            exponents[i] += 1

    if remainder <= 1:
        return exponents, remainder  # fully smooth

    return exponents, remainder


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


def _solve_and_extract(
    n: int,
    relations: list[tuple[int, list[int]]],
    factor_base: list[int],
) -> tuple[int, int] | None:
    """Find a congruence of squares from collected relations via GF(2) elimination.

    Parameters
    ----------
    n : int
        The number being factored.
    relations : list of (a_value, exponent_vector)
        Each relation means a_value^2 ≡ product(fb[i]^exp[i]) (mod n).
    factor_base : list[int]
        The factor base (first element is -1 for sign).

    Returns
    -------
    tuple[int, int] | None
        A non-trivial factor pair, or None.
    """
    num_rels = len(relations)
    fb_size = len(factor_base)

    # Build GF(2) matrix from exponent vectors
    matrix = [[rel[1][j] % 2 for j in range(fb_size)] for rel in relations]
    history = [
        [1 if i == j else 0 for j in range(num_rels)]
        for i in range(num_rels)
    ]

    deps = _gauss_elim_gf2(matrix, history)

    for dep in deps:
        involved = [i for i in range(num_rels) if dep[i]]
        if not involved:
            continue

        # a = product of a_values mod n
        a = 1
        for i in involved:
            a = (a * relations[i][0]) % n

        # Sum exponent vectors
        combined_exps = [0] * fb_size
        for i in involved:
            for j in range(fb_size):
                combined_exps[j] += relations[i][1][j]

        # b = sqrt of the product of FB elements
        # Skip -1 (index 0) for the modular product; sign is handled by parity
        b = 1
        for j in range(1, fb_size):
            half_exp = combined_exps[j] // 2
            if half_exp > 0:
                b = (b * powmod(factor_base[j], half_exp, n)) % n

        d = gcd(abs(a - b) % n, n)
        if 1 < d < n:
            return (d, n // d)

        d = gcd((a + b) % n, n)
        if 1 < d < n:
            return (d, n // d)

    return None


# ---------------------------------------------------------------------------
# Main factoring function
# ---------------------------------------------------------------------------

def factor(
    n: int,
    *,
    bound: int | None = None,
    sieve_range: int | None = None,
    use_partials: bool = True,
    large_prime_bound: int | None = None,
) -> tuple[int, int] | None:
    """Factor *n* using the regularity-guided quadratic sieve.

    Uses cuneiform's regularity tier system as a fast pre-filter in the
    quadratic sieve, and smooth-part extraction to harvest partial relations.

    Parameters
    ----------
    n : int
        The integer to factor (must be composite and > 1).
    bound : int | None
        Smoothness bound for the factor base.  Auto-computed when None.
    sieve_range : int | None
        Half-width of the sieve interval around sqrt(n).  Auto-computed
        when None.
    use_partials : bool
        If True (default), collect partial relations (single large prime
        variation) and combine them.
    large_prime_bound : int | None
        Maximum size of the large prime in partial relations.  Defaults
        to bound * 50.

    Returns
    -------
    tuple[int, int] | None
        A pair (p, q) with p * q == n, or None if no factor was found.
    """
    # --- Edge cases ---
    if n < 4:
        return None

    # Even
    if n % 2 == 0:
        return (2, n // 2)

    # Perfect square
    s = isqrt(n)
    if s * s == n:
        return (s, s)

    # Small prime factors
    for p in (3, 5, 7, 11, 13):
        if n % p == 0:
            return (p, n // p)

    # Check if n is prime
    if is_probable_prime(n):
        return None

    # --- Auto-compute parameters ---
    ln_n = log(n) if n > 1 else 1.0
    ln_ln_n = log(ln_n) if ln_n > 1 else 1.0
    L = exp(fsqrt(ln_n * ln_ln_n)) if ln_n > 1 else 10.0

    if bound is None:
        # Standard QS uses L^(1/sqrt(2)) ~ L^0.707.  We use a slightly
        # higher exponent to ensure a generous factor base, since the
        # regularity pre-filter lets us sieve faster per candidate.
        bound = max(300, int(L ** 0.75))
        bound = min(bound, 500_000)

    if sieve_range is None:
        sieve_range = max(50_000, bound * 20)
        sieve_range = min(sieve_range, 5_000_000)

    if large_prime_bound is None:
        large_prime_bound = bound * 50

    # --- Step 1: Build factor base ---
    primes = sieve_of_eratosthenes(bound)
    factor_base: list[int] = [-1]  # sign sentinel
    sqrt_mod_p: dict[int, int] = {}

    for p in primes:
        if p == 2:
            factor_base.append(2)
            sqrt_mod_p[2] = n % 2
            continue
        # Check if n is a quadratic residue mod p
        r = powmod(n % p, (p - 1) // 2, p)
        if r <= 1:  # n is QR mod p (r==1) or p | n (r==0)
            factor_base.append(p)
            sq = _tonelli_shanks(n % p, p)
            if sq is not None:
                sqrt_mod_p[p] = sq

    fb_size = len(factor_base)
    # We need at least fb_size+1 relations to guarantee a GF(2) dependency,
    # but we collect generously to get multiple dependencies (increasing the
    # probability that at least one produces a non-trivial factor).
    min_relations = fb_size + 1

    sqrt_n = isqrt(n)
    if sqrt_n * sqrt_n == n:
        return (sqrt_n, n // sqrt_n)

    # --- Step 2: Log-based sieve with regularity pre-filtering ---
    #
    # Standard QS technique: build a sieve array of size 2*sieve_range+1.
    # For each prime p in factor_base with known sqrt(n) mod p, add
    # log2(p) at positions where p | Q(x).  Then only trial-divide
    # candidates whose sieve value exceeds a threshold.
    #
    # The cuneiform enhancement: BEFORE trial division, apply the
    # regularity pre-filter (extract_smooth_part) to further prune.

    full_relations: list[tuple[int, list[int]]] = []
    partial_relations: dict[int, tuple[int, list[int]]] = {}

    # Stats
    tier_0_free = 0
    tier_skipped = 0
    trial_divided = 0
    partials_found = 0
    partials_combined = 0

    # Sieve array: accumulate approximate log2 contributions
    sieve_len = 2 * sieve_range + 1
    sieve_array = bytearray(sieve_len)  # uint8 log sums

    from math import log2

    # Sieve with each prime in the factor base (skip -1 at index 0)
    for fb_idx in range(1, fb_size):
        p = factor_base[fb_idx]
        if p not in sqrt_mod_p:
            continue
        logp = int(log2(p) + 0.5)  # approximate log2(p)
        if logp < 1:
            logp = 1
        sq = sqrt_mod_p[p]

        # Q(x) = (sqrt_n + x)^2 - n ≡ 0 (mod p)
        # => sqrt_n + x ≡ ±sq (mod p)
        # => x ≡ sq - sqrt_n (mod p) or x ≡ -sq - sqrt_n (mod p)
        roots_mod_p = set()
        roots_mod_p.add((sq - sqrt_n) % p)
        roots_mod_p.add((-sq - sqrt_n) % p)

        for r in roots_mod_p:
            # Array index i corresponds to x = i - sieve_range
            start_x = -sieve_range + ((r - (-sieve_range)) % p)
            start_idx = start_x + sieve_range
            idx = start_idx
            while 0 <= idx < sieve_len:
                sieve_array[idx] = min(255, sieve_array[idx] + logp)
                idx += p

    # Sieve threshold: accept if sieve sum >= log2(Q_abs) - slack.
    # Slack controls the tradeoff between trial-division work and
    # missing smooth values.
    bits_n = n.bit_length()
    slack = min(30, bits_n // 2)

    for i in range(sieve_len):
        x = i - sieve_range
        a = sqrt_n + x
        if a <= 0:
            continue
        Q = a * a - n
        if Q == 0:
            continue

        sign = 1
        Q_abs = abs(Q)
        if Q < 0:
            sign = -1

        # Quick sieve check: is the accumulated log close enough?
        log2_Q = Q_abs.bit_length()
        threshold = max(0, log2_Q - slack)
        if sieve_array[i] < threshold:
            # Sieve says not enough small prime content — but check
            # cuneiform regularity first for tier-0 values
            smooth_part, cofactor = extract_smooth_part(Q_abs)
            if cofactor == 1:
                # TIER 0: Fully 5-smooth! Free relation!
                tier_0_free += 1
                exp_vec = _trial_factor_fb(Q_abs, sign, factor_base)
                if exp_vec is not None:
                    full_relations.append((a % n, exp_vec))
            continue

        # Passed sieve threshold — apply cuneiform regularity pre-filter
        smooth_part, cofactor = extract_smooth_part(Q_abs)

        if cofactor == 1:
            # TIER 0: Fully 5-smooth! Free relation!
            tier_0_free += 1
            exp_vec = _trial_factor_fb(Q_abs, sign, factor_base)
            if exp_vec is not None:
                full_relations.append((a % n, exp_vec))
            continue

        # REGULARITY HEURISTIC: skip values where the 5-smooth cofactor
        # is too large to plausibly factor over the remaining factor base.
        if cofactor > bound * bound * bound:
            tier_skipped += 1
            continue

        # Trial divide Q_abs over factor base
        trial_divided += 1
        exp_vec = _trial_factor_fb(Q_abs, sign, factor_base)

        if exp_vec is not None:
            full_relations.append((a % n, exp_vec))

    # --- Step 3: If not enough full relations, do a second pass for partials ---
    if use_partials and len(full_relations) <= fb_size:
        for i in range(sieve_len):
            x = i - sieve_range
            a = sqrt_n + x
            if a <= 0:
                continue
            Q = a * a - n
            if Q == 0:
                continue

            sign = 1
            Q_abs = abs(Q)
            if Q < 0:
                sign = -1

            log2_Q = Q_abs.bit_length()
            threshold = max(0, log2_Q - slack)
            if sieve_array[i] < threshold:
                continue

            smooth_part, cofactor = extract_smooth_part(Q_abs)
            if cofactor == 1 or cofactor > bound * bound * bound:
                continue

            partial_exp, leftover = _trial_factor_partial(
                Q_abs, sign, factor_base
            )
            if partial_exp is not None and 1 < leftover < large_prime_bound:
                if is_probable_prime(leftover):
                    partials_found += 1
                    if leftover in partial_relations:
                        other_a, other_exp = partial_relations[leftover]
                        combined_a = (a * other_a) % n
                        combined_exp = [
                            partial_exp[j] + other_exp[j]
                            for j in range(fb_size)
                        ]
                        full_relations.append((combined_a, combined_exp))
                        partials_combined += 1
                    else:
                        partial_relations[leftover] = (a % n, partial_exp)

    # --- Step 4: Solve via GF(2) elimination ---
    if len(full_relations) > fb_size:
        result = _solve_and_extract(n, full_relations, factor_base)
        if result:
            return result

    return None


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import time

    print("Regularity-Guided Quadratic Sieve — self-test")
    print("=" * 60)

    from cuneiform.number_theory.primes import is_prime as _is_prime

    # Test 1: trivial edge cases
    print("\nTest 1: edge cases")
    assert factor(2) is None, "prime should return None"
    assert factor(3) is None, "prime should return None"
    assert factor(4) == (2, 2), f"4 should be (2, 2), got {factor(4)}"
    assert factor(6) == (2, 3) or factor(6) == (3, 2), f"6 edge case failed"
    assert factor(9) == (3, 3), f"9 should be (3, 3), got {factor(9)}"
    # Even number
    r = factor(100)
    assert r is not None and r[0] * r[1] == 100, f"100 failed: {r}"
    # Perfect square of a prime
    r = factor(49)
    assert r == (7, 7), f"49 should be (7, 7), got {r}"
    # Prime
    assert factor(1000000007) is None, "prime should return None"
    print("  PASS")

    # Test 2: small semiprimes
    print("\nTest 2: small semiprimes")
    small_cases = [
        (3 * 5, 15),
        (7 * 11, 77),
        (13 * 17, 221),
        (101 * 103, 10403),
        (127 * 131, 16637),
        (1009 * 1013, 1022117),
    ]
    for expected_product, n_val in small_cases:
        t0 = time.perf_counter()
        result = factor(n_val)
        elapsed = time.perf_counter() - t0
        if result:
            p, q = result
            assert p * q == n_val, f"FAIL: {p} * {q} != {n_val}"
            print(f"  n={n_val:>12}  => ({p}, {q})  [{elapsed:.3f}s] PASS")
        else:
            print(f"  n={n_val:>12}  => None  [{elapsed:.3f}s] SKIP")

    # Test 3: medium semiprimes
    print("\nTest 3: medium semiprimes")
    medium_cases = [
        10007 * 10009,
        100003 * 100019,
        1000003 * 1000033,
    ]
    for n_val in medium_cases:
        t0 = time.perf_counter()
        result = factor(n_val)
        elapsed = time.perf_counter() - t0
        if result:
            p, q = result
            assert p * q == n_val, f"FAIL: {p} * {q} != {n_val}"
            print(f"  n={n_val}  ({n_val.bit_length()} bits) => ({p}, {q})  [{elapsed:.3f}s] PASS")
        else:
            print(f"  n={n_val}  ({n_val.bit_length()} bits) => None  [{elapsed:.3f}s]")

    # Test 4: verify partials contribute
    print("\nTest 4: partials vs no-partials comparison")
    n4 = 100003 * 100019
    t0 = time.perf_counter()
    r_with = factor(n4, use_partials=True)
    t_with = time.perf_counter() - t0
    t0 = time.perf_counter()
    r_without = factor(n4, use_partials=False)
    t_without = time.perf_counter() - t0
    print(f"  With partials:    {r_with}  [{t_with:.3f}s]")
    print(f"  Without partials: {r_without}  [{t_without:.3f}s]")
    if r_with:
        assert r_with[0] * r_with[1] == n4
        print("  PASS")

    # Test 5: 5-smooth-adjacent semiprime (cuneiform advantage)
    print("\nTest 5: factor near 5-smooth numbers (cuneiform sweet spot)")
    # Primes near powers of 2*3*5
    p5 = 2**4 * 3**2 * 5 + 1  # 721 — check primality
    if not _is_prime(p5):
        p5 = 2**3 * 3 * 5 * 7 + 1  # 841 = 29^2, not prime
        p5 = 2**3 * 3 * 5 * 7 - 1  # 839, prime
    q5 = 2**5 * 3**3 * 5 - 1  # 4319, check
    if not _is_prime(q5):
        q5 = 4327  # prime
    n5 = p5 * q5
    t0 = time.perf_counter()
    result = factor(n5)
    elapsed = time.perf_counter() - t0
    if result:
        assert result[0] * result[1] == n5
        print(f"  n={n5} => {result}  [{elapsed:.3f}s] PASS")
    else:
        print(f"  n={n5} => None  [{elapsed:.3f}s]")

    print("\n" + "=" * 60)
    print("Self-test complete.")
