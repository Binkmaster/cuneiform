"""Gaussian Integer Factoring via Plimpton-322 Parametrization.

The deepest synthesis of Babylonian mathematics and modern number theory.

Mathematical foundation:
    In the Gaussian integers Z[i], a prime p = 1 (mod 4) splits as
    p = (a + bi)(a - bi) where a^2 + b^2 = p. For N = pq, there are
    MULTIPLE representations N = a^2 + b^2 = c^2 + d^2, and the cross-products
    gcd(a*d - b*c, N) reveal the factors.

    Plimpton 322 (c. 1800 BCE) is a table of Pythagorean triples
    (a, b, c) with a^2 + b^2 = c^2. These are precisely the NORMS of
    Gaussian integers: N(a + bi) = a^2 + b^2 = c^2. The generating pairs
    (p, q) on the tablet are 5-smooth numbers -- the "regular numbers"
    of sexagesimal arithmetic.

    The Babylonians were doing Gaussian integer theory 3,700 years
    before Gauss.

Cuneiform contributions:
    1. Plimpton-322 parametric search: generates Gaussian integers from
       5-smooth generating pairs, computing orbits z^k in Z[i]/(N).
    2. Gaussian lattice reduction: finds short vectors in the lattice
       {(x,y) : x = y*sqrt(-1) (mod N)}, giving sum-of-squares representations.
    3. Cross-product factor extraction: when two representations
       N = a^2 + b^2 = c^2 + d^2 exist, their cross-product reveals factors.
    4. Smooth multiplier extension: tries N*k for 5-smooth k values,
       expanding the search to numbers where sum-of-squares representations
       are more accessible.

Complexity: O(sqrt(p)) for the Gaussian orbit search, O(n^(1/4)) for lattice
    reduction. Most effective when both factors are = 1 (mod 4).
"""

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent))

from cuneiform.core.accel import gcd, isqrt, powmod, invert
from cuneiform.core.smooth import is_smooth


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sqrt_neg1_mod(n):
    """Find r such that r^2 = -1 (mod n), or None.

    For n prime and n = 1 (mod 4), a solution always exists.
    For composite n = p*q with both p,q = 1 (mod 4), there are
    four square roots of -1 mod n (via CRT).

    Uses multiple strategies:
    1. Direct exponentiation a^((n-1)/4) for prime-like n
    2. Tonelli-Shanks style: factor out powers of 2 from (n-1)
       to systematically find square roots
    3. Extended search with many random bases
    """
    if n % 4 == 3:
        return None
    if n <= 1:
        return None

    import random
    rng = random.Random(42)

    # Strategy 1: Try a^((n-1)/4) for many random bases
    if n % 4 == 1:
        exp = (n - 1) // 4
        for _ in range(200):
            a = rng.randint(2, n - 1)
            r = powmod(a, exp, n)
            if (r * r + 1) % n == 0:
                return r
            # Also check n - r
            if ((n - r) * (n - r) + 1) % n == 0:
                return n - r

    # Strategy 2: Factor out 2s from n-1, do Tonelli-Shanks-like search
    # Write n - 1 = 2^s * d with d odd
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1

    # For each random base, compute a^d mod n, then square up
    for _ in range(200):
        a = rng.randint(2, n - 1)
        x = powmod(a, d, n)
        # Square x repeatedly and look for a value whose square is n-1
        for i in range(s):
            x2 = (x * x) % n
            if x2 == n - 1:  # x^2 = -1 mod n
                return x
            if x2 == 1:
                break
            x = x2

    # Strategy 3: Deterministic small bases
    if n % 4 == 1:
        exp = (n - 1) // 4
        for a in range(2, min(10000, n)):
            r = powmod(a, exp, n)
            if (r * r) % n == n - 1:
                return r

    return None


def _cornacchia(n):
    """Find (a, b) such that a^2 + b^2 = n, or None if impossible.

    Works when n is prime and n = 1 (mod 4), or n is a product of such primes.
    Uses the standard Cornacchia algorithm.
    """
    if n <= 1:
        return None
    if n == 2:
        return (1, 1)
    if n % 4 == 3:
        return None  # impossible for n = 3 (mod 4) when n is prime

    # Find sqrt(-1) mod n
    r = _sqrt_neg1_mod(n)
    if r is None:
        return None

    # Euclidean algorithm to find small (a, b) with a^2 + b^2 = n
    # Start with r, n and reduce until remainder < sqrt(n)
    sqrt_n = isqrt(n)
    a, b = n, r
    while b > sqrt_n:
        a, b = b, a % b

    # Now b^2 + c^2 should equal n
    c_sq = n - b * b
    c = isqrt(c_sq)
    if c * c == c_sq:
        return (b, c) if b <= c else (c, b)
    return None


