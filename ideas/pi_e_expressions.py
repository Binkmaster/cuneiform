#!/usr/bin/env python3
"""Compute π, e, and expressions thereof in Babylonian sexagesimal cuneiform.

Uses the cuneiform library's exact rational arithmetic (Sexa class) with
high-precision rational approximations of transcendental constants via
Machin-type formulas and Taylor series.

For irrational powers (π^π, e^e, etc.) we use mpmath for high-precision
decimal computation, then convert to Fraction approximations.
"""

import sys
from fractions import Fraction
from pathlib import Path
from decimal import Decimal, getcontext

# High precision for Decimal conversions
getcontext().prec = 120

import mpmath
mpmath.mp.dps = 100  # 100 decimal digits of precision

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cuneiform.core import Sexa

# Reuse the pi.py helpers
from ideas.pi import machin_pi, _arctan_rational, _isqrt_rational


# =============================================================================
# Helpers
# =============================================================================

def _sexa_str(s: Sexa, frac_places: int = 8) -> str:
    """Format a Sexa with a specified number of fractional digits."""
    int_digits, frac_digits, negative = s.digits(max_frac_digits=frac_places)
    sign = "-" if negative else ""
    int_str = ",".join(str(d) for d in int_digits)
    frac_digits = frac_digits[:frac_places]
    if frac_digits:
        frac_str = ",".join(str(d) for d in frac_digits)
        return f"{sign}{int_str};{frac_str}"
    return f"{sign}{int_str}"


def _cuneiform_str(s: Sexa, frac_places: int = 8) -> str:
    """Render cuneiform with controlled fractional digits."""
    int_digits, frac_digits, negative = s.digits(max_frac_digits=frac_places)
    from cuneiform.core.sexagesimal import _digit_to_cuneiform
    sign = "-" if negative else ""
    int_str = " ".join(_digit_to_cuneiform(d) for d in int_digits)
    frac_digits = frac_digits[:frac_places]
    if frac_digits:
        frac_str = " ".join(_digit_to_cuneiform(d) for d in frac_digits)
        return f"{sign}{int_str} ; {frac_str}"
    return f"{sign}{int_str}"


def mpf_to_sexa(value: mpmath.mpf, label: str = "") -> Sexa:
    """Convert an mpmath high-precision float to a Sexa via Fraction.

    We convert through a string decimal representation to preserve precision.
    """
    # Get a high-precision string
    s = mpmath.nstr(value, 80, strip_zeros=False)
    frac = Fraction(s)
    return Sexa._from_frac(frac)


def rational_e(terms: int = 60) -> Sexa:
    """Compute e via the Taylor series: e = sum(1/k!) using exact Fractions.

    60 terms gives enormous precision since k! grows super-exponentially.
    """
    total = Fraction(0)
    factorial = Fraction(1)
    for k in range(terms):
        total += Fraction(1) / factorial
        factorial *= (k + 1)
    return Sexa._from_frac(total)


# =============================================================================
# Part 1: The Constants
# =============================================================================

def compute_constants():
    """Compute and display π and e in sexagesimal."""
    print("=" * 78)
    print("  PART 1: π AND e IN BABYLONIAN SEXAGESIMAL")
    print("=" * 78)

    # π via Machin's formula (80 terms → ~65 sexagesimal digits precision)
    pi_sexa = machin_pi(80)
    # e via Taylor series (60 terms → enormous precision)
    e_sexa = rational_e(60)

    print("\n  π ≈ 3.14159265358979323846...")
    print(f"    Decimal:      {float(pi_sexa):.20f}")
    print(f"    Sexagesimal:  {_sexa_str(pi_sexa, 8)}")
    print(f"    Cuneiform:    {_cuneiform_str(pi_sexa, 6)}")

    # Show the breakdown
    int_d, frac_d, _ = pi_sexa.digits(max_frac_digits=8)
    print(f"\n    Breakdown: {int_d[0]} + ", end="")
    for i, d in enumerate(frac_d[:8]):
        print(f"{d}/60^{i+1}", end="")
        if i < 7:
            print(" + ", end="")
    print()

    print(f"\n    Babylonian approximation: 3;7,30 = 25/8 = 3.125")
    print(f"    Our value:               {_sexa_str(pi_sexa, 2)} ≈ {float(pi_sexa):.15f}")
    print(f"    The Babylonians were off by ~{abs(float(pi_sexa) - 3.125):.6f}")

    print("\n  " + "-" * 74)

    print("\n  e ≈ 2.71828182845904523536...")
    print(f"    Decimal:      {float(e_sexa):.20f}")
    print(f"    Sexagesimal:  {_sexa_str(e_sexa, 8)}")
    print(f"    Cuneiform:    {_cuneiform_str(e_sexa, 6)}")

    int_d, frac_d, _ = e_sexa.digits(max_frac_digits=8)
    print(f"\n    Breakdown: {int_d[0]} + ", end="")
    for i, d in enumerate(frac_d[:8]):
        print(f"{d}/60^{i+1}", end="")
        if i < 7:
            print(" + ", end="")
    print()

    return pi_sexa, e_sexa


