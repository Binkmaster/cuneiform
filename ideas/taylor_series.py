#!/usr/bin/env python3
"""Taylor series in Babylonian sexagesimal cuneiform.

The Taylor coefficients of the classical functions are simple rationals:

    e^x      : 1/k!
    sin x    : ±1/(2k+1)!
    cos x    : ±1/(2k)!
    ln(1+x)  : ±1/k
    arctan x : ±1/(2k+1)
    1/(1-x)  : 1

A rational terminates in base 60 exactly when its (reduced) denominator is
5-smooth (only prime factors 2, 3, 5).  Since 7! introduces the prime 7,
the factorial k! is 5-smooth only for k <= 6 — so precisely the first seven
terms of the exponential series are *regular* numbers a Babylonian scribe
could have written exactly on a clay tablet.

This script renders coefficient tables and partial sums in sexagesimal
notation and cuneiform Unicode, using only exact rational arithmetic.
"""

import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cuneiform.core import Sexa
from cuneiform.core.sexagesimal import _digit_to_cuneiform
from cuneiform.core.smooth import is_smooth


# =============================================================================
# Rendering helpers (exact — truncation is explicit, never floating point)
# =============================================================================

def sexa_str(f: Fraction, frac_places: int = 8) -> str:
    """Sexagesimal digit string of a Fraction, truncated to frac_places."""
    s = Sexa._from_frac(f)
    int_digits, frac_digits, negative = s.digits(max_frac_digits=frac_places + 1)
    sign = "-" if negative else ""
    int_str = ",".join(str(d) for d in int_digits)
    terminates = is_smooth(f.denominator)
    shown = frac_digits if terminates else frac_digits[:frac_places]
    if not shown:
        return f"{sign}{int_str}"
    frac_str = ",".join(str(d) for d in shown)
    ellipsis = "" if terminates else ",..."
    return f"{sign}{int_str};{frac_str}{ellipsis}"


def cuneiform_str(f: Fraction, frac_places: int = 8) -> str:
    """Cuneiform rendering of a Fraction, truncated to frac_places."""
    s = Sexa._from_frac(f)
    int_digits, frac_digits, negative = s.digits(max_frac_digits=frac_places + 1)
    sign = "-" if negative else ""
    int_str = " ".join(_digit_to_cuneiform(d) for d in int_digits)
    terminates = is_smooth(f.denominator)
    shown = frac_digits if terminates else frac_digits[:frac_places]
    if not shown:
        return f"{sign}{int_str}"
    frac_str = " ".join(_digit_to_cuneiform(d) for d in shown)
    ellipsis = "" if terminates else " ..."
    return f"{sign}{int_str} ; {frac_str}{ellipsis}"


def regular_label(f: Fraction) -> str:
    return "REGULAR" if is_smooth(f.denominator) else "irregular"


# =============================================================================
# Taylor coefficient generators (exact Fractions)
# =============================================================================

def factorial(n: int) -> int:
    result = 1
    for k in range(2, n + 1):
        result *= k
    return result


def exp_coeffs(n: int) -> list[Fraction]:
    """1/k! for k = 0..n-1."""
    return [Fraction(1, factorial(k)) for k in range(n)]


def sin_coeffs(n: int) -> list[tuple[int, Fraction]]:
    """(power, coefficient) pairs: x - x^3/3! + x^5/5! - ..."""
    return [(2 * k + 1, Fraction((-1) ** k, factorial(2 * k + 1)))
            for k in range(n)]


def cos_coeffs(n: int) -> list[tuple[int, Fraction]]:
    """(power, coefficient) pairs: 1 - x^2/2! + x^4/4! - ..."""
    return [(2 * k, Fraction((-1) ** k, factorial(2 * k)))
            for k in range(n)]


def ln1p_coeffs(n: int) -> list[tuple[int, Fraction]]:
    """(power, coefficient) pairs: x - x^2/2 + x^3/3 - ..."""
    return [(k, Fraction((-1) ** (k + 1), k)) for k in range(1, n + 1)]


def arctan_coeffs(n: int) -> list[tuple[int, Fraction]]:
    """(power, coefficient) pairs: x - x^3/3 + x^5/5 - ..."""
    return [(2 * k + 1, Fraction((-1) ** k, 2 * k + 1)) for k in range(n)]


def basel_partial_sums(n: int) -> list[Fraction]:
    """Partial sums of the Basel series: sum 1/k^2 for k = 1..n."""
    sums = []
    total = Fraction(0)
    for k in range(1, n + 1):
        total += Fraction(1, k * k)
        sums.append(total)
    return sums


def pi_squared_over_six() -> Fraction:
    """High-precision rational approximation of pi^2/6 via Machin's formula."""
    from ideas.pi import machin_pi
    pi_frac = machin_pi(terms=80).as_fraction
    return pi_frac * pi_frac / 6


# =============================================================================
# Report sections
# =============================================================================

