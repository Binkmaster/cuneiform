"""Cuneiform Polar Factoring -- Gaussian Pollard Rho with Plimpton-322.

Lifts Pollard's rho into the complex plane and samples starting points
from the Babylonian parametrization of Pythagorean triples.

Mathematical foundation:
    The Babylonians characterized directions not by angles but by RATIOS
    of sides -- the rows of Plimpton 322 give (a, b, c) with a^2 + b^2 = c^2,
    parametrized by 5-smooth generating pairs (p, q). These correspond to
    GAUSSIAN INTEGERS a + bi on the unit circle (scaled by c).

    The iteration z -> z^2 + c in Z[i]/(N) decomposes via CRT into
    independent dynamics mod p and mod q. Collisions between the two
    components (where z_hare = z_tortoise mod p but not mod q) reveal
    factors via gcd of the real part, imaginary part, or norm of the
    difference.

Cuneiform contributions:
    1. Starting points and constants from Plimpton-322 Gaussian integers,
       whose norms are perfect squares with 5-smooth structure.
    2. Two-dimensional walk in Z[i]/(N) gives richer collision detection:
       real-part, imaginary-part, and norm-based GCD checks.
    3. Batched product GCD across all three collision channels.
    4. Brent-style cycle detection lifted to Gaussian integers.

    The Babylonians' ratio-based "polar" system is reinterpreted as
    a structured sampling of the complex plane for factoring.

Complexity: O(sqrt(p)) expected (same as Pollard rho), but with potentially
    better constants from the 2D walk and structured starting points.
"""

import sys

sys.path.insert(
    0, str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent)
)

from cuneiform.core.accel import gcd, isqrt, is_probable_prime


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _plimpton_gaussians(count: int) -> list[tuple[int, int]]:
    """Generate Gaussian integers from Plimpton-322-style parametrization.

    For 5-smooth p > q > 0 with gcd(p, q) = 1 and p - q odd:
        z = (p^2 - q^2) + (2pq) * i
    These are the Pythagorean-triple Gaussian integers.
    Also includes simpler smooth Gaussian integers: a + bi for 5-smooth a, b.
    """
    # Build sorted list of 5-smooth numbers up to 200
    smooth: list[int] = []
    for e2 in range(15):
        v2 = 2**e2
        if v2 > 200:
            break
        for e3 in range(10):
            v23 = v2 * 3**e3
            if v23 > 200:
                break
            for e5 in range(7):
                v = v23 * 5**e5
                if v > 200:
                    break
                smooth.append(v)
    smooth.sort()

    results: list[tuple[int, int]] = []

    # Method 1: Plimpton-322 triples (p, q) -> (p^2 - q^2, 2pq)
    for p in smooth:
        for q in smooth:
            if q >= p:
                break
            if gcd(p, q) == 1 and (p - q) % 2 == 1:
                a = p * p - q * q
                b = 2 * p * q
                results.append((a, b))
                if len(results) >= count:
                    return results

    # Method 2: Simple smooth Gaussians (a + bi for small smooth a, b)
    for a in smooth[:20]:
        for b in smooth[:20]:
            if a != b:
                results.append((a, b))
                if len(results) >= count:
                    return results

    return results


def _gauss_sq_add(r: int, i: int, c_r: int, c_i: int, n: int) -> tuple[int, int]:
    """Compute z^2 + c in Z[i]/(N): (r + i*j)^2 + (c_r + c_i*j)."""
    new_r = (r * r - i * i + c_r) % n
    new_i = (2 * r * i + c_i) % n
    return new_r, new_i


# ---------------------------------------------------------------------------
# Main algorithm
# ---------------------------------------------------------------------------


