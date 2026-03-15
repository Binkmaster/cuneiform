"""Exact rational zeta values — CUNEIFORM's home turf.

The Riemann zeta function at positive even integers gives EXACT RATIONALS
(times powers of pi):

    zeta(2k) = (-1)^(k+1) * B_{2k} * (2*pi)^(2k) / (2 * (2k)!)

where B_{2k} are Bernoulli numbers — RATIONAL numbers.

This is the one place where CUNEIFORM's exact arithmetic genuinely
contributes: we can compute Bernoulli numbers and zeta-related rationals
with zero rounding error.

The Bernoulli numbers also appear in:
- The functional equation of zeta
- Values of zeta at negative integers: zeta(-n) = -B_{n+1}/(n+1)
- The Laurent expansion of zeta near s=1
"""

from __future__ import annotations

import sys
import os
from fractions import Fraction
from math import factorial

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from cuneiform.core.rational import SexaRational
from cuneiform.core.smooth import is_smooth, extract_smooth_part


def bernoulli_numbers(n: int) -> list[Fraction]:
    """Compute Bernoulli numbers B_0 through B_n using the Akiyama-Tanigawa algorithm.

    Returns exact Fractions — no floating point anywhere.
    """
    # Initialize with a_0(k) = 1/(k+1)
    a = [Fraction(1, k + 1) for k in range(n + 1)]

    result = [a[0]]  # B_0 = 1

    for m in range(1, n + 1):
        for k in range(n - m + 1):
            a[k] = (k + 1) * (a[k] - a[k + 1])
        result.append(a[0])

    return result


def zeta_even_rational_part(k: int, bernoullis: list[Fraction]) -> Fraction:
    """The rational part of zeta(2k).

    zeta(2k) = (-1)^(k+1) * B_{2k} * (2*pi)^(2k) / (2 * (2k)!)

    The rational factor (without the pi^(2k) part) is:
    R(2k) = (-1)^(k+1) * B_{2k} * 2^(2k) / (2 * (2k)!)
          = (-1)^(k+1) * B_{2k} * 2^(2k-1) / (2k)!

    So: zeta(2k) = R(2k) * pi^(2k)
    """
    if 2 * k >= len(bernoullis):
        raise ValueError(f"Need B_{2*k}, only computed up to B_{len(bernoullis)-1}")

    b2k = bernoullis[2 * k]
    sign = (-1) ** (k + 1)
    numer = sign * b2k * Fraction(2 ** (2 * k - 1))
    denom = Fraction(factorial(2 * k))
    return numer / denom