def print_exp_table(n: int = 10) -> None:
    print("=" * 78)
    print("e^x = sum x^k / k!   —   coefficients 1/k! in base 60")
    print("=" * 78)
    print(f"{'k':>2}  {'1/k!':>12}  {'sexagesimal':<28} {'status':<10} cuneiform")
    print("-" * 78)
    for k, c in enumerate(exp_coeffs(n)):
        print(f"{k:>2}  {str(c):>12}  {sexa_str(c):<28} "
              f"{regular_label(c):<10} {cuneiform_str(c)}")
    print()
    print("k! is 5-smooth only for k <= 6 (7! = 5040 introduces the prime 7),")
    print("so exactly the first SEVEN terms are regular — writable exactly on")
    print("a clay tablet.  From 1/7! on, every coefficient is irregular.")
    print()


def print_signed_table(title: str, series: str,
                       pairs: list[tuple[int, Fraction]]) -> None:
    print("=" * 78)
    print(f"{title}   —   {series}")
    print("=" * 78)
    print(f"{'x^p':>5}  {'coeff':>10}  {'sexagesimal':<28} {'status':<10} cuneiform")
    print("-" * 78)
    for power, c in pairs:
        print(f"x^{power:<3}  {str(c):>10}  {sexa_str(c):<28} "
              f"{regular_label(c):<10} {cuneiform_str(c)}")
    print()


def print_partial_sums_of_e(n: int = 10) -> None:
    print("=" * 78)
    print("Partial sums of e = sum 1/k!   —   watching convergence in base 60")
    print("=" * 78)
    print(f"{'terms':>5}  {'partial sum':>16}  {'sexagesimal':<32} cuneiform")
    print("-" * 78)
    total = Fraction(0)
    for k in range(n):
        total += Fraction(1, factorial(k))
        print(f"{k + 1:>5}  {str(total):>16}  {sexa_str(total, 6):<32} "
              f"{cuneiform_str(total, 6)}")
    print()
    print("e = 2;43,5,48,52,29,48,...  — the 7-term partial sum 2;43,5 is the")
    print("last one a scribe could write exactly; it already matches e in its")
    print("first two fractional digits (error < 1/60^2).")
    print()


def print_basel_table(n: int = 12) -> None:
    print("=" * 78)
    print("The Basel problem: sum 1/n^2 = pi^2/6   —   in base 60")
    print("=" * 78)
    print(f"{'n':>3}  {'1/n^2':>7}  {'partial sum':>14}  "
          f"{'sexagesimal':<26} {'sum status':<10} cuneiform")
    print("-" * 78)
    for k, total in enumerate(basel_partial_sums(n), start=1):
        term = Fraction(1, k * k)
        print(f"{k:>3}  {str(term):>7}  {str(total):>14}  "
              f"{sexa_str(total, 6):<26} {regular_label(total):<10} "
              f"{cuneiform_str(total, 4)}")
    print()
    target = pi_squared_over_six()
    print(f"  pi^2/6 = {sexa_str(target, 8)}")
    print(f"           {cuneiform_str(target, 8)}")
    print()
    print("The terms 1/n^2 are regular exactly when n is 5-smooth, but the")
    print("PARTIAL SUMS are regular only through n = 6: S_6 = 5369/3600 =")
    print("1;29,29 — exactly two sexagesimal digits.  Adding 1/49 at n = 7")
    print("plants the prime 7 in the denominator permanently.  Convergence is")
    print("slow (the tail is ~1/n): even S_12 has only reached 1;33,...,")
    print("far from pi^2/6 = 1;38,41,...  Euler needed a genuinely new idea —")
    print("no amount of tablet arithmetic gets there by direct summation.")
    print()


def print_taylor_polynomial_demo() -> None:
    """Evaluate the degree-6 Taylor polynomial of e^x via the CAS class."""
    from cuneiform.cas.ratcalculus import RationalTaylorSeries

    print("=" * 78)
    print("CAS demo: RationalTaylorSeries for e^x, all 7 regular terms")
    print("=" * 78)
    # Every derivative of e^x at 0 is exactly 1.
    series = RationalTaylorSeries([1] * 7, center=0)
    print(f"T_6(x) = {series.polynomial}")
    print()
    for num, den, label in [(1, 1, "x = 1"), (3, 2, "x = 1;30"),
                            (1, 2, "x = 0;30"), (1, 60, "x = 0;1")]:
        value = series.evaluate(Fraction(num, den))
        f = Fraction(value.numerator, value.denominator) \
            if hasattr(value, "numerator") else Fraction(value)
        print(f"  T_6({label}):  {sexa_str(f, 8):<30} {cuneiform_str(f, 8)}")
    print()


def main() -> None:
    print()
    print("TAYLOR SERIES IN BABYLONIAN SEXAGESIMAL CUNEIFORM")
    print("All arithmetic exact (Fraction / Sexa).  Truncation always marked.")
    print()
    print_exp_table(10)
    print_signed_table("sin x", "x - x^3/3! + x^5/5! - ...", sin_coeffs(5))
    print_signed_table("cos x", "1 - x^2/2! + x^4/4! - ...", cos_coeffs(5))
    print_signed_table("ln(1+x)", "x - x^2/2 + x^3/3 - ...", ln1p_coeffs(10))
    print_signed_table("arctan x", "x - x^3/3 + x^5/5 - ...", arctan_coeffs(8))
    print_partial_sums_of_e(10)
    print_basel_table(12)
    print_taylor_polynomial_demo()


if __name__ == "__main__":
    main()
