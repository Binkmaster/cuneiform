"""MPQS (Silverman, 1987). Major practical improvement over basic QS — uses
multiple polynomials to keep sieve values small, enabling larger sieve ranges.
Complexity same as QS asymptotically: L(n)^(1/sqrt(2)). The workhorse for
50-100 digit numbers before GNFS.

Algorithm
---------
Instead of a single polynomial Q(x) = (x + isqrt(n))^2 - n, MPQS generates
a sequence of polynomials g(x) = a*x^2 + 2*b*x + c whose values satisfy
(a*x + b)^2 = a * g(x) (mod n).  By choosing a = q^2 for suitable primes q,
the sieve values g(x) stay around n/a in magnitude — dramatically smaller
than basic QS — so smooth values are found much more frequently over the
same sieve interval [-M, M].

This implementation is self-contained pure Python: sieve, trial division,
and GF(2) linear algebra are all done in-process.
"""

import math
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent))

from cuneiform.core.accel import gcd, isqrt, powmod
from cuneiform.number_theory.primes import sieve_of_eratosthenes


# ---------------------------------------------------------------------------
# Helper: Tonelli-Shanks
# ---------------------------------------------------------------------------

def _tonelli_shanks(n: int, p: int) -> int | None:
    """Compute a square root of *n* mod *p* (odd prime).

    Returns an integer r with r^2 = n (mod p), or ``None`` if *n* is not
    a quadratic residue mod *p*.
    """
    if p == 2:
        return n % 2
    n %= p
    if n == 0:
        return 0
    # Euler criterion
    if powmod(n, (p - 1) // 2, p) != 1:
        return None

    # Find Q, S such that p - 1 = Q * 2^S with Q odd
    Q, S = p - 1, 0
    while Q % 2 == 0:
        Q //= 2
        S += 1

    if S == 1:
        # p ≡ 3 (mod 4)
        return powmod(n, (p + 1) // 4, p)

    # Find a quadratic non-residue z
    z = 2
    while powmod(z, (p - 1) // 2, p) != p - 1:
        z += 1

    M = S
    c = powmod(z, Q, p)
    t = powmod(n, Q, p)
    R = powmod(n, (Q + 1) // 2, p)

    while True:
        if t == 1:
            return R
        # Find the least i such that t^(2^i) ≡ 1 (mod p)
        i = 1
        tmp = (t * t) % p
        while tmp != 1:
            tmp = (tmp * tmp) % p
            i += 1
        b = powmod(c, 1 << (M - i - 1), p)
        M = i
        c = (b * b) % p
        t = (t * c) % p
        R = (R * b) % p


# ---------------------------------------------------------------------------
# Helper: modular inverse
# ---------------------------------------------------------------------------

def _modinv(a: int, m: int) -> int:
    """Return the modular inverse of *a* mod *m* via extended Euclidean."""
    g, x, _ = _extended_gcd(a % m, m)
    if g != 1:
        raise ValueError(f"No inverse: gcd({a}, {m}) = {g}")
    return x % m


def _extended_gcd(a: int, b: int) -> tuple[int, int, int]:
    """Extended Euclidean algorithm.  Returns (g, x, y) with a*x + b*y = g."""
    if a == 0:
        return b, 0, 1
    g, x1, y1 = _extended_gcd(b % a, a)
    return g, y1 - (b // a) * x1, x1


# ---------------------------------------------------------------------------
# Helper: GF(2) Gaussian elimination
# ---------------------------------------------------------------------------

def _gauss_elim_gf2(
    matrix: list[list[int]], history: list[list[int]]
) -> list[list[int]]:
    """Row-reduce *matrix* over GF(2), tracking row combinations in *history*.

    Returns history rows corresponding to zero rows in the reduced matrix
    (i.e. linear dependencies).
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
# Helper: compute sieve roots for a polynomial
# ---------------------------------------------------------------------------

def _compute_sieve_roots(
    a: int, b: int, c: int, factor_base: list[int],
    sqrt_table: dict[int, int], M: int,
) -> list[list[int]]:
    """Compute sieve starting positions for each factor-base prime.

    For prime p with sqrt(n) mod p = r, the sieve positions are:
        x ≡ (-b ± r) * a^(-1)  (mod p)

    When p divides a, g(x) is linear mod p and yields a single root:
        x ≡ -c * (2b)^(-1)  (mod p)

    Returns a list (one entry per factor-base prime) of lists of starting
    offsets within [0, 2*M].
    """
    roots = []
    for p in factor_base:
        if a % p == 0:
            # g(x) ≡ 2*b*x + c (mod p) — linear, single root
            twob = (2 * b) % p
            if twob == 0:
                roots.append([])
                continue
            inv_2b = _modinv(twob, p)
            x0 = (-(c % p) * inv_2b) % p
            start = (x0 + M) % p
            roots.append([start])
            continue

        r = sqrt_table.get(p)
        if r is None:
            roots.append([])
            continue

        ainv = _modinv(a, p)
        x1 = ((-b + r) * ainv) % p
        x2 = ((-b - r) * ainv) % p

        # Convert to sieve indices: sieve_idx = x + M, so start = (x0 + M) % p
        starts = [(x1 + M) % p, (x2 + M) % p]
        roots.append(starts)

    return roots


# ---------------------------------------------------------------------------
# Main: MPQS factor
# ---------------------------------------------------------------------------

def factor(
    n: int,
    *,
    bound: int | None = None,
    sieve_range: int | None = None,
    num_polynomials: int = 100,
) -> tuple[int, int] | None:
    """Factor *n* using the Multiple Polynomial Quadratic Sieve (MPQS).

    Parameters
    ----------
    n : int
        The integer to factor (must be composite and > 1).
    bound : int | None
        Smoothness bound B for the factor base.  When ``None``, B is chosen
        automatically from L(n).
    sieve_range : int | None
        Half-width M of the sieve interval [-M, M].  Default: ``bound * 10``.
    num_polynomials : int
        Maximum number of polynomials to generate (default: 100).

    Returns
    -------
    tuple[int, int] | None
        A pair (p, n // p) with 1 < p < n, or ``None`` if no factor found.
    """
    # --- trivial checks ---
    if n < 4:
        return None
    g = gcd(n, 6)
    if 1 < g < n:
        return (g, n // g)
    # Check perfect square
    s = isqrt(n)
    if s * s == n:
        return (s, s)

    # --- smoothness bound ---
    ln_n = math.log(n)
    ln_ln_n = math.log(ln_n) if ln_n > 1 else 1.0
    if bound is None:
        # L(n) = exp(sqrt(ln(n) * ln(ln(n))))
        # Use L^0.6 for a good balance between factor base size and smoothness
        L = math.exp(math.sqrt(ln_n * ln_ln_n))
        bound = max(50, int(L ** 0.6))

    if sieve_range is None:
        M = bound * 10
    else:
        M = sieve_range

    # --- build factor base ---
    all_primes = sieve_of_eratosthenes(bound)
    factor_base: list[int] = []
    sqrt_table: dict[int, int] = {}  # p -> sqrt(n) mod p

    for p in all_primes:
        if p == 2:
            factor_base.append(2)
            sqrt_table[2] = n % 2
            continue
        leg = powmod(n % p, (p - 1) // 2, p)
        if leg == 0 or leg == 1:
            # n is a QR mod p (or p | n)
            factor_base.append(p)
            if leg == 0:
                sqrt_table[p] = 0
            else:
                r = _tonelli_shanks(n, p)
                if r is not None:
                    sqrt_table[p] = r

    fb_len = len(factor_base)
    if fb_len == 0:
        return None
    # Collect extra relations beyond the minimum to improve chances
    # that the GF(2) null space yields a non-trivial congruence.
    needed = fb_len + max(10, fb_len // 3)

    # --- sieve threshold ---
    # After subtracting log contributions, values below this are candidates
    log2_threshold = max(10.0, math.log2(n) * 0.4)

    # --- relation collection ---
    # Each relation records (val, exponent_vector) where val^2 ≡ g(x) (mod n).
    # Since (a*x + b)^2 = a * g(x) (mod n) and a = q^2, we store
    # val = (a*x + b) * q^{-1} mod n so that val^2 ≡ g(x) (mod n).
    # exponent vector: index 0 is for -1 (sign), then one per factor base prime.
    relations: list[tuple[int, list[int]]] = []

    sqrt_2n = isqrt(2 * n)
    base_target_q = max(3, sqrt_2n // max(M, 1))
    used_qs: set[int] = set()

    for poly_idx in range(num_polynomials):
        if len(relations) >= needed:
            break

        # --- generate polynomial ---
        # Choose q prime with n a QR mod q, q ≈ sqrt(2n) / M
        # Vary target to get different polynomials each iteration
        target_q = base_target_q + poly_idx * 2
        q = _find_poly_prime(n, target_q)
        if q is None or q in used_qs:
            continue
        used_qs.add(q)

        a = q * q
        # Compute b via Hensel lifting: b^2 ≡ n (mod a)
        r_q = _tonelli_shanks(n, q)
        if r_q is None:
            continue
        b = _hensel_lift(n, q, r_q)
        if b is None:
            continue

        # c = (b^2 - n) / a — must be exact integer
        b2_minus_n = b * b - n
        if b2_minus_n % a != 0:
            continue
        c = b2_minus_n // a

        # q^{-1} mod n for converting (a*x+b) to the relation value
        q_inv = _modinv(q, n) if gcd(q, n) == 1 else None
        if q_inv is None:
            # q divides n — we found a factor!
            return (q, n // q)

        # --- sieve ---
        sieve_len = 2 * M + 1
        sieve = [0.0] * sieve_len

        # Initialize with log2(|g(x)|) estimates
        # g(x) = a*x^2 + 2*b*x + c
        for idx in range(sieve_len):
            x = idx - M
            gx = a * x * x + 2 * b * x + c
            if gx == 0:
                sieve[idx] = 0.0
            else:
                sieve[idx] = math.log2(abs(gx)) if abs(gx) > 0 else 0.0

        # Compute sieve roots and subtract log contributions
        roots = _compute_sieve_roots(a, b, c, factor_base, sqrt_table, M)

        for i, p in enumerate(factor_base):
            if not roots[i]:
                continue
            logp = math.log2(p)
            for start in roots[i]:
                if start < 0:
                    continue
                pos = start
                while pos < sieve_len:
                    sieve[pos] -= logp
                    pos += p

        # --- trial division on candidates ---
        for idx in range(sieve_len):
            if len(relations) >= needed:
                break
            if sieve[idx] > log2_threshold:
                continue

            x = idx - M
            gx = a * x * x + 2 * b * x + c
            if gx == 0:
                continue

            # Trial divide g(x) over factor base
            sign = 0
            val = gx
            if val < 0:
                val = -val
                sign = 1

            exponents = [sign]  # index 0 = sign (-1 exponent)
            remainder = val
            for p in factor_base:
                e = 0
                while remainder % p == 0:
                    remainder //= p
                    e += 1
                exponents.append(e)

            if remainder != 1:
                continue  # not smooth

            # Store val = (a*x + b) * q^{-1} mod n
            # so that val^2 ≡ g(x) (mod n)
            axb = (a * x + b) % n
            rel_val = (axb * q_inv) % n
            relations.append((rel_val, exponents))

    if len(relations) <= fb_len:
        return None

    # --- linear algebra: GF(2) ---
    num_rels = len(relations)
    # +1 column for sign
    num_cols = fb_len + 1
    matrix = [[e % 2 for e in rel[1]] for rel in relations]
    history = [[1 if i == j else 0 for j in range(num_rels)] for i in range(num_rels)]

    deps = _gauss_elim_gf2(matrix, history)

    # --- try each dependency ---
    for dep in deps:
        involved = [i for i in range(num_rels) if dep[i]]
        if not involved:
            continue

        # a_val = product of (a*x + b) values mod n
        a_val = 1
        for i in involved:
            a_val = (a_val * relations[i][0]) % n

        # Sum exponent vectors (skip sign at index 0)
        combined_exps = [0] * fb_len
        for i in involved:
            for j in range(fb_len):
                combined_exps[j] += relations[i][1][j + 1]

        # b_val = sqrt of product
        b_val = 1
        for j in range(fb_len):
            half_exp = combined_exps[j] // 2
            if half_exp > 0:
                b_val = (b_val * powmod(factor_base[j], half_exp, n)) % n

        # Check gcd(a_val - b_val, n) and gcd(a_val + b_val, n)
        d = gcd(abs(a_val - b_val) % n, n)
        if 1 < d < n:
            return (d, n // d)

        d = gcd((a_val + b_val) % n, n)
        if 1 < d < n:
            return (d, n // d)

    return None


# ---------------------------------------------------------------------------
# Internal: find a suitable prime for polynomial generation
# ---------------------------------------------------------------------------

def _find_poly_prime(n: int, target: int) -> int | None:
    """Find a prime q near *target* such that n is a quadratic residue mod q.

    Searches upward from target, returning the first suitable prime found.
    Gives up after 1000 candidates.
    """
    candidate = target | 1  # make odd
    if candidate < 3:
        candidate = 3
    for _ in range(1000):
        if _is_prime_small(candidate):
            leg = powmod(n % candidate, (candidate - 1) // 2, candidate)
            if leg == 1:
                return candidate
        candidate += 2
    return None


def _is_prime_small(n: int) -> bool:
    """Simple primality test for reasonably small numbers."""
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


# ---------------------------------------------------------------------------
# Internal: Hensel lifting
# ---------------------------------------------------------------------------

def _hensel_lift(n: int, q: int, r: int) -> int | None:
    """Lift square root r of n mod q to a square root mod q^2.

    Given r with r^2 ≡ n (mod q), compute b with b^2 ≡ n (mod q^2)
    using Hensel's lemma.
    """
    # r^2 ≡ n (mod q), so r^2 - n = k*q for some k
    # Lift: b = r + t*q where t chosen so b^2 ≡ n (mod q^2)
    # b^2 = r^2 + 2*r*t*q + t^2*q^2 ≡ r^2 + 2*r*t*q (mod q^2)
    # Need r^2 + 2*r*t*q ≡ n (mod q^2)
    # => 2*r*t*q ≡ n - r^2 (mod q^2)
    # => t ≡ (n - r^2) / q * (2*r)^{-1} (mod q)

    diff = n - r * r
    if diff % q != 0:
        return None
    k = diff // q  # k = (n - r^2) / q

    inv_2r = _modinv(2 * r, q)
    t = (k * inv_2r) % q
    b = r + t * q

    # Verify
    if (b * b - n) % (q * q) != 0:
        return None
    return b
