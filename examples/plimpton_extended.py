#!/usr/bin/env python3
"""Generate an extended Plimpton 322 table.

The original tablet had 15 rows. We can generate hundreds more
using the same reciprocal pair method the Babylonians used.
"""

from cuneiform.tablet.plimpton322 import Plimpton322

tablet = Plimpton322()

# The original 15 rows
print("=== ORIGINAL PLIMPTON 322 (15 rows) ===")
print(tablet.format_table())

# Extended table with max_regular=500
extended = tablet.extended(max_regular=500)
print(f"\n=== EXTENDED TABLE ({len(extended)} rows, max_regular=500) ===")
for i, row in enumerate(extended[:20]):
    w, l, d = row.triple
    print(f"  Row {i+1:3d}: ({w:6d}, {l:6d}, {d:6d})  "
          f"spread={float(row.spreads[0]):.6f}")

print(f"  ... ({len(extended)} total rows)")

# Coverage analysis
report = tablet.coverage_report(max_regular=500)
print(f"\nCoverage: {report['count']} triples")
print(f"Max gap: {report['max_gap']:.4f}")
print(f"Spread range: {report['min_spread']:.6f} to {report['max_spread']:.6f}")