# =============================================================================
# Part 2: The Expressions
# =============================================================================

def compute_expressions(pi_sexa: Sexa, e_sexa: Sexa):
    """Compute π/e expressions and render in sexagesimal cuneiform."""
    print("\n\n" + "=" * 78)
    print("  PART 2: EXPRESSIONS IN BABYLONIAN SEXAGESIMAL CUNEIFORM")
    print("=" * 78)

    # For exact rational operations we can use Sexa arithmetic directly
    # For irrational powers we need mpmath
    mp_pi = mpmath.pi
    mp_e = mpmath.e

    expressions = [
        ("π + e",    pi_sexa + e_sexa,              mp_pi + mp_e),
        ("π − e",    pi_sexa - e_sexa,              mp_pi - mp_e),
        ("π × e",    pi_sexa * e_sexa,              mp_pi * mp_e),
        ("π / e",    pi_sexa / e_sexa,              mp_pi / mp_e),
        ("π^π",      mpf_to_sexa(mp_pi ** mp_pi),   mp_pi ** mp_pi),
        ("e^e",      mpf_to_sexa(mp_e ** mp_e),     mp_e ** mp_e),
        ("π^e",      mpf_to_sexa(mp_pi ** mp_e),    mp_pi ** mp_e),
        ("π^√2",     mpf_to_sexa(mp_pi ** mpmath.sqrt(2)), mp_pi ** mpmath.sqrt(2)),
        ("e^(π²)",   mpf_to_sexa(mp_e ** (mp_pi**2)), mp_e ** (mp_pi**2)),
    ]

    for label, sexa_val, mp_val in expressions:
        decimal_val = float(mp_val)
        print(f"\n  {label}")
        print(f"    Decimal:      {mpmath.nstr(mp_val, 25)}")
        print(f"    Sexagesimal:  {_sexa_str(sexa_val, 6)}")
        print(f"    Cuneiform:    {_cuneiform_str(sexa_val, 4)}")

    return expressions


# =============================================================================
# Part 3: Number-theoretic status of the expressions
# =============================================================================

def number_theory_status():
    """Display what is known/unknown about the number-theoretic status."""
    print("\n\n" + "=" * 78)
    print("  NUMBER-THEORETIC STATUS OF THESE EXPRESSIONS")
    print("=" * 78)

    status = [
        ("π",      "Transcendental", "Lindemann (1882)"),
        ("e",      "Transcendental", "Hermite (1873)"),
        ("π + e",  "Irrational?",    "UNKNOWN — conjectured transcendental"),
        ("π − e",  "Irrational?",    "UNKNOWN — conjectured transcendental"),
        ("π × e",  "Irrational?",    "UNKNOWN — conjectured transcendental"),
        ("π / e",  "Irrational?",    "UNKNOWN — conjectured transcendental"),
        ("π^π",    "Irrational?",    "UNKNOWN — conjectured transcendental"),
        ("e^e",    "Irrational?",    "UNKNOWN — conjectured transcendental"),
        ("π^e",    "Irrational?",    "UNKNOWN — conjectured transcendental"),
        ("π^√2",   "Irrational?",    "UNKNOWN — Gelfond–Schneider doesn't apply (base transcendental)"),
        ("e^(π²)", "Irrational?",    "UNKNOWN — conjectured transcendental"),
    ]

    print(f"\n  {'Expression':<12} {'Status':<20} {'Notes'}")
    print("  " + "-" * 74)
    for expr, stat, notes in status:
        print(f"  {expr:<12} {stat:<20} {notes}")

    print("""
  Key theorems:
  • Lindemann–Weierstrass: e^α is transcendental for algebraic α ≠ 0
    → This gives us e^1 = e (transcendental) and e^(iπ) = -1
    → But e^π and e^(π²) have transcendental exponents, so it doesn't apply
  • Gelfond–Schneider: α^β is transcendental for algebraic α ≠ 0,1 and
    irrational algebraic β
    → Gives us 2^√2 (Gelfond–Schneider constant) is transcendental
    → But π^√2 has transcendental base, so it doesn't apply
  • Schanuel's conjecture (UNPROVEN) would imply all of the above are
    transcendental, but this remains one of the great open problems
  • We know at least one of π+e and π×e is transcendental (since they are
    roots of x²−(π+e)x+πe = 0, and both roots can't be algebraic unless
    the coefficients are too)
  • Similarly, at least one of e^e and e^(e²) is transcendental
""")


