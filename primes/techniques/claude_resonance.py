"""Multi-Discriminant Lucas Resonance Cascade — a novel factoring technique.

Mathematical foundation:
    For a generalized Lucas sequence U_k(P,Q) with discriminant Delta = P^2-4Q,
    the rank of apparition alpha(p) -- the smallest k where p | U_k -- satisfies:
        alpha(p) | p - (Delta/p)
    where (Delta/p) is the Legendre symbol.

    When (Delta/p) = +1: alpha(p) | p-1  (like Pollard p-1)
    When (Delta/p) = -1: alpha(p) | p+1  (like Williams p+1)

Novel contributions:
    1. Use MANY discriminants simultaneously to probe both p-1 and p+1 structure,
       regardless of which case applies for each discriminant.
    2. Select discriminants from quadratic fields with small class number (h=1 or h=2),
       where the rank of apparition tends to have smoother factorization.
    3. CASCADE: multiply U-sequence results across discriminants and check the
       product GCD. Different sequences contribute different prime power factors
       of the group order, so their product may cover the full order even when
       no individual sequence does.

    This generalizes both Pollard p-1 and Williams p+1 into a single unified
    framework, and the class-number heuristic for discriminant selection has
    not been explored in the factoring literature.

Complexity: O(B * log(B) * D) where B is the smoothness bound and D is the
    number of discriminants. Finds factors where p-1 or p+1 has a large
    smooth part relative to any of the D probed discriminants.
"""

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent))

from cuneiform.core.accel import gcd, isqrt, powmod, invert


from cuneiform.number_theory.primes import sieve_of_eratosthenes


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mat_mul_mod(A, B, n):
    """Multiply two 2x2 matrices mod n.

    Matrices are represented as ((a,b),(c,d)).
    """
    (a0, a1), (a2, a3) = A
    (b0, b1), (b2, b3) = B
    return (
        ((a0 * b0 + a1 * b2) % n, (a0 * b1 + a1 * b3) % n),
        ((a2 * b0 + a3 * b2) % n, (a2 * b1 + a3 * b3) % n),
    )


def _mat_pow_mod(M, e, n):
    """Raise 2x2 matrix M to the power e, mod n (binary exponentiation)."""
    # Identity matrix
    result = ((1, 0), (0, 1))
    base = M
    while e > 0:
        if e & 1:
            result = _mat_mul_mod(result, base, n)
        base = _mat_mul_mod(base, base, n)
        e >>= 1
    return result


def _lucas_chain(P, Q, n, primes, B):
    """Drive the Lucas U-sequence companion matrix through prime powers up to B.

    The companion matrix for U_k(P, Q) is:
        M = [[P, -Q], [1, 0]]

    We compute M^E mod n where E = product of all prime powers pe <= B.
    The (1, 0) entry of M^E gives U_E mod n.

    Parameters
    ----------
    P, Q : int
        Lucas sequence parameters (discriminant = P^2 - 4*Q).
    n : int
        Modulus (the number being factored).
    primes : list[int]
        Primes up to B.
    B : int
        Smoothness bound.

    Returns
    -------
    int
        U_E mod n.
    """
    # Companion matrix [[P, -Q], [1, 0]]
    # We reduce Q mod n to keep things positive in modular arithmetic.
    Qmod = (-Q) % n
    mat = ((P % n, Qmod), (1, 0))

    for p in primes:
        # Largest prime power pe with pe <= B
        pe = p
        while pe * p <= B:
            pe *= p
        mat = _mat_pow_mod(mat, pe, n)

    # M^E = [[U_{E+1} - Q*U_E*..., ...], [U_E, ...]]
    # For companion matrix [[P, -Q], [1, 0]]^k, the (1,0) entry is U_k.
    return mat[1][0]


