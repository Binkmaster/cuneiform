#!/usr/bin/env python3
"""
Sexagesimal Random Number Generator — Design Notes & Examples
=============================================================

Concept
-------
Babylonian scribes had no formal theory of randomness, but they used
astragali (knuckle bones) for divination and games of chance. This module
imagines: *what if they had built a deterministic pseudo-random generator
using only the arithmetic available on clay tablets?*

The answer is a **Linear Congruential Generator (LCG)** whose parameters
are all native to base-60 arithmetic:

    X_{n+1} = (a * X_n + c) mod m

Where:
    m = 60^4 = 12,960,000   — "Plato's nuptial number", a power of 60
    a = 59*60 + 1 = 3,541   — chosen so (a-1) is divisible by 2, 3, 5
    c = 1                   — coprime to m (trivially)

These parameters satisfy the Hull-Dobell theorem, guaranteeing a full
period of 12,960,000 unique values before the sequence repeats.

Why 60^4?
---------
- 12,960,000 is mentioned by Plato in the Republic (the "nuptial number")
  and is deeply connected to sexagesimal arithmetic
- It's large enough for practical randomness (~23 bits of state)
- Every intermediate value has a terminating sexagesimal expansion
- It fits in 4 sexagesimal digits of integer state

Three Generator Modes
---------------------
1. **SexaRandom** — Core LCG producing random Sexa values in [0,1) or
   random integers. The workhorse generator.

2. **SmoothRandom** — Generates random 5-smooth (regular) numbers by
   picking random exponents for 2, 3, 5. Every output has a terminating
   reciprocal — perfect for generating "tablet-friendly" problems.

3. **CuneiformDice** — Simulates ancient randomness devices:
   - Astragali (knuckle bones): 4 faces with values 1, 3, 4, 6
   - d6: standard six-sided die (attested in Mesopotamia ~3000 BCE)
   - d60: a full sexagesimal digit die (1-59)

Future Ideas
------------
- Mersenne-Twister-style generator using 5-smooth Mersenne numbers
- Cryptographic-strength RNG based on sexagesimal discrete log
- Monte Carlo integration in sexagesimal (pi estimation on a tablet)
- Random Plimpton-322-style triple generation
- Procedural cuneiform tablet generation (random but valid tablets)

Examples
--------
"""

from cuneiform.random import SexaRandom, SmoothRandom, CuneiformDice

# --- Basic random sexagesimal values ---
print("=== Random Sexa values in [0, 1) ===")
rng = SexaRandom(seed=42)
for i in range(5):
    s = rng.sexa(digits=4)
    print(f"  {s}  =  {float(s):.6f}  cuneiform: {s.cuneiform()}")

# --- Random integers in sexagesimal ---
print("\n=== Random integers 1..3600 (in sexa notation) ===")
rng = SexaRandom(seed=7)
for i in range(5):
    from cuneiform.core import Sexa
    val = rng.randint(1, 3600)
    s = Sexa(val)
    print(f"  {val:>5d} = {s}")

# --- Smooth (regular) random numbers ---
print("\n=== Random regular (5-smooth) numbers ===")
sr = SmoothRandom(seed=13)
for i in range(5):
    n, recip = sr.reciprocal_pair()
    print(f"  {n}  ×  {recip}  =  1")

# --- Tablet problems ---
print("\n=== Random tablet multiplication problems ===")
sr = SmoothRandom(seed=99)
for i in range(3):
    prob = sr.tablet_problem()
    print(f"  {prob['display']}")

# --- Cuneiform dice ---
print("\n=== Astragalus (knuckle bone) rolls ===")
dice = CuneiformDice(seed=42)
for i in range(6):
    r = dice.astragalus()
    print(f"  Roll {i+1}: {r['cuneiform']}  ({r['value']})")

print("\n=== 3d60 roll ===")
dice = CuneiformDice(seed=42)
result = dice.roll_total(n=3, sides=60)
for i, r in enumerate(result["rolls"]):
    print(f"  Die {i+1}: {r['cuneiform']}  ({r['value']})")
print(f"  Total: {result['cuneiform']}  ({result['total']})")
