"""Tablet analyzer — computational tools for decoding mathematical cuneiform tablets.

Given a transcribed mathematical tablet (as a grid of sexagesimal numbers),
attempts to determine what mathematical procedure it represents.
"""

from __future__ import annotations

from fractions import Fraction
from math import gcd

from cuneiform.core.sexagesimal import Sexa
from cuneiform.core.rational import SexaRational
from cuneiform.core.smooth import is_smooth


class TabletAnalyzer:
    """Analyze a mathematical cuneiform tablet.

    Input: a grid of Sexa values (rows × columns) as transcribed
    from a tablet photograph or hand copy.

    Methods:
    1. Pattern matching: compare columns against known relationships
    2. Gap filling: predict missing or damaged entries
    3. Error detection: find potential scribal mistakes
    4. Procedure reconstruction: reverse-engineer the calculation
    """

    def __init__(self, tablet_data: list[list[Sexa | int]]):
        self.data = [
            [v if isinstance(v, Sexa) else Sexa(v) for v in row]
            for row in tablet_data
        ]
        self.num_rows = len(self.data)
        self.num_cols = len(self.data[0]) if self.data else 0

    def _col(self, j: int) -> list[Fraction]:
        """Extract column j as Fractions."""
        return [self.data[i][j].as_fraction for i in range(self.num_rows)]

    def identify_column_relationships(self) -> list[dict]:
        """Test all column pairs/triples for known mathematical relationships.

        Tests:
        - A = B² (squaring)
        - A × B = constant (reciprocal pairs)
        - A² + B² = C² (Pythagorean)
        - A = B + C (addition)
        - A = B - C (subtraction)
        - A / B = constant (constant ratio)
        - A = B * constant (scaling)
        """
        results = []

        for i in range(self.num_cols):
            for j in range(self.num_cols):
                if i == j:
                    continue
                col_i = self._col(i)
                col_j = self._col(j)

                # Test: col_i = col_j squared
                matches = sum(
                    1 for a, b in zip(col_i, col_j) if b != 0 and a == b * b
                )
                if matches >= self.num_rows - 1 and matches > 0:
                    errors = [
                        r for r, (a, b) in enumerate(zip(col_i, col_j))
                        if b != 0 and a != b * b
                    ]
                    results.append({
                        "type": "squaring",
                        "columns": (i, j),
                        "description": f"col[{i}] = col[{j}]²",
                        "matches": matches,
                        "total": self.num_rows,
                        "error_rows": errors,
                    })

                # Test: col_i × col_j = constant
                products = [
                    a * b for a, b in zip(col_i, col_j) if a != 0 and b != 0
                ]
                if len(products) >= 2:
                    if len(set(products)) == 1:
                        results.append({
                            "type": "reciprocal_pair",
                            "columns": (i, j),
                            "description": f"col[{i}] × col[{j}] = {products[0]}",
                            "constant": products[0],
                            "matches": len(products),
                            "total": self.num_rows,
                            "error_rows": [],
                        })
                    elif len(set(products)) == 2 and len(products) >= 3:
                        # Might have one error
                        from collections import Counter
                        counts = Counter(products)
                        common = counts.most_common(1)[0]
                        if common[1] >= len(products) - 1:
                            error_val = [v for v in counts if v != common[0]]
                            error_rows = [
                                r for r, (a, b) in enumerate(zip(col_i, col_j))
                                if a != 0 and b != 0 and a * b != common[0]
                            ]
                            results.append({
                                "type": "reciprocal_pair",
                                "columns": (i, j),
                                "description": f"col[{i}] × col[{j}] ≈ {common[0]}",
                                "constant": common[0],
                                "matches": common[1],
                                "total": self.num_rows,
                                "error_rows": error_rows,
                            })

                # Test: col_i / col_j = constant ratio
                ratios = [
                    a / b for a, b in zip(col_i, col_j) if b != 0
                ]
                if len(ratios) >= 2 and len(set(ratios)) == 1:
                    results.append({
                        "type": "constant_ratio",
                        "columns": (i, j),
                        "description": f"col[{i}] / col[{j}] = {ratios[0]}",
                        "constant": ratios[0],
                        "matches": len(ratios),
                        "total": self.num_rows,
                        "error_rows": [],
                    })

        # Test triples: Pythagorean
        for i in range(self.num_cols):
            for j in range(i + 1, self.num_cols):
                for k in range(self.num_cols):
                    if k == i or k == j:
                        continue
                    col_i = self._col(i)
                    col_j = self._col(j)
                    col_k = self._col(k)

                    matches = sum(
                        1 for a, b, c in zip(col_i, col_j, col_k)
                        if a * a + b * b == c * c
                    )
                    if matches >= self.num_rows - 1 and matches > 0:
                        errors = [
                            r for r, (a, b, c) in enumerate(zip(col_i, col_j, col_k))
                            if a * a + b * b != c * c
                        ]
                        results.append({
                            "type": "pythagorean",
                            "columns": (i, j, k),
                            "description": f"col[{i}]² + col[{j}]² = col[{k}]²",
                            "matches": matches,
                            "total": self.num_rows,
                            "error_rows": errors,
                        })

        # Test pairs: addition
        for i in range(self.num_cols):
            for j in range(i + 1, self.num_cols):
                for k in range(self.num_cols):
                    if k == i or k == j:
                        continue
                    col_i = self._col(i)
                    col_j = self._col(j)
                    col_k = self._col(k)

                    matches = sum(
                        1 for a, b, c in zip(col_i, col_j, col_k)
                        if a + b == c
                    )
                    if matches >= self.num_rows - 1 and matches > 0:
                        errors = [
                            r for r, (a, b, c) in enumerate(zip(col_i, col_j, col_k))
                            if a + b != c
                        ]
                        results.append({
                            "type": "addition",
                            "columns": (i, j, k),
                            "description": f"col[{i}] + col[{j}] = col[{k}]",
                            "matches": matches,
                            "total": self.num_rows,
                            "error_rows": errors,
                        })

        return results

    def check_regularity(self) -> list[dict]:
        """Check which entries are regular (5-smooth denominators/values).

        Babylonian tables typically contain only regular numbers.
        Irregular entries may indicate errors or non-standard content.
        """
        results = []
        for i in range(self.num_rows):
            for j in range(self.num_cols):
                val = self.data[i][j].as_fraction
                num_regular = is_smooth(abs(val.numerator)) if val.numerator != 0 else True
                den_regular = is_smooth(val.denominator)
                if not num_regular or not den_regular:
                    results.append({
                        "row": i,
                        "col": j,
                        "value": val,
                        "numerator_regular": num_regular,
                        "denominator_regular": den_regular,
                    })
        return results

    def suggest_corrections(self) -> list[dict]:
        """Suggest corrections for suspected scribal errors.

        Based on identified relationships, propose corrected values
        for rows that don't match the pattern.
        """
        relationships = self.identify_column_relationships()
        suggestions = []

        for rel in relationships:
            for error_row in rel.get("error_rows", []):
                if rel["type"] == "squaring":
                    ci, cj = rel["columns"]
                    base_val = self.data[error_row][cj].as_fraction
                    expected = base_val * base_val
                    actual = self.data[error_row][ci].as_fraction
                    suggestions.append({
                        "row": error_row,
                        "col": ci,
                        "actual": actual,
                        "expected": expected,
                        "relationship": rel["description"],
                        "confidence": "high" if rel["matches"] >= self.num_rows - 1 else "medium",
                    })
                elif rel["type"] == "reciprocal_pair":
                    ci, cj = rel["columns"]
                    const = rel["constant"]
                    val_j = self.data[error_row][cj].as_fraction
                    val_i = self.data[error_row][ci].as_fraction
                    if val_j != 0:
                        expected_i = const / val_j
                        suggestions.append({
                            "row": error_row,
                            "col": ci,
                            "actual": val_i,
                            "expected": expected_i,
                            "relationship": rel["description"],
                            "confidence": "medium",
                        })

        return suggestions

    def fill_gaps(self, gap_marker: int = -1) -> list[dict]:
        """Predict values for missing entries (marked with gap_marker).

        Uses identified relationships to compute what missing values
        should be.
        """
        relationships = self.identify_column_relationships()
        fills = []

        for i in range(self.num_rows):
            for j in range(self.num_cols):
                if self.data[i][j].as_fraction == Fraction(gap_marker):
                    # Try each relationship to fill this gap
                    for rel in relationships:
                        cols = rel["columns"]
                        if j not in cols:
                            continue
                        predicted = self._predict_from_relationship(i, j, rel)
                        if predicted is not None:
                            fills.append({
                                "row": i,
                                "col": j,
                                "predicted_value": predicted,
                                "via_relationship": rel["description"],
                            })
                            break

        return fills

    def _predict_from_relationship(self, row: int, col: int,
                                    rel: dict) -> Fraction | None:
        """Predict a value using a known relationship."""
        cols = rel["columns"]
        rtype = rel["type"]

        if rtype == "squaring":
            ci, cj = cols
            if col == ci:
                base = self.data[row][cj].as_fraction
                return base * base
            elif col == cj:
                sq = self.data[row][ci].as_fraction
                # Would need sqrt — skip if not perfect square
                return None

        elif rtype == "reciprocal_pair":
            ci, cj = cols
            const = rel["constant"]
            if col == ci:
                other = self.data[row][cj].as_fraction
                return const / other if other != 0 else None
            elif col == cj:
                other = self.data[row][ci].as_fraction
                return const / other if other != 0 else None

        elif rtype == "addition":
            ci, cj, ck = cols
            a = self.data[row][ci].as_fraction
            b = self.data[row][cj].as_fraction
            c = self.data[row][ck].as_fraction
            if col == ck:
                return a + b
            elif col == ci:
                return c - b
            elif col == cj:
                return c - a

        elif rtype == "pythagorean":
            ci, cj, ck = cols
            a = self.data[row][ci].as_fraction
            b = self.data[row][cj].as_fraction
            c = self.data[row][ck].as_fraction
            if col == ck:
                sq = a * a + b * b
                # Check if perfect square
                sr = _isqrt_frac(sq)
                return sr
            # Other cases would need sqrt, skip
            return None

        return None

    def classify_tablet_type(self) -> str:
        """Classify the tablet based on detected patterns.

        Known types:
        - reciprocal_table: products are constant
        - multiplication_table: constant ratios
        - square_table: squaring relationship
        - pythagorean_table: Pythagorean triples
        - unknown: no recognized pattern
        """
        rels = self.identify_column_relationships()
        types_found = {r["type"] for r in rels}

        if "pythagorean" in types_found:
            return "pythagorean_table"
        if "reciprocal_pair" in types_found:
            return "reciprocal_table"
        if "squaring" in types_found:
            return "square_table"
        if "constant_ratio" in types_found:
            return "multiplication_table"
        if "addition" in types_found:
            return "addition_table"
        return "unknown"

    def date_estimate(self) -> dict:
        """Estimate period based on mathematical sophistication and number ranges.

        Old Babylonian (OB, 1900-1600 BCE): moderate numbers, reciprocal pairs,
        specific error patterns.
        Seleucid (300-100 BCE): larger numbers, more sophisticated techniques.
        """
        max_val = max(
            abs(int(self.data[i][j].as_fraction))
            for i in range(self.num_rows)
            for j in range(self.num_cols)
        )

        rels = self.identify_column_relationships()
        has_pythagorean = any(r["type"] == "pythagorean" for r in rels)
        has_reciprocal = any(r["type"] == "reciprocal_pair" for r in rels)

        # Heuristics based on known tablet characteristics
        if max_val > 1_000_000:
            period = "Seleucid (300-100 BCE)"
            confidence = "low"
        elif has_pythagorean and has_reciprocal:
            period = "Old Babylonian (1900-1600 BCE)"
            confidence = "medium"
        elif has_reciprocal:
            period = "Old Babylonian (1900-1600 BCE)"
            confidence = "medium"
        else:
            period = "uncertain"
            confidence = "low"

        return {
            "estimated_period": period,
            "confidence": confidence,
            "max_value": max_val,
            "num_relationships": len(rels),
            "has_pythagorean": has_pythagorean,
            "has_reciprocal_pairs": has_reciprocal,
        }


def _isqrt_frac(f: Fraction) -> Fraction | None:
    """Integer-style sqrt for a Fraction. Returns None if not perfect square."""
    if f < 0:
        return None
    num = f.numerator
    den = f.denominator
    sn = _isqrt(num)
    sd = _isqrt(den)
    if sn is not None and sd is not None:
        return Fraction(sn, sd)
    return None


def _isqrt(n: int) -> int | None:
    """Integer square root if perfect square, else None."""
    if n < 0:
        return None
    if n == 0:
        return 0
    x = n
    y = (x + 1) // 2
    while y < x:
        x = y
        y = (x + n // x) // 2
    return x if x * x == n else None