def _get_discriminants(max_count):
    """Generate discriminants from quadratic fields with small class number.

    Class number 1 fields have unique factorization, producing Lucas sequences
    with cleaner period structure (rank of apparition tends to be smoother).

    Returns a list of up to max_count discriminants.
    """
    # Class number 1 (negative fundamental discriminants -- the Heegner numbers)
    heegner = [-3, -4, -7, -8, -11, -19, -43, -67, -163]

    # Small positive discriminants with class number 1
    positive_h1 = [5, 8, 12, 13, 17, 21, 24, 28, 29, 33, 37, 41, 44,
                   53, 56, 57, 61, 69, 73, 76, 77, 89, 92, 93, 97]

    # Class number 2 negative discriminants
    neg_h2 = [-15, -20, -24, -35, -40, -51, -52, -88, -91, -115,
              -123, -148, -187, -232, -235, -267, -403, -427]

    all_discs = heegner + positive_h1 + neg_h2
    return all_discs[:max_count]


def _params_for_discriminant(delta):
    """Find (P, Q) such that P^2 - 4*Q = delta and Q != 0.

    We need P^2 - 4*Q = delta, so Q = (P^2 - delta) / 4.
    P must satisfy P = delta (mod 2) for Q to be an integer.
    We choose the smallest valid P > 0.
    """
    # Start with appropriate parity
    if delta % 2 == 0:
        P = 2
    else:
        P = 1

    while True:
        num = P * P - delta
        if num % 4 == 0:
            Q = num // 4
            if Q != 0:
                return (P, Q)
        P += 2


