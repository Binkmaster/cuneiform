"""Plimpton 322 — the original 15 rows + reconstruction & extension.

Plimpton 322 is a Babylonian clay tablet (c. 1800 BCE) held at Columbia
University. It contains a table of Pythagorean triples generated using the
reciprocal pair method, with every ratio exact in sexagesimal.

The tablet has 4 columns and 15 rows. The standard interpretation
(Neugebauer & Sachs 1945, refined by Bruins 1949, Mansfield & Wildberger 2017):

  Column I:   (d/l)² = (p² + q²)² / (2pq)²  — the "secant squared" ratio
  Column II:  width  = p² - q²                — the short side
  Column III: diagonal = p² + q²              — the hypotenuse
  Column IV:  row number (1-15)

where p and q are regular (5-smooth) numbers with p > q > 0, gcd(p,q) = 1,
and p - q is odd (to ensure a primitive triple).

The tablet is sorted by decreasing (d/l)², which corresponds to spreads
ranging from just under 1 (nearly 45°) down to about 1/4 (about 31°).

Known scribal errors in the original tablet:
  Row 2:  Column I (d/l)² contains a computational error
  Row 9:  width written as 9,01 instead of correct 8,01 (541 vs 481)
  Row 13: width written as 7,12,01 instead of 2,41 (25921 vs 161; scribe squared it)
  Row 15: diagonal written as 53 instead of correct 1,46 (53 vs 106; scribe halved it)

References:
  - Neugebauer & Sachs, "Mathematical Cuneiform Texts" (1945)
  - Robson, "Neither Sherlock Holmes nor Babylon" (2001)
  - Mansfield & Wildberger, "Plimpton 322 is Babylonian exact sexagesimal
    trigonometry" (2017), Historia Mathematica 44(4), 395-419
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from math import gcd

from cuneiform.core.sexagesimal import Sexa
from cuneiform.core.rational import SexaRational
from cuneiform.core.smooth import SmoothNumber, generate_smooth_numbers


@dataclass
class PlimptonRow:
    """A single row of a Plimpton-style table."""

    row_number: int
    p: int
    q: int
    width: int          # short side: p² - q²
    length: int         # long side: 2pq
    diagonal: int       # hypotenuse: p² + q²
    d_over_l_sq: Fraction   # (d/l)² — Column I of original tablet
    # Scribal error info (only for original 15 rows)
    tablet_width: int | None = None      # value as written on tablet (if error)
    tablet_diagonal: int | None = None   # value as written on tablet (if error)
    tablet_col1_error: bool = False       # Column I (d/l)² error on tablet

    @property
    def triple(self) -> tuple[int, int, int]:
        return (self.width, self.length, self.diagonal)

    @property
    def is_primitive(self) -> bool:
        return gcd(gcd(self.width, self.length), self.diagonal) == 1

    @property
    def has_scribal_error(self) -> bool:
        return (self.tablet_width is not None or
                self.tablet_diagonal is not None or
                self.tablet_col1_error)

    @property
    def spread_width(self) -> Fraction:
        """Spread at the width vertex = width² / diagonal²."""
        return Fraction(self.width * self.width, self.diagonal * self.diagonal)

    @property
    def spread_length(self) -> Fraction:
        """Spread at the length vertex = length² / diagonal²."""
        return Fraction(self.length * self.length, self.diagonal * self.diagonal)

    def width_sexa(self) -> Sexa:
        return Sexa(self.width)

    def diagonal_sexa(self) -> Sexa:
        return Sexa(self.diagonal)

    def d_over_l_sq_sexa(self) -> Sexa:
        return Sexa(self.d_over_l_sq)

    def all_ratios(self) -> dict[str, SexaRational]:
        """Every side ratio as SexaRational."""
        return {
            "w/l": SexaRational(self.width, self.length),
            "w/d": SexaRational(self.width, self.diagonal),
            "l/d": SexaRational(self.length, self.diagonal),
            "l/w": SexaRational(self.length, self.width),
            "d/w": SexaRational(self.diagonal, self.width),
            "d/l": SexaRational(self.diagonal, self.length),
        }

    def format_row(self, show_sexa: bool = True) -> str:
        """Format for display."""
        error = " *" if self.has_scribal_error else ""
        line = (
            f"Row {self.row_number:>2}: "
            f"p={self.p:<4} q={self.q:<4} "
            f"({self.width}, {self.length}, {self.diagonal})"
        )
        if show_sexa:
            line += (
                f"  w={self.width_sexa()!r:>12}"
                f"  d={self.diagonal_sexa()!r:>12}"
                f"  (d/l)²={self.d_over_l_sq_sexa()!r}"
            )
        line += error
        return line

    def __repr__(self) -> str:
        return (
            f"PlimptonRow(#{self.row_number}, p={self.p}, q={self.q}, "
            f"triple=({self.width}, {self.length}, {self.diagonal}))"
        )


# The 15 known generating pairs from the original tablet, in tablet order
# (sorted by decreasing d/l²).
# Sources: Neugebauer & Sachs 1945; Robson 2001; Mansfield & Wildberger 2017.
_ORIGINAL_PAIRS: list[tuple[int, int]] = [
    (12, 5),
    (64, 27),
    (75, 32),
    (125, 54),
    (9, 4),
    (20, 9),
    (54, 25),
    (32, 15),
    (25, 12),
    (81, 40),
    (2, 1),
    (48, 25),
    (15, 8),
    (50, 27),
    (9, 5),
]

# Known scribal errors: row_number -> (tablet_width, tablet_diagonal)
# None means the tablet value is correct for that field.
# Known scribal errors: row_number -> (tablet_width, tablet_diagonal, col1_error)
# None means the tablet value is correct for that field.
_SCRIBAL_ERRORS: dict[int, tuple[int | None, int | None, bool]] = {
    2:  (None, None, True),   # Column I computational error
    9:  (541, None, False),   # width: 9,01 instead of 8,01 (481)
    13: (25921, None, False), # width: 7,12,01 instead of 2,41 (161); scribe squared it
    15: (None, 53, False),    # diagonal: 53 instead of 1,46 (106); scribe halved it
}


def _make_row(row_number: int, p: int, q: int) -> PlimptonRow:
    """Construct a PlimptonRow from generating pair (p, q)."""
    w = p * p - q * q
    l = 2 * p * q
    d = p * p + q * q

    assert w * w + l * l == d * d, f"Not a Pythagorean triple: {w}, {l}, {d}"

    d_over_l_sq = Fraction(d * d, l * l)

    tablet_w = None
    tablet_d = None
    col1_err = False
    if row_number in _SCRIBAL_ERRORS:
        tablet_w, tablet_d, col1_err = _SCRIBAL_ERRORS[row_number]

    return PlimptonRow(
        row_number=row_number,
        p=p, q=q,
        width=w, length=l, diagonal=d,
        d_over_l_sq=d_over_l_sq,
        tablet_width=tablet_w,
        tablet_diagonal=tablet_d,
        tablet_col1_error=col1_err,
    )


class Plimpton322:
    """The Plimpton 322 tablet: original 15 rows and extended generation.

    Usage:
        tablet = Plimpton322()
        for row in tablet.original():
            print(row.format_row())

        # Extended table with larger regular number bound
        for row in tablet.extended(max_regular=1000):
            print(row.triple)
    """

    def original(self) -> list[PlimptonRow]:
        """Return the original 15 rows of Plimpton 322.

        Includes scribal error annotations. The corrected mathematical
        values are always in width/diagonal; the erroneous tablet values
        are in tablet_width/tablet_diagonal when they differ.
        """
        rows = []
        for i, (p, q) in enumerate(_ORIGINAL_PAIRS, start=1):
            rows.append(_make_row(i, p, q))
        return rows

    def extended(self, max_regular: int = 125) -> list[PlimptonRow]:
        """Generate an extended Plimpton table.

        Uses all pairs (p, q) of regular numbers where:
        - p > q > 0
        - gcd(p, q) = 1
        - p and q are not both odd (ensures primitive triple)

        Args:
            max_regular: largest regular number to use for p.
                Original tablet uses 125 (= 2,05 in base 60).

        Returns:
            Rows sorted by decreasing d/l² (spread), matching
            the original tablet's ordering convention.
        """
        regulars = generate_smooth_numbers(max_regular)
        regular_values = [s.value for s in regulars if s.value > 0]

        rows = []
        row_num = 0
        for p in regular_values:
            for q in regular_values:
                if q >= p:
                    continue
                if gcd(p, q) != 1:
                    continue
                # For a primitive triple, p and q must not both be odd
                if p % 2 == 1 and q % 2 == 1:
                    continue

                row_num += 1
                w = p * p - q * q
                l = 2 * p * q
                d = p * p + q * q
                d_over_l_sq = Fraction(d * d, l * l)

                rows.append(PlimptonRow(
                    row_number=row_num,
                    p=p, q=q,
                    width=w, length=l, diagonal=d,
                    d_over_l_sq=d_over_l_sq,
                ))

        # Sort by d/l² descending (original tablet ordering)
        rows.sort(key=lambda r: r.d_over_l_sq, reverse=True)
        # Renumber after sorting
        for i, row in enumerate(rows, start=1):
            row.row_number = i

        return rows

    def coverage_report(self, rows: list[PlimptonRow] | None = None) -> dict:
        """Analyze spread coverage of a table.

        Returns statistics on how well the table covers the spread
        range, addressing the criticism that Plimpton 322 has gaps.
        """
        if rows is None:
            rows = self.original()

        spreads = sorted(set(row.spread_width for row in rows))

        if len(spreads) < 2:
            return {
                "num_rows": len(rows),
                "num_unique_spreads": len(spreads),
                "spread_range": (spreads[0], spreads[-1]) if spreads else (0, 0),
                "max_gap": Fraction(0),
                "avg_gap": Fraction(0),
                "gaps": [],
            }

        gaps = [spreads[i + 1] - spreads[i] for i in range(len(spreads) - 1)]
        max_gap = max(gaps)
        avg_gap = sum(gaps) / len(gaps)

        return {
            "num_rows": len(rows),
            "num_unique_spreads": len(spreads),
            "spread_range": (float(spreads[0]), float(spreads[-1])),
            "max_gap": float(max_gap),
            "avg_gap": float(avg_gap),
            "gaps": [float(g) for g in gaps],
        }

    def density_scaling(
        self, bounds: list[int] | None = None
    ) -> list[dict]:
        """Generate tables at increasing bounds and measure coverage.

        This is the key experiment: does coverage fill in as the
        regular number bound increases?
        """
        if bounds is None:
            bounds = [125, 250, 500, 1000, 2000]

        results = []
        for b in bounds:
            rows = self.extended(max_regular=b)
            report = self.coverage_report(rows)
            results.append({
                "bound": b,
                "num_rows": report["num_rows"],
                "num_unique_spreads": report["num_unique_spreads"],
                "max_gap": report["max_gap"],
                "avg_gap": report["avg_gap"],
                "spread_range": report["spread_range"],
            })
        return results

    def format_table(
        self, rows: list[PlimptonRow] | None = None, show_sexa: bool = True
    ) -> str:
        """Format the table for display."""
        if rows is None:
            rows = self.original()

        lines = [
            "PLIMPTON 322 — Pythagorean Triples via Reciprocal Pairs",
            "=" * 72,
        ]

        for row in rows:
            lines.append(row.format_row(show_sexa=show_sexa))

        error_rows = [r for r in rows if r.has_scribal_error]
        if error_rows:
            lines.append("")
            lines.append("* = known scribal error on original tablet:")
            for r in error_rows:
                parts = []
                if r.tablet_col1_error:
                    parts.append(
                        f"  Row {r.row_number}: Column I (d/l)² computational error"
                    )
                if r.tablet_width is not None:
                    parts.append(
                        f"  Row {r.row_number}: width on tablet = "
                        f"{Sexa(r.tablet_width)!r} ({r.tablet_width}), "
                        f"correct = {r.width_sexa()!r} ({r.width})"
                    )
                if r.tablet_diagonal is not None:
                    parts.append(
                        f"  Row {r.row_number}: diagonal on tablet = "
                        f"{Sexa(r.tablet_diagonal)!r} ({r.tablet_diagonal}), "
                        f"correct = {r.diagonal_sexa()!r} ({r.diagonal})"
                    )
                lines.extend(parts)

        return "\n".join(lines)

    def export_csv(self, rows: list[PlimptonRow] | None = None) -> str:
        """Export table as CSV."""
        if rows is None:
            rows = self.original()

        lines = [
            "row,p,q,width,length,diagonal,"
            "width_sexa,diagonal_sexa,d_over_l_sq_sexa,"
            "spread_width,spread_length,primitive,scribal_error"
        ]
        for r in rows:
            lines.append(
                f"{r.row_number},{r.p},{r.q},"
                f"{r.width},{r.length},{r.diagonal},"
                f"{r.width_sexa()!r},{r.diagonal_sexa()!r},{r.d_over_l_sq_sexa()!r},"
                f"{float(r.spread_width):.10f},{float(r.spread_length):.10f},"
                f"{r.is_primitive},{r.has_scribal_error}"
            )
        return "\n".join(lines)
