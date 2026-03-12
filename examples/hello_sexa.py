#!/usr/bin/env python3
"""Hello, Sexagesimal! — First CUNEIFORM program.

Demonstrates the basics: creating sexagesimal numbers,
exact arithmetic, and the key insight of base-60.
"""

from cuneiform import Sexa

# In base 10, 1/3 = 0.333... (repeating forever)
# In base 60, 1/3 = 0;20 (exact, terminating)
one_third = Sexa.from_fraction(1, 3)
print(f"1/3 in base 60: {one_third.notation}")
print(f"  Cuneiform: {one_third.cuneiform()}")

# 1/7 does NOT terminate in base 60 (7 is not 5-smooth)
try:
    one_seventh = Sexa.from_fraction(1, 7)
    print(f"1/7 = {one_seventh}")
except Exception as e:
    print(f"1/7 is IRREGULAR: {e}")

# Exact arithmetic — no floating point, ever
a = Sexa.from_notation("1;30")   # = 1.5
b = Sexa.from_notation("0;40")   # = 2/3
c = a * b
print(f"\n{a.notation} × {b.notation} = {c.notation}")
print(f"That's {float(a.as_fraction)} × {float(b.as_fraction)} = {float(c.as_fraction)}")

# The Babylonians' power: reciprocals
print("\nBabylonian reciprocal table:")
for n in [2, 3, 4, 5, 6, 8, 9, 10, 12, 15, 16, 18, 20, 24, 25, 27, 30]:
    recip = Sexa.from_fraction(1, n)
    print(f"  1/{n:2d} = {recip.notation}")
