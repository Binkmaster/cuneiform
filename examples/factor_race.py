#!/usr/bin/env python3
"""Factor Race — standard vs sexagesimal Quadratic Sieve.

Demonstrates the core Phase 3 experiment: does sexagesimal
organization of the factor base improve smooth relation finding?
"""

from cuneiform.number_theory.sieve import StandardQuadraticSieve, SexagesimalQuadraticSieve


# A 15-digit semiprime
n = 1000000007 * 1000000009
print(f"=== Factoring {n} ===")
print(f"  ({n.bit_length()} bits)")

# Standard QS
print("\n--- Standard Quadratic Sieve ---")
std_qs = StandardQuadraticSieve(n)
std_factor = std_qs.factor()
if std_factor:
    print(f"  Factor found: {std_factor}")
    print(f"  {n} = {std_factor} × {n // std_factor}")
else:
    print("  No factor found with default parameters")

# Sexagesimal QS
print("\n--- Sexagesimal Quadratic Sieve ---")
sexa_qs = SexagesimalQuadraticSieve(n)
sexa_factor = sexa_qs.factor()
if sexa_factor:
    print(f"  Factor found: {sexa_factor}")
    print(f"  {n} = {sexa_factor} × {n // sexa_factor}")
else:
    print("  No factor found with default parameters")

# Smaller example with more detail
small_n = 15347
print(f"\n=== Detailed Factoring of {small_n} ===")
std = StandardQuadraticSieve(small_n)
sexa = SexagesimalQuadraticSieve(small_n)

print(f"\nStandard factor base ({len(std.factor_base)} primes):")
print(f"  {std.factor_base[:15]}...")

print(f"\nSexagesimal tiered factor base ({len(sexa.factor_base)} primes):")
print(f"  {sexa.factor_base[:15]}...")

std_result = std.factor()
sexa_result = sexa.factor()

print(f"\nStandard result: {std_result}")
print(f"Sexagesimal result: {sexa_result}")
if std_result:
    print(f"  {small_n} = {std_result} × {small_n // std_result}")