def zeta_negative_integers(n: int, bernoullis: list[Fraction]) -> Fraction:
    """zeta(-n) = -B_{n+1} / (n+1) for n >= 1.

    These are exact rationals (no pi involved).
    zeta(-1) = -1/12  (the famous "sum of natural numbers")
    zeta(-2) = 0  (trivial zero!)
    zeta(-3) = 1/120
    zeta(-4) = 0  (trivial zero!)
    ...
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    if n + 1 >= len(bernoullis):
        raise ValueError(f"Need B_{n+1}")
    return -bernoullis[n + 1] / Fraction(n + 1)


def analyze_bernoulli_regularity():
    """Analyze Bernoulli numbers through CUNEIFORM's regularity lens.

    Since Bernoulli numbers are rationals, we can ask: how "regular"
    are they in the sexagesimal sense? Do their denominators have
    nice 5-smooth structure?

    The Von Staudt-Clausen theorem tells us:
    B_{2k} + sum_{(p-1)|2k} 1/p is an integer

    So the denominator of B_{2k} = product of primes p where (p-1) | 2k.
    """
    print("=" * 78)
    print("BERNOULLI NUMBERS: EXACT RATIONAL ZETA VALUES")
    print("B_n computed with CUNEIFORM exact arithmetic (no floating point)")
    print("=" * 78)
    print()

    max_n = 30
    bernoullis = bernoulli_numbers(max_n)

    print("--- Bernoulli numbers (nonzero) ---")
    print(f"{'n':>4} {'B_n':>30} {'denom':>12} {'5-smooth?':>10}")
    print("-" * 60)

    for n in range(max_n + 1):
        b = bernoullis[n]
        if b == 0 and n > 1:
            continue  # Skip B_3 = B_5 = ... = 0
        denom = b.denominator
        smooth = is_smooth(denom) if denom > 0 else True
        b_str = str(b) if len(str(b)) <= 28 else f"{b.numerator}/{b.denominator}"
        print(f"{n:>4} {b_str:>30} {denom:>12} {'YES' if smooth else 'no':>10}")

    print()
    print("--- Von Staudt-Clausen: denominator structure ---")
    print("The denominator of B_{2k} = product of primes p where (p-1) | 2k")
    print()

    for k in range(1, 11):
        b = bernoullis[2 * k]
        denom = b.denominator
        smooth_part, cofactor = extract_smooth_part(denom)
        print(f"B_{2*k:>2}: denom = {denom:>8}  "
              f"smooth_part = {smooth_part:>6}  cofactor = {cofactor:>4}  "
              f"{'REGULAR' if cofactor == 1 else f'tier {cofactor}'}")

    print()


def zeta_values_table():
    """Table of exact zeta values using CUNEIFORM arithmetic."""
    print("=" * 78)
    print("EXACT ZETA VALUES (rational part)")
    print("zeta(2k) = R(2k) * pi^(2k)")
    print("=" * 78)
    print()

    bernoullis = bernoulli_numbers(24)

    print(f"{'s':>4} {'zeta(s)':>35} {'familiar form':>25}")
    print("-" * 68)

    familiar = {
        2: "pi^2 / 6",
        4: "pi^4 / 90",
        6: "pi^6 / 945",
        8: "pi^8 / 9450",
        10: "pi^10 / 93555",
        12: "691*pi^12 / 638512875",
    }

    for k in range(1, 13):
        s = 2 * k
        r = zeta_even_rational_part(k, bernoullis)
        fam = familiar.get(s, "")
        r_str = str(r) if len(str(r)) <= 33 else f".../{r.denominator}"
        print(f"{s:>4} {r_str:>35} * pi^{s:<4} {fam:>25}")

    print()
    print("--- Zeta at negative integers (exact rationals, no pi) ---")
    print()

    print(f"{'s':>4} {'zeta(s)':>20} {'note':>30}")
    print("-" * 58)

    for n in range(0, 13):
        z = zeta_negative_integers(n, bernoullis)
        note = ""
        if n == 1:
            note = "sum of naturals = -1/12"
        elif n % 2 == 0 and n > 0:
            note = "TRIVIAL ZERO"
        print(f"{-n:>4} {str(z):>20} {note:>30}")

    print()
    print("The trivial zeros at s = -2, -4, -6, ... are NOT what RH is about.")
    print("RH concerns the NONTRIVIAL zeros in the critical strip 0 < Re(s) < 1.")


def sexagesimal_zeta_display():
    """Show zeta values in sexagesimal notation where possible.

    The rational parts of zeta values can be displayed in base-60
    when their denominators are 5-smooth.
    """
    print()
    print("=" * 78)
    print("SEXAGESIMAL DISPLAY OF ZETA-RELATED RATIONALS")
    print("=" * 78)
    print()

    bernoullis = bernoulli_numbers(20)

    for k in range(1, 8):
        r = zeta_even_rational_part(k, bernoullis)
        denom = r.denominator
        try:
            sexa = SexaRational(r)
            print(f"zeta({2*k}) rational part: {r} = {sexa} (sexagesimal)")
        except Exception:
            smooth_part, cofactor = extract_smooth_part(denom)
            print(f"zeta({2*k}) rational part: {r} "
                  f"(denom cofactor = {cofactor}, not fully regular)")

    print()
    print("Values with 5-smooth denominators display cleanly in base 60.")
    print("Others would require CUNEIFORM's regularity extension to handle.")


if __name__ == "__main__":
    print()
    print("RIEMANN HYPOTHESIS: EXACT RATIONAL ZETA VALUES")
    print("Using CUNEIFORM sexagesimal exact arithmetic")
    print()

    analyze_bernoulli_regularity()
    print()
    zeta_values_table()
    print()
    sexagesimal_zeta_display()
