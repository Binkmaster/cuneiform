#!/usr/bin/env python3
"""Smooth Analysis — regularity classification demo.

Shows how CUNEIFORM classifies integers by their relationship
to 5-smooth numbers (the Babylonian "regular" numbers).
"""

from cuneiform.number_theory.regularity import RegularityClass
from cuneiform.core.smooth import is_smooth, generate_smooth_numbers


# The regular numbers — integers divisible only by 2, 3, and 5
print("=== 5-Smooth (Regular) Numbers up to 100 ===")
smooth_nums = list(generate_smooth_numbers(100))
print(f"Count: {len(smooth_nums)}")
print(f"Values: {[s.value for s in smooth_nums]}")

# Classify some numbers
print("\n=== Regularity Classification ===")
for n in [1, 7, 12, 30, 60, 61, 100, 360, 3600, 7919]:
    rc = RegularityClass(n)
    smooth_part = rc.smooth_part
    cofactor = rc.cofactor
    tier = rc.regularity_tier
    print(f"  {n:5d}: tier={tier}, smooth_part={smooth_part}, "
          f"cofactor={cofactor}, regular={rc.is_regular}")

# Why 60? It has ALL three smooth primes
print("\n=== Why Base 60? ===")
for base in [2, 10, 12, 16, 20, 60, 100, 360]:
    rc = RegularityClass(base)
    print(f"  Base {base:4d}: 2^{rc.exponents[0]} × 3^{rc.exponents[1]} "
          f"× 5^{rc.exponents[2]} × {rc.cofactor}")

# Density of smooth numbers
print("\n=== Smooth Number Density ===")
for limit in [100, 1000, 10000]:
    count = len(list(generate_smooth_numbers(limit)))
    density = count / limit * 100
    print(f"  Up to {limit:6d}: {count:4d} smooth numbers ({density:.1f}%)")
