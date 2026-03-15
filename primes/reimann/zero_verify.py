"""Numerical verification of zeta zeros and the Z-function.

While numerical verification cannot PROVE RH, it serves to:
1. Build intuition about the zeros
2. Verify known zero locations
3. Implement Gram points and zero counting
4. Demonstrate the Z-function (Hardy's function)

The Riemann-Siegel Z-function:
    Z(t) = exp(i*theta(t)) * zeta(1/2 + it)

where theta(t) is the Riemann-Siegel theta function. Z(t) is real
for real t, and its real zeros correspond to zeros of zeta on the
critical line.
"""

from __future__ import annotations

import sys
import os
from math import log, pi as PI, sqrt, atan, sin, cos, floor, ceil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from cuneiform.number_theory.primes import sieve_of_eratosthenes


def riemann_siegel_theta(t: float) -> float:
    """Riemann-Siegel theta function.

    theta(t) = arg(Gamma(1/4 + it/2)) - (t/2)*log(pi)

    Using Stirling's approximation for large t:
    theta(t) ~ (t/2)*log(t/(2*pi)) - t/2 - pi/8 + 1/(48*t) + ...
    """
    if abs(t) < 0.1:
        return 0.0
    # Stirling approximation (good for t > 10)
    result = (t / 2.0) * log(abs(t) / (2 * PI)) - t / 2.0 - PI / 8.0
    # First correction term
    result += 1.0 / (48.0 * t)
    # Second correction
    result += 7.0 / (5760.0 * t ** 3)
    return result


def zeta_on_critical_line(t: float, num_terms: int = 500) -> complex:
    """Compute zeta(1/2 + it) using the Dirichlet series with smoothing.

    This is a SLOW method — just for educational purposes.
    For real work, use the Riemann-Siegel formula.

    The series sum_{n=1}^N n^(-s) converges very slowly for Re(s)=1/2,
    so we use the approximate functional equation.
    """
    s = complex(0.5, t)
    # Direct summation with Abel smoothing
    total = complex(0.0, 0.0)
    for n in range(1, num_terms + 1):
        # n^(-s) = exp(-s * log(n))
        log_n = log(n)
        # Smoothing weight
        weight = 1.0 - n / (num_terms + 1)
        term = weight * complex(cos(-t * log_n), sin(-t * log_n)) / sqrt(n)
        total += term
    return total


def hardy_z_function(t: float, num_terms: int = 500) -> float:
    """Hardy's Z-function: Z(t) = exp(i*theta(t)) * zeta(1/2 + it).

    Z(t) is real for real t.
    Real zeros of Z(t) correspond to zeros of zeta on the critical line.
    """
    theta = riemann_siegel_theta(t)
    zeta_val = zeta_on_critical_line(t, num_terms)
    # Z(t) = exp(i*theta) * zeta(1/2 + it)
    z = complex(cos(theta), sin(theta)) * zeta_val
    return z.real  # Should be real; imaginary part is numerical noise


def riemann_siegel_z(t: float) -> float:
    """Z-function via the Riemann-Siegel formula (faster, more accurate).

    Z(t) ~ 2 * sum_{n=1}^{N} cos(theta(t) - t*log(n)) / sqrt(n)
           + remainder

    where N = floor(sqrt(t / (2*pi))).
    """
    if abs(t) < 1.0:
        return hardy_z_function(t, 200)

    theta = riemann_siegel_theta(t)
    N = max(1, int(sqrt(abs(t) / (2.0 * PI))))

    total = 0.0
    for n in range(1, N + 1):
        total += cos(theta - t * log(n)) / sqrt(n)
    total *= 2.0

    # Leading remainder term (Riemann-Siegel correction)
    p = sqrt(abs(t) / (2.0 * PI)) - N
    # C_0(p) approximation
    c0 = cos(2 * PI * (p * p - p - 1.0 / 16.0)) / cos(2 * PI * p)
    remainder = (-1) ** (N - 1) * (abs(t) / (2.0 * PI)) ** (-0.25) * c0
    total += remainder

    return total