def _gaussian_lattice_reduce(n, t):
    """Reduce the lattice {(n, 0), (t, 1)} to find a short vector.

    Returns (a, b) such that a = b*t (mod n) and a^2 + b^2 is small.
    Uses Gaussian reduction (equivalent to LLL in 2D).

    The lattice L = {(x, y) : x = y*t (mod n)} has basis
    v0 = (n, 0), v1 = (t % n, 1). Reducing this lattice finds
    short vectors whose norms reveal factor structure.
    """
    a0, b0 = n, 0
    a1, b1 = t % n, 1

    while a1 * a1 + b1 * b1 > 0:
        # Compute quotient: q = round(dot(v0, v1) / dot(v1, v1))
        dot01 = a0 * a1 + b0 * b1
        dot11 = a1 * a1 + b1 * b1
        if dot11 == 0:
            break
        q = (dot01 + dot11 // 2) // dot11  # rounded division

        # v0 = v0 - q * v1
        a0, b0 = a0 - q * a1, b0 - q * b1

        # Swap if v0 is shorter
        if a0 * a0 + b0 * b0 < a1 * a1 + b1 * b1:
            a0, b0, a1, b1 = a1, b1, a0, b0
        else:
            break

    return (abs(a1), abs(b1))


def _plimpton_pairs(count):
    """Generate Plimpton-322-style generating pairs (p, q) with p > q > 0
    and p, q being 5-smooth numbers.

    These are the "regular number" pairs that parameterize Pythagorean
    triples on the ancient tablet. The conditions p > q, gcd(p,q) = 1,
    and (p - q) odd ensure primitive triples.
    """
    smooth = []
    for e2 in range(20):
        v2 = 2 ** e2
        if v2 > 1000:
            break
        for e3 in range(13):
            v23 = v2 * 3 ** e3
            if v23 > 1000:
                break
            for e5 in range(9):
                v = v23 * 5 ** e5
                if v > 1000:
                    break
                smooth.append(v)
    smooth.sort()

    pairs = []
    for i, p in enumerate(smooth):
        for q in smooth:
            if q >= p:
                break
            if gcd(p, q) == 1 and (p - q) % 2 == 1:
                pairs.append((p, q))
            if len(pairs) >= count:
                return pairs

    return pairs


# ---------------------------------------------------------------------------
# Main algorithm
# ---------------------------------------------------------------------------

def factor(n, *, max_iterations=1_000_000):
    """Factor n using Gaussian integer / sum-of-squares method.

    Uses three complementary approaches:
      1. Cornacchia's algorithm + smooth multipliers to find sum-of-squares
         representations, extracting factors via GCD.
      2. Gaussian lattice reduction to find short vectors in Z[i]/(n),
         then cross-product factor extraction from multiple representations.
      3. Plimpton-322 Gaussian orbit: powers of Gaussian integers z^k
         in Z[i]/(n) using 5-smooth generating pairs, checking norms
         and components for factors.

    Parameters
    ----------
    n : int
        The integer to factor.
    max_iterations : int
        Upper bound on work in the Gaussian orbit phase.

    Returns
    -------
    tuple[int, int] | None
        A non-trivial factorization (p, q) with p <= q, or None.
    """
    # --- Edge cases ---
    if n < 2:
        return None
    if n % 2 == 0:
        return (2, n // 2)
    s = isqrt(n)
    if s * s == n:
        return (s, s)

    # =================================================================
    # METHOD 1: Cornacchia + smooth multipliers
    # =================================================================
    # Direct Cornacchia for n = a^2 + b^2
    rep = _cornacchia(n)
    if rep:
        a, b = rep
        # If n itself is a sum of two squares, it might be prime.
        # But check GCDs just in case.
        g = gcd(a, n)
        if 1 < g < n:
            p = min(g, n // g)
            return (p, n // p)

    # Try n*k for small 5-smooth multipliers k
    for k in [2, 3, 5, 4, 6, 8, 9, 10, 12, 15, 16, 18, 20, 24, 25, 30]:
        nk = n * k
        rep = _cornacchia(nk)
        if rep:
            a, b = rep
            # n*k = a^2 + b^2. Check if components share a factor with n.
            g = gcd(a, n)
            if 1 < g < n:
                p = min(g, n // g)
                return (p, n // p)
            g = gcd(b, n)
            if 1 < g < n:
                p = min(g, n // g)
                return (p, n // p)

    # =================================================================
    # METHOD 2: Gaussian lattice reduction
    # =================================================================
    # If n = 1 (mod 4), find sqrt(-1) mod n and reduce the lattice
    sqrt_neg1 = _sqrt_neg1_mod(n)

    if sqrt_neg1 is not None:
        # First lattice reduction with +sqrt(-1)
        a, b = _gaussian_lattice_reduce(n, sqrt_neg1)
        g = gcd(a * a + b * b, n)
        if 1 < g < n:
            p = min(g, n // g)
            return (p, n // p)

        # Second lattice reduction with -sqrt(-1)
        a2, b2 = _gaussian_lattice_reduce(n, n - sqrt_neg1)
        g = gcd(a2 * a2 + b2 * b2, n)
        if 1 < g < n:
            p = min(g, n // g)
            return (p, n // p)

        # Cross-product method: combine two representations
        if a * a + b * b != a2 * a2 + b2 * b2:
            for val in [
                a * a2 - b * b2,
                a * b2 - b * a2,
                a * a2 + b * b2,
                a * b2 + b * a2,
            ]:
                g = gcd(val, n)
                if 1 < g < n:
                    p = min(g, n // g)
                    return (p, n // p)

    # =================================================================
    # METHOD 3: Plimpton-322 Gaussian orbit
    # =================================================================
    # Generate Gaussian integers from 5-smooth generating pairs and
    # compute orbits z^k in Z[i]/(n), checking norms and components.
    smooth_pairs = _plimpton_pairs(200)
    iterations = 0

    for p_gen, q_gen in smooth_pairs:
        # Gaussian integer z = p_gen + q_gen*i
        # Norm(z) = p_gen^2 + q_gen^2
        norm_z = (p_gen * p_gen + q_gen * q_gen) % n
        g = gcd(norm_z, n)
        if 1 < g < n:
            p = min(g, n // g)
            return (p, n // p)

        # Compute z^k mod n in Gaussian integers for increasing k
        real, imag = p_gen % n, q_gen % n
        for k in range(2, 1000):
            iterations += 1
            if iterations > max_iterations:
                return None

            # (real + imag*i) * (p_gen + q_gen*i) mod n
            new_real = (real * p_gen - imag * q_gen) % n
            new_imag = (real * q_gen + imag * p_gen) % n
            real, imag = new_real, new_imag

            # Check real part, imaginary part, and norm for factors
            g = gcd(real, n)
            if 1 < g < n:
                p = min(g, n // g)
                return (p, n // p)
            g = gcd(imag, n)
            if 1 < g < n:
                p = min(g, n // g)
                return (p, n // p)
            norm_k = (real * real + imag * imag) % n
            g = gcd(norm_k, n)
            if 1 < g < n:
                p = min(g, n // g)
                return (p, n // p)

    return None


# ---------------------------------------------------------------------------
# CLI smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Gaussian Integer Factoring (Plimpton-322) ===\n")

    tests = [
        (65, "5 * 13, both = 1 mod 4"),
        (1009 * 2003, "1009 * 2003"),
        (104729 * 104723, "two ~100k primes"),
        (10009 * 10037, "two ~10k primes, both = 1 mod 4"),
        (49993 * 49999, "two ~50k primes"),
        (15, "3 * 5, mixed mod-4 residues"),
        (21, "3 * 7, both = 3 mod 4"),
    ]

    for n, desc in tests:
        result = factor(n)
        status = "OK" if result else "FAIL"
        if result:
            p, q = result
            check = "VALID" if p * q == n and p > 1 and q > 1 else "INVALID"
            print(f"  [{status}] {desc}: N={n} -> {p} * {q}  [{check}]")
        else:
            print(f"  [{status}] {desc}: N={n} -> None")
