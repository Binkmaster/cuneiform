"""Extended Plimpton 322 tabulator — CSV/JSON output.

Generates the largest-ever extension of humanity's oldest trigonometric table.
The original tablet has 15 rows. This generates thousands.

Usage:
    tab = PlimptonTabulator(max_regular=10000)
    rows = tab.generate()
    csv = tab.to_csv(rows)
"""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass, asdict
from fractions import Fraction
from math import gcd

from cuneiform.core.smooth import generate_smooth_numbers


@dataclass
class PlimptonRow:
    """A row of the extended Plimpton table."""
    row_number: int
    p: int
    q: int
    width: int       # p^2 - q^2
    length: int      # 2pq
    diagonal: int    # p^2 + q^2
    d_over_l_sq: str  # (d/l)^2 as fraction string
    spread: str       # width^2 / diagonal^2 as fraction string
    is_original: bool  # True if this is one of the original 15 rows


# The original 15 (p, q) pairs from the tablet
_ORIGINAL_PQ = [
    (12, 5), (64, 27), (75, 32), (125, 54), (9, 4),
    (20, 9), (54, 25), (32, 15), (25, 12), (81, 40),
    (2, 1), (48, 25), (15, 8), (50, 27), (9, 5),
]


class PlimptonTabulator:
    """Generate extended Plimpton 322 tables.

    Uses the reciprocal pair method: for each pair of regular numbers
    (p, q) with p > q, gcd(p,q) = 1, and p-q odd, generate the
    Pythagorean triple (p^2 - q^2, 2pq, p^2 + q^2).
    """

    def __init__(self, max_regular: int = 1000):
        self.max_regular = max_regular

    def generate(self) -> list[PlimptonRow]:
        """Generate all valid Plimpton rows up to max_regular.

        Returns rows sorted by decreasing spread (matching the
        original tablet's ordering convention).
        """
        smooth_nums = generate_smooth_numbers(self.max_regular)
        smooth_values = sorted(s.value for s in smooth_nums if s.value >= 1)

        original_set = set(_ORIGINAL_PQ)
        rows = []

        for i, p_val in enumerate(smooth_values):
            for q_val in smooth_values:
                if q_val >= p_val:
                    break
                # Allow all coprime pairs (original tablet includes
                # non-primitive triples like row 15: p=9, q=5)
                if gcd(p_val, q_val) != 1:
                    continue

                width = p_val * p_val - q_val * q_val
                length = 2 * p_val * q_val
                diagonal = p_val * p_val + q_val * q_val

                d_over_l_sq = Fraction(diagonal * diagonal, length * length)
                spread = Fraction(width * width, diagonal * diagonal)

                rows.append(PlimptonRow(
                    row_number=0,  # Will be assigned after sorting
                    p=p_val,
                    q=q_val,
                    width=width,
                    length=length,
                    diagonal=diagonal,
                    d_over_l_sq=str(d_over_l_sq),
                    spread=str(spread),
                    is_original=(p_val, q_val) in original_set,
                ))

        # Sort by decreasing spread (matching tablet convention)
        rows.sort(key=lambda r: Fraction(r.spread), reverse=True)

        # Assign row numbers
        for i, row in enumerate(rows):
            row.row_number = i + 1

        return rows

    def to_csv(self, rows: list[PlimptonRow] | None = None) -> str:
        """Generate CSV output."""
        if rows is None:
            rows = self.generate()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "row", "p", "q", "width", "length", "diagonal",
            "d_over_l_squared", "spread", "is_original_15"
        ])
        for row in rows:
            writer.writerow([
                row.row_number, row.p, row.q,
                row.width, row.length, row.diagonal,
                row.d_over_l_sq, row.spread,
                row.is_original,
            ])
        return output.getvalue()

    def to_json(self, rows: list[PlimptonRow] | None = None,
                indent: int = 2) -> str:
        """Generate JSON output."""
        if rows is None:
            rows = self.generate()
        return json.dumps([asdict(r) for r in rows], indent=indent)

    def statistics(self, rows: list[PlimptonRow] | None = None) -> dict:
        """Compute table statistics."""
        if rows is None:
            rows = self.generate()

        spreads = [Fraction(r.spread) for r in rows]

        return {
            "total_rows": len(rows),
            "max_regular": self.max_regular,
            "original_rows_found": sum(1 for r in rows if r.is_original),
            "spread_range": (str(min(spreads)), str(max(spreads))) if spreads else ("0", "0"),
            "max_width": max(r.width for r in rows) if rows else 0,
            "max_diagonal": max(r.diagonal for r in rows) if rows else 0,
        }