def factor(
    n: int,
    *,
    num_orbits: int = 20,
    max_iterations: int = 2_000_000,
    batch_size: int = 500,
) -> tuple[int, int] | None:
    """Factor n using Gaussian Pollard rho with Plimpton-322 starting points.

    Parameters
    ----------
    n : int
        The integer to factor (must be composite and > 1).
    num_orbits : int
        Number of different (starting-point, constant) orbits to try.
    max_iterations : int
        Maximum iterations per orbit before moving to the next.
    batch_size : int
        How often to check the batched product GCD.

    Returns
    -------
    tuple[int, int] | None
        A pair (p, n // p) with 1 < p < n, or None if no factor was found.
    """
    # --- Edge cases ---
    if n < 2:
        return None
    if n % 2 == 0:
        return (2, n // 2)
    if is_probable_prime(n):
        return None
    # Small factors by trial division (handles cases where Gaussian
    # orbits collapse due to small modulus)
    for p in (3, 5, 7, 11, 13, 17, 19, 23, 29, 31):
        if n % p == 0 and n > p:
            return (p, n // p)
    # Perfect square check
    s = isqrt(n)
    if s * s == n:
        if is_probable_prime(s):
            return (s, s)
        # Fall through to main algorithm for composite roots

    # --- Generate Plimpton-322 Gaussian integers ---
    smooth_gaussians = _plimpton_gaussians(num_orbits * 2)

    # Pad with fallback values if we didn't get enough
    while len(smooth_gaussians) < num_orbits * 2:
        idx = len(smooth_gaussians)
        smooth_gaussians.append((3 + idx, 7 + idx * 2))

    for orbit_idx in range(num_orbits):
        # Starting point: a Plimpton-322 Gaussian integer
        z_real, z_imag = smooth_gaussians[orbit_idx * 2]
        # Constant: another Plimpton-322 Gaussian integer
        c_real, c_imag = smooth_gaussians[orbit_idx * 2 + 1]

        # Reduce mod n
        z_real %= n
        z_imag %= n
        c_real %= n
        c_imag %= n

        # Brent-style cycle detection in Gaussian integers
        # Hare advances 2 steps, tortoise advances 1 step
        hr, hi = z_real, z_imag
        tr, ti = z_real, z_imag

        product = 1  # batched GCD product

        # Save state for backtracking
        hr_save, hi_save = hr, hi
        tr_save, ti_save = tr, ti

        for iteration in range(1, max_iterations + 1):
            # Save state at start of each batch for backtracking
            if iteration % batch_size == 1:
                hr_save, hi_save = hr, hi
                tr_save, ti_save = tr, ti

            # Advance hare by TWO steps
            hr, hi = _gauss_sq_add(hr, hi, c_real, c_imag, n)
            hr, hi = _gauss_sq_add(hr, hi, c_real, c_imag, n)

            # Advance tortoise by ONE step
            tr, ti = _gauss_sq_add(tr, ti, c_real, c_imag, n)

            # Difference in Gaussian integers
            diff_r = (hr - tr) % n
            diff_i = (hi - ti) % n

            if diff_r == 0 and diff_i == 0:
                # Exact collision (hare == tortoise mod n) -- cycle detected
                # Check individual components against n before giving up
                break  # try next orbit

            # Norm of difference: |hare - tortoise|^2
            norm_diff = (diff_r * diff_r + diff_i * diff_i) % n

            if norm_diff == 0:
                # Norm is zero mod n but difference is nonzero --
                # This means diff_r^2 + diff_i^2 = 0 mod n, a structural collision
                g = gcd(diff_r, n)
                if 1 < g < n:
                    return (g, n // g)
                g = gcd(diff_i, n)
                if 1 < g < n:
                    return (g, n // g)
                break  # try next orbit

            # Accumulate into batched product:
            # - Real part difference (partial collision in real component)
            # - Imaginary part difference (partial collision in imag component)
            # - Norm of difference (full collision in norm)
            if diff_r != 0:
                product = (product * diff_r) % n
            if diff_i != 0:
                product = (product * diff_i) % n
            product = (product * norm_diff) % n

            if iteration % batch_size == 0:
                g = gcd(product, n)
                if g == n:
                    # Backtrack: replay this batch with individual GCDs
                    h2r, h2i = hr_save, hi_save
                    t2r, t2i = tr_save, ti_save
                    for _j in range(batch_size):
                        h2r, h2i = _gauss_sq_add(h2r, h2i, c_real, c_imag, n)
                        h2r, h2i = _gauss_sq_add(h2r, h2i, c_real, c_imag, n)
                        t2r, t2i = _gauss_sq_add(t2r, t2i, c_real, c_imag, n)

                        dr = (h2r - t2r) % n
                        di = (h2i - t2i) % n

                        if dr == 0 and di == 0:
                            break

                        # Check real part
                        if dr != 0:
                            g2 = gcd(dr, n)
                            if 1 < g2 < n:
                                return (g2, n // g2)
                        # Check imaginary part
                        if di != 0:
                            g2 = gcd(di, n)
                            if 1 < g2 < n:
                                return (g2, n // g2)
                        # Check norm
                        nd = (dr * dr + di * di) % n
                        if nd != 0:
                            g2 = gcd(nd, n)
                            if 1 < g2 < n:
                                return (g2, n // g2)

                    # Backtrack failed -- try next orbit
                    break
                if 1 < g < n:
                    return (g, n // g)
                product = 1

    return None


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_cases = [
        # Small semiprimes
        (15, "3 * 5"),
        (77, "7 * 11"),
        (221, "13 * 17"),
        (1147, "31 * 37"),
        # p = 1 mod 4 cases
        (5 * 13, "5 * 13 (both 1 mod 4)"),
        (29 * 41, "29 * 41 (both 1 mod 4)"),
        (89 * 97, "89 * 97 (both 1 mod 4)"),
        # p = 3 mod 4 cases
        (3 * 7, "3 * 7 (both 3 mod 4)"),
        (11 * 23, "11 * 23 (both 3 mod 4)"),
        (43 * 67, "43 * 67 (both 3 mod 4)"),
        (107 * 127, "107 * 127 (both 3 mod 4)"),
        # Mixed: one factor 1 mod 4, one factor 3 mod 4
        (5 * 7, "5 * 7 (mixed)"),
        (13 * 23, "13 * 23 (mixed)"),
        (29 * 43, "29 * 43 (mixed)"),
        # Larger semiprimes
        (1000003 * 1000033, "1000003 * 1000033 (~40-bit)"),
        (10000019 * 10000079, "10000019 * 10000079 (~47-bit)"),
        # Even larger
        (100000007 * 100000037, "100000007 * 100000037 (~54-bit)"),
        # Edge cases
        (4, "2 * 2 (perfect square)"),
        (9, "3 * 3 (perfect square of prime)"),
        (6, "2 * 3 (even)"),
    ]

    passed = 0
    failed = 0

    for n, desc in test_cases:
        result = factor(n)
        if result is None:
            print(f"  FAIL  {desc}: n={n}, got None")
            failed += 1
        else:
            p, q = result
            if p * q == n and 1 < p < n:
                print(f"  OK    {desc}: {p} * {q}")
                passed += 1
            else:
                print(f"  FAIL  {desc}: n={n}, got ({p}, {q})")
                failed += 1

    print(f"\n{passed}/{passed + failed} tests passed.")
    if failed:
        sys.exit(1)