# =============================================================================
# ALU Simulation
# =============================================================================

def alu_demo(pi_sexa: Sexa, e_sexa: Sexa):
    """Demonstrate the Sexagesimal ALU with π + e computation."""
    print("=" * 78)
    print("  ALU SIMULATION: π + e ON THE SEXAGESIMAL PROCESSOR")
    print("=" * 78)

    from cuneiform.hardware.sexa_sim import SexaALU, Instruction, Op

    alu = SexaALU()

    # We'll load integer approximations (scaled) into the ALU
    # The ALU works with integer sexagesimal registers
    # Load π ≈ 3;8,29,44 and e ≈ 2;43,5,54 as scaled integers
    # Scale by 60^3 = 216000 to preserve 3 sexagesimal fractional places
    scale = 60 ** 3  # 216000

    pi_scaled = int(float(pi_sexa) * scale)  # ≈ 678792
    e_scaled = int(float(e_sexa) * scale)    # ≈ 587148

    alu.load(0, pi_scaled)
    alu.load(1, e_scaled)

    # Add them
    add_inst = Instruction(Op.SADD, dest=2, src1=0, src2=1)
    alu.execute(add_inst)

    result = alu.read(2)
    result_float = result / scale
    print(f"\n  S0 (π × 60³):  {pi_scaled}")
    print(f"  S1 (e × 60³):  {e_scaled}")
    print(f"  S2 = S0 + S1:  {result}")
    print(f"  Decoded:        {result_float:.10f}")
    print(f"  Expected:       {float(pi_sexa) + float(e_sexa):.10f}")
    print(f"  ALU cycles:     {alu.cycles}")
    print()


# =============================================================================
# Plimpton 322 context
# =============================================================================

def plimpton_context():
    """Show Plimpton 322 for historical context."""
    print("=" * 78)
    print("  HISTORICAL CONTEXT: PLIMPTON 322 TABLET")
    print("=" * 78)

    from cuneiform.tablet.plimpton322 import Plimpton322

    tablet = Plimpton322()
    rows = tablet.original()

    print("\n  The Plimpton 322 tablet (c. 1800 BCE) contains 15 Pythagorean triples")
    print("  organized by decreasing spread (sin²θ), all using regular numbers.")
    print("  The Babylonians worked entirely with RATIONALS — no π, no √2, no e.")
    print()
    print(f"  {'Row':>4}  {'Width':>8}  {'Diagonal':>8}  {'(d/l)²':>20}  Cuneiform")
    print("  " + "-" * 70)
    for row in rows[:5]:
        d_over_l = row.d_over_l_sq_sexa()
        print(f"  {row.row_number:4d}  {row.width:8d}  {row.diagonal:8d}  "
              f"{str(d_over_l):>20s}  {d_over_l.cuneiform()}")
    print(f"  ... ({len(rows)} rows total)")
    print()


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    pi_sexa, e_sexa = compute_constants()
    expressions = compute_expressions(pi_sexa, e_sexa)
    print()
    number_theory_status()
    alu_demo(pi_sexa, e_sexa)
    plimpton_context()

    print("=" * 78)
    print("  ALL DONE — As inscribed in cuneiform on a virtual clay tablet")
    print("=" * 78)