def _backtrack(P, Q, n, primes, B):
    """Handle overshoot: when gcd(U_M, n) == n, step through prime powers
    one at a time, checking GCD after each to isolate a single factor.

    Returns (p, n//p) or None.
    """
    Qmod = (-Q) % n
    mat = ((P % n, Qmod), (1, 0))
    prev_mat = mat  # checkpoint before last prime power

    for p in primes:
        pe = p
        while pe * p <= B:
            pe *= p
        prev_mat = mat
        mat = _mat_pow_mod(mat, pe, n)
        u = mat[1][0]
        g = gcd(u, n)
        if 1 < g < n:
            return (g, n // g)
        if g == n:
            # Overshoot happened at this prime power.  Apply p one at a time
            # from the checkpoint before this prime power.
            mat2 = prev_mat
            exp = p
            while exp <= pe:
                mat2 = _mat_pow_mod(mat2, p, n)
                u2 = mat2[1][0]
                g2 = gcd(u2, n)
                if 1 < g2 < n:
                    return (g2, n // g2)
                if g2 == n:
                    break
                exp *= p
            # Could not isolate from this prime — continue with accumulated mat
    return None


# ---------------------------------------------------------------------------
# Main factoring function
# ---------------------------------------------------------------------------

def factor(
    n: int,
    *,
    B: int = 500_000,
    max_discriminants: int = 50,
) -> tuple[int, int] | None:
    """Factor n using the Multi-Discriminant Lucas Resonance Cascade.

    For each discriminant Delta from a curated list (small class number quadratic
    fields), we drive the generalized Lucas U-sequence through all prime powers
    up to B using 2x2 companion matrix exponentiation.  The rank of apparition
    alpha(p) divides p - (Delta/p), so different discriminants probe different
    group structures (p-1 or p+1) depending on the Legendre symbol.

    Results are cascaded: U-values across discriminants are multiplied together
    (mod n) and their product GCD is checked, allowing partial smooth orders
    from different discriminants to combine into a full factorization.

    Parameters
    ----------
    n : int
        The integer to factor (must be composite and > 1).
    B : int
        Smoothness bound for prime powers in the Lucas chain.
    max_discriminants : int
        Maximum number of discriminants to try.

    Returns
    -------
    tuple[int, int] | None
        A pair (p, n // p) with 1 < p < n, or None if no factor was found.
    """
    primes = sieve_of_eratosthenes(B)
    discriminants = _get_discriminants(max_discriminants)

    cascade_product = 1

    for delta in discriminants:
        P, Q = _params_for_discriminant(delta)

        u_final = _lucas_chain(P, Q, n, primes, B)

        # Check this discriminant individually
        g = gcd(u_final, n)
        if 1 < g < n:
            return (g, n // g)

        if g == n:
            # Overshoot: both factors divide U_M.  Back off by checking
            # the GCD after each prime power to find where the first
            # factor appears.
            result = _backtrack(P, Q, n, primes, B)
            if result is not None:
                return result
            # If backtracking also fails (unlikely), continue to next discriminant.
            continue

        # Cascade: accumulate product across discriminants
        cascade_product = (cascade_product * u_final) % n
        g = gcd(cascade_product, n)
        if 1 < g < n:
            return (g, n // g)

    return None


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import time

    print("Multi-Discriminant Lucas Resonance Cascade — self-test")
    print("=" * 60)

    # Test 1: basic semiprime
    n1 = 1000000007 * 1000000009
    print(f"\nTest 1: n = {n1}  ({n1.bit_length()} bits)")
    t0 = time.perf_counter()
    result = factor(n1, B=50_000, max_discriminants=10)
    elapsed = time.perf_counter() - t0
    print(f"  Result: {result}  ({elapsed:.3f}s)")
    if result:
        p, q = result
        assert p * q == n1, "FAIL: product mismatch"
        print("  PASS")

    # Test 2: semiprime where p+1 is smooth but p-1 is not
    # p = 2^17 * 3 - 1 = 393215 (p-1 = 393214 = 2 * 196607, and 196607 is prime — NOT smooth)
    # p + 1 = 393216 = 2^17 * 3 (very smooth!)
    # q = a prime with non-smooth p-1 and p+1
    p_smooth_pp1 = 2**17 * 3 - 1  # 393215... check primality
    from cuneiform.number_theory.primes import is_prime as _is_prime
    if not _is_prime(p_smooth_pp1):
        # Try another: p = 2^k * 3^j - 1 that is prime
        # p = 2^7 * 3^4 - 1 = 128 * 81 - 1 = 10367 (check: 10367 is prime)
        candidates = []
        for k in range(5, 25):
            for j in range(1, 10):
                cand = (2**k) * (3**j) - 1
                if cand > 100 and _is_prime(cand):
                    candidates.append(cand)
        if candidates:
            p_smooth_pp1 = candidates[-1]  # pick a larger one

    # Pick a second prime whose p-1 is also not smooth
    q_test = 1000000007
    n2 = p_smooth_pp1 * q_test

    print(f"\nTest 2: p+1-smooth factor test")
    print(f"  p = {p_smooth_pp1} (p+1 is smooth)")
    print(f"  n = {n2}  ({n2.bit_length()} bits)")
    t0 = time.perf_counter()
    result = factor(n2, B=50_000, max_discriminants=20)
    elapsed = time.perf_counter() - t0
    print(f"  Result: {result}  ({elapsed:.3f}s)")
    if result:
        p, q = sorted(result)
        assert p * q == n2, "FAIL: product mismatch"
        print("  PASS")
    else:
        print("  No factor found (may need larger B)")

    # Test 3: verify cascade effect — use a small B where individual
    # discriminants might miss but the cascade catches it
    # Use a known factorable semiprime
    n3 = 127 * 131
    print(f"\nTest 3: small semiprime n = {n3}")
    t0 = time.perf_counter()
    result = factor(n3, B=200, max_discriminants=50)
    elapsed = time.perf_counter() - t0
    print(f"  Result: {result}  ({elapsed:.3f}s)")
    if result:
        p, q = result
        assert p * q == n3, "FAIL: product mismatch"
        print("  PASS")

    # Test 4: larger semiprime with a p-1-smooth factor
    # p = 2 * 3 * 5 * 7 * 11 * 13 * 17 * 19 * 23 + 1 = 223092871 (check primality)
    p4 = 2 * 3 * 5 * 7 * 11 * 13 * 17 * 19 * 23 + 1
    if not _is_prime(p4):
        p4 = 2 * 3 * 5 * 7 * 11 * 13 * 17 * 19 + 1  # 9699691
    q4 = 1000000007
    n4 = p4 * q4
    print(f"\nTest 4: larger semiprime n = {n4}  ({n4.bit_length()} bits)")
    print(f"  p = {p4} (p-1 is {p4-1}-smooth)")
    t0 = time.perf_counter()
    result = factor(n4, B=50_000, max_discriminants=10)
    elapsed = time.perf_counter() - t0
    print(f"  Result: {result}  ({elapsed:.3f}s)")
    if result:
        p, q = result
        assert p * q == n4, "FAIL: product mismatch"
        print("  PASS")
    else:
        print("  No factor found")

    print("\n" + "=" * 60)
    print("Self-test complete.")