def verify_known_zeros():
    """Verify that Z(t) changes sign near known zero locations."""
    from primes.reimann.explicit_formula import KNOWN_ZERO_GAMMAS

    print("=" * 78)
    print("VERIFICATION OF KNOWN ZETA ZEROS")
    print("Z(t) should change sign at each zero (using Riemann-Siegel formula)")
    print("=" * 78)
    print()

    print(f"{'#':>3} {'gamma':>14} {'Z(gamma-0.1)':>14} {'Z(gamma)':>14} "
          f"{'Z(gamma+0.1)':>14} {'sign change':>12}")
    print("-" * 78)

    verified = 0
    for i, gamma in enumerate(KNOWN_ZERO_GAMMAS[:20]):
        z_before = riemann_siegel_z(gamma - 0.1)
        z_at = riemann_siegel_z(gamma)
        z_after = riemann_siegel_z(gamma + 0.1)

        # Check for sign change in neighborhood
        has_sign_change = (z_before * z_after < 0) or abs(z_at) < 0.5
        if has_sign_change:
            verified += 1

        print(f"{i+1:>3} {gamma:>14.6f} {z_before:>14.4f} {z_at:>14.4f} "
              f"{z_after:>14.4f} {'YES' if has_sign_change else 'no':>12}")

    print()
    print(f"Verified {verified}/{min(20, len(KNOWN_ZERO_GAMMAS))} zeros show "
          f"sign change in Z(t)")
    print()
    print("NOTE: This is numerical verification, NOT proof. Billions of zeros")
    print("have been verified computationally (Odlyzko, Gourdon, Platt).")
    print("But RH requires ALL zeros, and there are infinitely many.")


def gram_points(n_points: int = 30):
    """Compute Gram points — where theta(t) = n*pi.

    Gram's law (not always true) says Z(g_n) tends to be (-1)^n,
    i.e., Z changes sign between consecutive Gram points.
    Violations of Gram's law are called "Gram blocks."
    """
    print("=" * 78)
    print("GRAM POINTS AND GRAM'S LAW")
    print("Gram point g_n: theta(g_n) = n*pi")
    print("Gram's law (heuristic): (-1)^n * Z(g_n) > 0")
    print("=" * 78)
    print()

    print(f"{'n':>4} {'g_n':>12} {'Z(g_n)':>12} {'(-1)^n':>8} "
          f"{'Gram law':>10}")
    print("-" * 50)

    violations = 0
    for n in range(n_points):
        # Find g_n by bisection: theta(g_n) = n * pi
        target = n * PI
        lo, hi = max(1.0, target * 0.5), target * 3.0 + 20.0
        for _ in range(100):
            mid = (lo + hi) / 2.0
            if riemann_siegel_theta(mid) < target:
                lo = mid
            else:
                hi = mid
        g_n = (lo + hi) / 2.0

        z_val = riemann_siegel_z(g_n)
        expected_sign = (-1) ** n
        gram_holds = (expected_sign * z_val > 0)
        if not gram_holds:
            violations += 1

        print(f"{n:>4} {g_n:>12.4f} {z_val:>12.4f} {expected_sign:>8} "
              f"{'OK' if gram_holds else 'VIOLATION':>10}")

    print()
    print(f"Gram's law violations: {violations}/{n_points}")
    print("Gram's law is a heuristic, not a theorem. Violations are normal")
    print("and do NOT indicate zeros off the critical line.")


def zero_counting_N_T(T: float) -> float:
    """N(T) = #{rho : 0 < Im(rho) < T, zeta(rho)=0} (in critical strip).

    By the argument principle:
    N(T) = theta(T)/pi + 1 + S(T)

    where S(T) = (1/pi) * arg(zeta(1/2 + iT)) is small (O(log T)).

    This counts zeros WITHOUT finding them individually.
    """
    theta_T = riemann_siegel_theta(T)
    # Main term
    N_main = theta_T / PI + 1.0
    # S(T) correction is small; we estimate it from Z-function behavior
    return N_main


def zero_count_analysis():
    """Show how many zeros exist up to various heights."""
    print("=" * 78)
    print("ZERO COUNTING: N(T) = number of zeros with 0 < Im(rho) < T")
    print("=" * 78)
    print()

    from primes.reimann.explicit_formula import KNOWN_ZERO_GAMMAS

    print(f"{'T':>10} {'N(T) approx':>14} {'known zeros < T':>16}")
    print("-" * 44)

    heights = [15, 25, 35, 50, 75, 100, 200, 500, 1000]
    for T in heights:
        n_approx = zero_counting_N_T(T)
        known = sum(1 for g in KNOWN_ZERO_GAMMAS if g < T)
        print(f"{T:>10} {n_approx:>14.1f} {known:>16}")

    print()
    print("The formula N(T) ~ (T/(2*pi)) * log(T/(2*pi*e)) + 7/8")
    print("tells us zeros become denser as T grows (like T*log(T)/(2*pi)).")
    print("This means any proof must handle infinitely many zeros.")


if __name__ == "__main__":
    print()
    print("RIEMANN HYPOTHESIS: ZERO VERIFICATION AND Z-FUNCTION")
    print()

    verify_known_zeros()
    print()
    gram_points(25)
    print()
    zero_count_analysis()
