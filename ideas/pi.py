"""Compute pi in sexagesimal using exact rational arithmetic.

Pi is irrational, so no finite sexagesimal expansion is exact.
But we can compute rational approximations to arbitrary precision
using fast-converging series — all natively in Sexa (Fraction-backed).

Methods implemented:
  1. Machin's formula:  pi/4 = 4*arctan(1/5) - arctan(1/239)
  2. Euler's series:    pi/4 = 1 - 1/3 + 1/5 - 1/7 + ...  (slow, for comparison)
  3. Chudnovsky:        ~14 decimal digits per term (fastest known)
  4. Babylonian historical value: 3;7,30 = 25/8 = 3.125

The Machin and Chudnovsky methods converge fast enough to produce
dozens of correct sexagesimal digits in well under a second.
"""

import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cuneiform.core import Sexa


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _arctan_rational(x: Fraction, terms: int) -> Fraction:
    """Compute arctan(x) via Taylor series with exact rational arithmetic.

    arctan(x) = x - x^3/3 + x^5/5 - x^7/7 + ...

    For |x| <= 1/5, convergence is rapid: each term shrinks by x^2 ~ 1/25.
    """
    total = Fraction(0)
    power = x          # x^(2k+1)
    x_sq = x * x
    for k in range(terms):
        sign = 1 if k % 2 == 0 else -1
        total += sign * power / (2 * k + 1)
        power *= x_sq
    return total


# ---------------------------------------------------------------------------
# Method 1: Machin's formula  —  pi/4 = 4*arctan(1/5) - arctan(1/239)
# ---------------------------------------------------------------------------

def machin_pi(terms: int = 80) -> Sexa:
    """Compute pi via Machin's formula with exact rational arithmetic.

    Each arctan(1/5) term shrinks by 1/25, so 80 terms gives ~112 decimal
    digits (~65 sexagesimal digits) of precision.
    """
    a = _arctan_rational(Fraction(1, 5), terms)
    b = _arctan_rational(Fraction(1, 239), terms)
    pi_approx = 4 * (4 * a - b)
    return Sexa._from_frac(pi_approx)


# ---------------------------------------------------------------------------
# Method 2: Euler (Leibniz) series  —  pi/4 = 1 - 1/3 + 1/5 - ...
# ---------------------------------------------------------------------------

def euler_pi(terms: int = 1000) -> Sexa:
    """Compute pi via the Euler/Leibniz series (slow — for comparison)."""
    total = Fraction(0)
    for k in range(terms):
        sign = 1 if k % 2 == 0 else -1
        total += Fraction(sign, 2 * k + 1)
    return Sexa._from_frac(4 * total)


# ---------------------------------------------------------------------------
# Method 3: Chudnovsky algorithm  —  ~14 digits per term
# ---------------------------------------------------------------------------

def chudnovsky_pi(terms: int = 10) -> Sexa:
    """Compute pi via the Chudnovsky series with exact rational arithmetic.

    1/pi = 12 * sum_{k=0}^{N} (-1)^k (6k)! (13591409 + 545140134k)
                                  / ((3k)! (k!)^3 640320^(3k+3/2))

    Rearranged for exact Fraction arithmetic (no sqrt — we handle
    the sqrt(640320) factor separately via a rational approximation
    of sqrt(10005) to high precision using Newton's method).
    """
    # sqrt(640320) = 8*sqrt(10005), so 640320^(3/2) = 640320 * 8 * sqrt(10005)
    sqrt_10005 = _isqrt_rational(10005, iterations=20)

    total = Fraction(0)
    # Iterative computation avoids huge factorial calls:
    #   M_k = (6k)! / ((3k)! * (k!)^3),  L_k = 13591409 + 545140134*k
    #   X_k = (-262537412640768000)^k
    M = Fraction(1)
    L = Fraction(13591409)
    X = Fraction(1)
    for k in range(terms):
        total += M * L / X
        # Update for next term
        M *= Fraction((6*k + 1) * (6*k + 2) * (6*k + 3) * (6*k + 4) * (6*k + 5) * (6*k + 6),
                       (3*k + 1) * (3*k + 2) * (3*k + 3) * (k + 1)**3)
        L += 545140134
        X *= -262537412640768000

    inv_pi = total * Fraction(12) / (Fraction(640320) * 8 * sqrt_10005)
    pi_approx = Fraction(1) / inv_pi
    return Sexa._from_frac(pi_approx)


