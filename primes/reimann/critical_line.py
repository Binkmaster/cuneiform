"""The critical-line proportion: a century of bounds, all regular sexagesimals.

The Riemann Hypothesis says 100% of nontrivial zeta zeros lie on the
critical line Re(s) = 1/2. Short of a proof, mathematicians have fought
for the next best thing: an unconditional lower bound on the *proportion*
of zeros on the line.

    1914  Hardy                              infinitely many (no proportion)
    1942  Selberg                            a positive proportion
    1974  Levinson                           more than 1/3
    1989  Conrey                             more than 2/5
    2020  Pratt-Robles-Zaharescu-Zeindler    more than 5/12
    2026  Claude (Anthropic)                 at least 269/400 = 67.25%

The August 2026 result — obtained by a research version of Claude by
combining Baluyot-Goldston-Suriajaya-Turnage-Butterbaugh's unconditional
adaptation of Montgomery's pair correlation with Bombieri's 2000 work,
checked by Conrey and Goldston and formalized in Lean — is the largest
single jump in the bound's history: +25.58 percentage points, versus the
+0.9 points the record advanced in the three decades before it.

CUNEIFORM's angle: every quantified record in this history is a REGULAR
sexagesimal — a rational whose denominator divides a power of 60, so its
base-60 expansion terminates:

    1/3     = 0;20
    2/5     = 0;24
    5/12    = 0;25        (the 2020 record is exactly 25 in one digit!)
    269/400 = 0;40,21

Even the jump itself (307/1200 = 0;15,21) and the distance still to go
(131/400 = 0;19,39) terminate. A Babylonian scribe could have tabulated
the entire history of this bound exactly.
"""

from __future__ import annotations

import sys
import os
from dataclasses import dataclass
from fractions import Fraction

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from cuneiform.core.sexagesimal import Sexa
from cuneiform.core.rational import SexaRational


@dataclass(frozen=True)
class CriticalLineBound:
    """One record in the history of the critical-line proportion bound."""

    year: int
    who: str
    proportion: Fraction | None  # None for unquantified milestones
    note: str

    @property
    def sexa(self) -> Sexa | None:
        if self.proportion is None:
            return None
        return Sexa(self.proportion)

    @property
    def is_regular(self) -> bool:
        """Does the bound have a terminating base-60 expansion?"""
        if self.proportion is None:
            return False
        return SexaRational(self.proportion.numerator,
                            self.proportion.denominator).is_regular


# The reported 2026 threshold is "at least 67.250%" = 269/400.
CLAUDE_2026 = Fraction(269, 400)

BOUND_HISTORY: list[CriticalLineBound] = [
    CriticalLineBound(1914, "Hardy", None,
                      "infinitely many zeros on the line"),
    CriticalLineBound(1942, "Selberg", None,
                      "a positive (unquantified) proportion"),
    CriticalLineBound(1974, "Levinson", Fraction(1, 3),
                      "mollifier method"),
    CriticalLineBound(1989, "Conrey", Fraction(2, 5),
                      "longer mollifiers, Levinson's method"),
    CriticalLineBound(2020, "Pratt-Robles-Zaharescu-Zeindler", Fraction(5, 12),
                      "high-degree mollified moments"),
    CriticalLineBound(2026, "Claude (Anthropic)", CLAUDE_2026,
                      "pair correlation without RH + Bombieri (2000); "
                      "Lean-formalized, community review ongoing"),
]


def quantified_bounds() -> list[CriticalLineBound]:
    """The records that carry an actual proportion."""
    return [b for b in BOUND_HISTORY if b.proportion is not None]


def improvement(older: CriticalLineBound, newer: CriticalLineBound) -> Fraction:
    """Exact gain between two quantified records."""
    if older.proportion is None or newer.proportion is None:
        raise ValueError("both bounds must be quantified")
    return newer.proportion - older.proportion


def remaining_gap(bound: CriticalLineBound) -> Fraction:
    """Exact distance from a record to what RH asserts (proportion 1)."""
    if bound.proportion is None:
        raise ValueError("bound must be quantified")
    return 1 - bound.proportion


def main() -> None:
    print("=" * 72)
    print("PROPORTION OF ZETA ZEROS ON THE CRITICAL LINE")
    print("Unconditional lower bounds, 1914-2026")
    print("=" * 72)
    print()
    print(f"{'Year':<6}{'Record holder':<36}{'Exact':>9}{'Base 60':>11}{'%':>9}")
    print("-" * 72)
    for b in BOUND_HISTORY:
        if b.proportion is None:
            print(f"{b.year:<6}{b.who:<36}{'—':>9}{'—':>11}{'—':>9}")
        else:
            pct = f"{float(b.proportion) * 100:.3f}"
            print(f"{b.year:<6}{b.who:<36}"
                  f"{str(b.proportion):>9}{str(b.sexa):>11}{pct:>9}")
    print()

    prev, latest = quantified_bounds()[-2:]
    jump = improvement(prev, latest)
    gap = remaining_gap(latest)
    print("The 2026 jump and what remains (all exact, all terminating):")
    print(f"  gain over {prev.year}:  {jump}  =  {Sexa(jump)}"
          f"  ({float(jump) * 100:.3f} points)")
    print(f"  distance to RH:  {gap}  =  {Sexa(gap)}"
          f"  ({float(gap) * 100:.3f} points)")
    print()

    print("Every quantified record is a regular sexagesimal:")
    for b in quantified_bounds():
        assert b.is_regular
        print(f"  {str(b.proportion):>8}  =  {str(b.sexa):<8}  "
              f"{b.sexa.cuneiform()}")
    print()
    print("Caveat: 67.25% is a lower bound on zeros ON the line, not a proof")
    print("that all of them are. RH remains open.")


if __name__ == "__main__":
    main()
