"""Smooth number connections to zeta — CUNEIFORM's unique angle.

The Euler product for zeta is:
    zeta(s) = prod_p (1 - p^(-s))^(-1)

CUNEIFORM's regularity decomposition separates primes into:
- "Regular" primes: {2, 3, 5}  (the base-60 primes)
- "Irregular" primes: {7, 11, 13, 17, ...}

This gives a natural factorization:
    zeta(s) = zeta_smooth(s) * zeta_irregular(s)

where:
    zeta_smooth(s) = (1-2^(-s))^(-1) * (1-3^(-s))^(-1) * (1-5^(-s))^(-1)
    zeta_irregular(s) = prod_{p>5} (1-p^(-s))^(-1)

The smooth part is completely understood. The irregular part carries
ALL the mystery, including the nontrivial zeros.

This module explores this decomposition and what it reveals about
the relationship between smooth numbers and the zeta function.
"""

from __future__ import annotations

import sys
import os
from math import log, pi as PI, sqrt, cos, sin
from fractions import Fraction

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from cuneiform.number_theory.primes import sieve_of_eratosthenes
from cuneiform.core.smooth import (
    is_smooth, extract_smooth_part, generate_smooth_numbers
)
from cuneiform.core.rational import SexaRational


def smooth_euler_factor(s: float) -> float:
    """The {2,3,5}-Euler product: zeta_smooth(s) = prod_{p in {2,3,5}} (1-p^(-s))^(-1).

    This is the "regular" part of zeta from CUNEIFORM's perspective.
    """
    result = 1.0
    for p in [2, 3, 5]:
        result *= 1.0 / (1.0 - p ** (-s))
    return result


def smooth_euler_factor_exact(s: int) -> Fraction:
    """Exact rational smooth Euler factor for positive integer s.

    zeta_smooth(s) = 1/((1-2^(-s))(1-3^(-s))(1-5^(-s)))
    """
    f2 = Fraction(1) - Fraction(1, 2 ** s)
    f3 = Fraction(1) - Fraction(1, 3 ** s)
    f5 = Fraction(1) - Fraction(1, 5 ** s)
    return Fraction(1) / (f2 * f3 * f5)


def irregular_euler_product(s: float, max_prime: int = 10000) -> float:
    """The "irregular" Euler product: primes > 5.

    zeta_irregular(s) = prod_{p>5, p prime} (1-p^(-s))^(-1)

    This factor carries ALL the nontrivial zeros of zeta.
    """
    primes = sieve_of_eratosthenes(max_prime)
    result = 1.0
    for p in primes:
        if p <= 5:
            continue
        result *= 1.0 / (1.0 - p ** (-s))
    return result


def smooth_dirichlet_series(s: float, limit: int = 10000) -> float:
    """Sum over 5-smooth numbers: sum_{n smooth} n^(-s).

    This equals zeta_smooth(s), but computed as a sum rather than a product.
    The agreement verifies the Euler product over {2,3,5}.
    """
    smooth_nums = generate_smooth_numbers(limit)
    return sum(n.value ** (-s) for n in smooth_nums)


def euler_product_decomposition():
    """Show the Euler product decomposition: zeta = smooth * irregular."""
    print("=" * 78)
    print("EULER PRODUCT DECOMPOSITION (CUNEIFORM)")
    print("zeta(s) = zeta_smooth(s) * zeta_irregular(s)")
    print("where zeta_smooth uses only primes {2, 3, 5}")
    print("=" * 78)
    print()

    print("--- Exact smooth Euler factors (rational, CUNEIFORM native) ---")
    print()
    for s in range(2, 13):
        exact = smooth_euler_factor_exact(s)
        try:
            sexa = SexaRational(exact)
            display = f" = {sexa} (sexa)"
        except Exception:
            display = ""
        print(f"zeta_smooth({s:>2}) = {str(exact):>20}{display}")

    print()
    print("--- Decomposition at real values ---")
    print()
    print(f"{'s':>6} {'zeta_smooth(s)':>16} {'zeta_irreg(s)':>16} "
          f"{'product':>16} {'zeta(s) known':>16}")
    print("-" * 72)

    known_zeta = {
        2: PI ** 2 / 6,
        3: 1.2020569031595942,  # Apery's constant
        4: PI ** 4 / 90,
        6: PI ** 6 / 945,
        8: PI ** 8 / 9450,
    }

    for s in [2, 3, 4, 6, 8]:
        smooth = smooth_euler_factor(s)
        irreg = irregular_euler_product(s, max_prime=50000)
        product = smooth * irreg
        known = known_zeta.get(s, 0)
        print(f"{s:>6} {smooth:>16.10f} {irreg:>16.10f} "
              f"{product:>16.10f} {known:>16.10f}")

    print()
    print("The smooth factor is completely determined by {2,3,5}.")
    print("ALL mystery (including the zeros) lives in zeta_irregular.")
    print()