def _isqrt_rational(n: int, iterations: int = 20) -> Fraction:
    """Compute sqrt(n) as a Fraction using Newton's method.

    Each iteration doubles the number of correct digits.
    20 iterations starting from int(sqrt(n)) gives enormous precision.
    """
    import math
    x = Fraction(math.isqrt(n))
    n_frac = Fraction(n)
    for _ in range(iterations):
        x = (x + n_frac / x) / 2
    return x


# ---------------------------------------------------------------------------
# Method 4: Babylonian historical value
# ---------------------------------------------------------------------------

def babylonian_pi() -> Sexa:
    """The Old Babylonian approximation: 3;7,30 = 25/8 = 3.125.

    Found on several tablets (e.g., YBC 7302). The Babylonians likely
    derived this from measuring circumference/diameter of circles,
    arriving at the regular-number approximation 25/8.
    """
    return Sexa.from_notation("3;7,30")


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def _error_digits(approx: Sexa, reference: Sexa, places: int = 80) -> int:
    """Count matching sexagesimal fractional digits."""
    _, ref_digits, _ = reference.digits(max_frac_digits=places)
    _, approx_digits, _ = approx.digits(max_frac_digits=places)
    matching = 0
    for a, b in zip(approx_digits, ref_digits):
        if a == b:
            matching += 1
        else:
            break
    return matching


def _sexa_str(s: Sexa, frac_places: int = 40) -> str:
    """Format a Sexa with a specified number of fractional digits."""
    int_digits, frac_digits, negative = s.digits(max_frac_digits=frac_places)
    sign = "-" if negative else ""
    int_str = ",".join(str(d) for d in int_digits)
    if frac_digits:
        frac_str = ",".join(str(d) for d in frac_digits)
        return f"{sign}{int_str};{frac_str}"
    return f"{sign}{int_str}"


if __name__ == "__main__":
    print("=" * 72)
    print("  Pi in Sexagesimal — Exact Rational Arithmetic via cuneiform.Sexa")
    print("=" * 72)

    # Reference value (Machin with extra terms for validation)
    ref = machin_pi(120)

    print("\n[1] Machin's formula (80 terms):")
    pi_machin = machin_pi(80)
    m = _error_digits(pi_machin, ref)
    print(f"    {_sexa_str(pi_machin, frac_places=m)}")
    print(f"    ({m} correct sexagesimal places)")
    print(f"    {pi_machin.cuneiform()}")

    print("\n[2] Chudnovsky algorithm (10 terms):")
    pi_chud = chudnovsky_pi(10)
    m = _error_digits(pi_chud, ref)
    print(f"    {_sexa_str(pi_chud, frac_places=m)}")
    print(f"    ({m} correct sexagesimal places)")

    print("\n[3] Euler/Leibniz series (1000 terms — slow convergence):")
    pi_euler = euler_pi(1000)
    m = _error_digits(pi_euler, ref)
    print(f"    {_sexa_str(pi_euler)}")
    print(f"    (only {m} correct sexagesimal digit(s))")

    print("\n[4] Babylonian historical value (tablet YBC 7302):")
    pi_bab = babylonian_pi()
    print(f"    {pi_bab}  =  {float(pi_bab)}")
    print(f"    {pi_bab.cuneiform()}")
    m = _error_digits(pi_bab, ref)
    print(f"    ({m} correct sexagesimal digit(s))")

    print("\n" + "-" * 72)
    print("  Pi is irrational — no finite sexagesimal expansion is exact.")
    print("  Best computed digits (Chudnovsky-10):")
    print(f"  {_sexa_str(pi_chud, frac_places=79)}")
    print("-" * 72)

    # Convergence demo
    print("\n  Machin convergence:")
    for n in [5, 10, 20, 40, 80]:
        p = machin_pi(n)
        m = _error_digits(p, ref)
        print(f"    {n:3d} terms → {m:2d} correct sexagesimal digits")
