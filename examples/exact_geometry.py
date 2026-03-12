#!/usr/bin/env python3
"""Exact Geometry — solve triangles without sin, cos, or pi.

Demonstrates Wildberger's rational trigonometry through CUNEIFORM:
quadrance replaces distance, spread replaces angle.
Everything is exact. No floating point. No approximation.
"""

from cuneiform.core.rational import SexaRational
from cuneiform.geometry.point import RatPoint
from cuneiform.geometry.triangle import RatTriangle
from cuneiform.geometry.constructions import circumcenter, orthocenter, centroid


# A classic 3-4-5 right triangle
print("=== 3-4-5 Right Triangle ===")
tri = RatTriangle.from_triple(3, 4, 5)
print(f"Vertices: A={tri.A}, B={tri.B}, C={tri.C}")
print(f"Quadrances: Q_a={tri.Q_a}, Q_b={tri.Q_b}, Q_c={tri.Q_c}")
print(f"Spreads:    s_A={tri.s_A}, s_B={tri.s_B}, s_C={tri.s_C}")
print(f"Right triangle? {tri.is_right()} (at vertex {tri.right_vertex()})")

# Verify all laws hold exactly
laws = tri.verify_all_laws()
print("\nLaw verification:")
for name, holds in laws.items():
    print(f"  {name}: {holds}")

# A non-right triangle: (0,0), (5,0), (2,3)
print("\n=== General Triangle ===")
A = RatPoint(SexaRational(0), SexaRational(0))
B = RatPoint(SexaRational(5), SexaRational(0))
C = RatPoint(SexaRational(2), SexaRational(3))
tri2 = RatTriangle(A, B, C)

print(f"Quadrances: {tri2.Q_a}, {tri2.Q_b}, {tri2.Q_c}")
print(f"Spreads:    {tri2.s_A}, {tri2.s_B}, {tri2.s_C}")
print(f"16 × Area²: {tri2.area_quadrance_16()}")

# Triangle centers — all exact
print("\n=== Exact Triangle Centers ===")
cc = circumcenter(A, B, C)
oc = orthocenter(A, B, C)
gc = centroid(A, B, C)
print(f"Circumcenter: ({cc.x}, {cc.y})")
print(f"Orthocenter:  ({oc.x}, {oc.y})")
print(f"Centroid:     ({gc.x}, {gc.y})")

# From Plimpton 322 — the first row
print("\n=== Plimpton 322, Row 1: (119, 120, 169) ===")
p322 = RatTriangle.from_triple(119, 120, 169)
print(f"Spread at width:  {p322.s_A}")
print(f"  ≈ {p322.s_A.classical_angle_approx():.4f}°")
print(f"Spread at length: {p322.s_B}")
print(f"  ≈ {p322.s_B.classical_angle_approx():.4f}°")
print(f"All laws hold: {all(p322.verify_all_laws().values())}")