def regularity_and_dirichlet():
    """Explore how CUNEIFORM regularity tiers relate to Dirichlet series.

    We can decompose the zeta Dirichlet series by regularity tier:
    sum_{n: tier 0} n^(-s) + sum_{n: tier 1} n^(-s) + ...

    Tier 0 = smooth numbers: their contribution equals zeta_smooth(s)
    Tier k = numbers with k irregular prime factors in their cofactor
    """
    print("=" * 78)
    print("DIRICHLET SERIES BY REGULARITY TIER")
    print("zeta(s) = sum_tier0 n^(-s) + sum_tier1 n^(-s) + ...")
    print("=" * 78)
    print()

    limit = 10000
    s_values = [2.0, 3.0, 4.0]

    # Classify numbers by regularity tier
    tier_sums = {}
    for s in s_values:
        tier_sums[s] = {}

    for n in range(1, limit + 1):
        smooth_part, cofactor = extract_smooth_part(n)
        # Count prime factors of cofactor = regularity tier
        tier = 0
        temp = cofactor
        d = 2
        while d * d <= temp:
            while temp % d == 0:
                tier += 1
                temp //= d
            d += 1
        if temp > 1:
            tier += 1

        for s in s_values:
            if tier not in tier_sums[s]:
                tier_sums[s][tier] = 0.0
            tier_sums[s][tier] += n ** (-s)

    for s in s_values:
        print(f"--- s = {s} ---")
        total = 0.0
        for tier in sorted(tier_sums[s].keys()):
            val = tier_sums[s][tier]
            total += val
            pct = 100 * val / total if total > 0 else 0
            count = sum(1 for n in range(1, limit + 1)
                        if _get_tier(n) == tier) if tier <= 3 else "..."
            print(f"  Tier {tier}: sum = {val:>12.8f}  "
                  f"(cumulative: {total:>12.8f})")
        print(f"  Total:     {total:>12.8f}")
        print(f"  Smooth factor alone: {smooth_euler_factor(s):>12.8f}")
        print()

    print("Tier 0 (smooth numbers) contributes the smooth Euler factor.")
    print("Higher tiers add the irregular primes' contributions.")
    print("The nontrivial zeros come from the interaction of ALL tiers.")


def _get_tier(n: int) -> int:
    """Get regularity tier of n."""
    _, cofactor = extract_smooth_part(n)
    tier = 0
    temp = cofactor
    d = 2
    while d * d <= temp:
        while temp % d == 0:
            tier += 1
            temp //= d
        d += 1
    if temp > 1:
        tier += 1
    return tier


def smooth_number_density_and_zeta():
    """Connection between smooth number density and zeta.

    The density of B-smooth numbers up to x is given by:
    Psi(x, B) ~ x * rho(u)  where u = log(x)/log(B)

    and rho is the Dickman function. This connects to the zeros of zeta
    because the Dickman function has a Mellin transform related to
    prod_{p<=B} (1 - p^(-s))^(-1), which is our smooth Euler factor.
    """
    print("=" * 78)
    print("SMOOTH NUMBER DENSITY AND ZETA")
    print("How many 5-smooth numbers exist up to x?")
    print("=" * 78)
    print()

    # Count 5-smooth numbers at various scales
    scales = [100, 1000, 10000, 100000]
    print(f"{'x':>10} {'smooth count':>14} {'density':>10} {'predicted':>10}")
    print("-" * 48)

    for x in scales:
        smooth = generate_smooth_numbers(x)
        count = len(smooth)
        density = count / x
        # Rough prediction: Psi(x, 5) ~ C * (log x)^3
        # (because 5-smooth = 3 generators, so #smooth < x is ~(log x)^3)
        log_x = log(x)
        predicted_count = (log_x ** 3) / 6  # rough leading term
        print(f"{x:>10} {count:>14} {density:>10.4f} {predicted_count:>10.1f}")

    print()
    print("5-smooth numbers become vanishingly rare as x grows.")
    print("This is why the {2,3,5} Euler factors alone cannot capture")
    print("the full behavior of zeta — the irregular primes dominate.")
    print()
    print("The Mellin transform connection:")
    print("  integral_0^inf rho_5(u) * x^(s-1) dx = zeta_smooth(s)")
    print("where rho_5 is the generalized Dickman function for base {2,3,5}.")


def partial_euler_products_and_zeros():
    """How partial Euler products approximate zeta near the critical line.

    Adding more primes to the Euler product changes the zero structure.
    With only {2,3,5}, there are no zeros.
    With all primes up to B, the "zeros" approximate the true zeros
    as B -> infinity.
    """
    print("=" * 78)
    print("PARTIAL EULER PRODUCTS NEAR THE CRITICAL LINE")
    print("How does adding primes change the 'zero structure'?")
    print("=" * 78)
    print()

    t_values = [14.13, 21.02, 25.01]  # near first three zeros
    prime_limits = [5, 20, 100, 1000, 10000]

    for t in t_values:
        print(f"--- At s = 1/2 + {t:.2f}i (near zero #{t_values.index(t)+1}) ---")
        s = complex(0.5, t)

        for plim in prime_limits:
            primes = sieve_of_eratosthenes(plim)
            product = complex(1.0, 0.0)
            for p in primes:
                term = 1.0 - p ** (-s)
                product *= term
            # zeta = 1/product (Euler product is for zeta^(-1))
            if abs(product) > 1e-15:
                zeta_approx = 1.0 / product
            else:
                zeta_approx = complex(float('inf'), 0)

            print(f"  primes <= {plim:>5}: "
                  f"|zeta| ~ {abs(zeta_approx):>10.4f}  "
                  f"arg ~ {_arg_degrees(zeta_approx):>8.1f} deg")

        print(f"  (True zero at gamma = {t:.2f}: |zeta| should -> 0)")
        print()

    print("As we include more primes, |zeta(1/2+it)| near true zeros")
    print("decreases toward 0. The zeros emerge from the collective")
    print("behavior of ALL primes — no finite subset can produce them.")


def _arg_degrees(z: complex) -> float:
    """Argument of complex number in degrees."""
    from math import atan2, degrees
    return degrees(atan2(z.imag, z.real))


if __name__ == "__main__":
    print()
    print("RIEMANN HYPOTHESIS: SMOOTH NUMBER CONNECTIONS TO ZETA")
    print("CUNEIFORM's unique angle on the Euler product")
    print()

    euler_product_decomposition()
    print()
    regularity_and_dirichlet()
    print()
    smooth_number_density_and_zeta()
    print()
    partial_euler_products_and_zeros()
