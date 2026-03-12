"""Tests for Plimpton 322 tablet reproduction.

Verified against published values from:
  - Neugebauer & Sachs, "Mathematical Cuneiform Texts" (1945)
  - Robson, "Neither Sherlock Holmes nor Babylon" (2001), Table 1
  - Mansfield & Wildberger (2017), Table 3
"""

import pytest
from fractions import Fraction

from cuneiform.core.sexagesimal import Sexa
from cuneiform.tablet.plimpton322 import Plimpton322, PlimptonRow


@pytest.fixture
def tablet():
    return Plimpton322()


@pytest.fixture
def original_rows(tablet):
    return tablet.original()


class TestOriginal15Rows:
    """Verify the 15 rows match published values exactly."""

    def test_row_count(self, original_rows):
        assert len(original_rows) == 15

    def test_all_pythagorean(self, original_rows):
        """Every row must satisfy w² + l² = d²."""
        for row in original_rows:
            w, l, d = row.triple
            assert w * w + l * l == d * d, (
                f"Row {row.row_number}: {w}² + {l}² = {w*w + l*l} ≠ {d}² = {d*d}"
            )

    def test_primitivity(self, original_rows):
        """All original 15 triples are primitive except row 15.
        Row 15 (p=9,q=5, both odd) gives triple (56,90,106) with gcd=2."""
        for row in original_rows:
            if row.row_number == 15:
                assert not row.is_primitive, "Row 15 should NOT be primitive"
            else:
                assert row.is_primitive, f"Row {row.row_number} should be primitive"

    # Published triples from Neugebauer & Sachs / Robson / Mansfield & Wildberger
    # Format: (row, p, q, width, length, diagonal)
    KNOWN_VALUES = [
        (1,  12,  5,   119,   120,   169),
        (2,  64,  27,  3367,  3456,  4825),    # tablet has width error
        (3,  75,  32,  4601,  4800,  6649),
        (4,  125, 54,  12709, 13500, 18541),
        (5,  9,   4,   65,    72,    97),
        (6,  20,  9,   319,   360,   481),
        (7,  54,  25,  2291,  2700,  3541),
        (8,  32,  15,  799,   960,   1249),
        (9,  25,  12,  481,   600,   769),      # tablet has width error
        (10, 81,  40,  4961,  6480,  8161),
        (11, 2,   1,   3,     4,     5),
        (12, 48,  25,  1679,  2400,  2929),
        (13, 15,  8,   161,   240,   289),      # tablet has width error
        (14, 50,  27,  1771,  2700,  3229),
        (15, 9,   5,   56,    90,    106),       # tablet has diagonal error
    ]

    @pytest.mark.parametrize(
        "row_num, p, q, width, length, diagonal", KNOWN_VALUES
    )
    def test_known_values(self, original_rows, row_num, p, q,
                          width, length, diagonal):
        row = original_rows[row_num - 1]
        assert row.row_number == row_num
        assert row.p == p, f"Row {row_num}: p"
        assert row.q == q, f"Row {row_num}: q"
        assert row.width == width, f"Row {row_num}: width"
        assert row.length == length, f"Row {row_num}: length"
        assert row.diagonal == diagonal, f"Row {row_num}: diagonal"

    def test_row_15_not_primitive(self, original_rows):
        """Row 15 triple (56, 90, 106) has gcd=2, so it's not primitive.
        Wait -- let's check: gcd(56, 90) = 2, gcd(2, 106) = 2.
        The primitive triple is (28, 45, 53). Row 15 uses p=9, q=5
        which gives 56, 90, 106 -- this is 2× the primitive (28,45,53).
        Actually p=9, q=5: gcd(9,5)=1, but both are odd, so the triple
        is 2× a primitive. Let's just verify the math is correct."""
        row = original_rows[14]
        assert row.p == 9
        assert row.q == 5
        # Both odd, so triple is not primitive (has factor of 2)
        w, l, d = row.triple
        assert w == 56 and l == 90 and d == 106
        # The triple is still Pythagorean
        assert w * w + l * l == d * d


class TestScribalErrors:
    """Verify scribal error annotations match published scholarship."""

    def test_error_count(self, original_rows):
        errors = [r for r in original_rows if r.has_scribal_error]
        assert len(errors) == 4

    def test_row2_column_i_error(self, original_rows):
        """Row 2 has a computational error in Column I (d/l²), not in width."""
        row = original_rows[1]  # row 2
        assert row.tablet_col1_error is True
        assert row.tablet_width is None  # width is correct
        assert row.width == 3367  # p=64,q=27: 64²-27² = 3367
        assert row.has_scribal_error

    def test_row9_width_error(self, original_rows):
        row = original_rows[8]  # row 9
        assert row.tablet_width == 541
        assert row.width == 481
        # Tablet reads 9,01 (= 541), correct is 8,01 (= 481)
        assert repr(Sexa(541)) == "9,1"
        assert repr(Sexa(481)) == "8,1"

    def test_row13_width_error(self, original_rows):
        row = original_rows[12]  # row 13
        assert row.tablet_width == 25921
        assert row.width == 161
        # Tablet reads 7,12,01 (= 7*3600 + 12*60 + 1 = 25921)
        assert repr(Sexa(25921)) == "7,12,1"
        # Correct is 2,41 (= 2*60 + 41 = 161)
        assert repr(Sexa(161)) == "2,41"

    def test_row15_diagonal_error(self, original_rows):
        row = original_rows[14]  # row 15
        assert row.tablet_diagonal == 53
        assert row.diagonal == 106
        # Tablet reads 53, correct is 1,46 (= 106)
        assert repr(Sexa(53)) == "53"
        assert repr(Sexa(106)) == "1,46"


class TestColumnI:
    """Verify Column I values: (d/l)² in sexagesimal."""

    # Published Column I values from Mansfield & Wildberger 2017
    # These are (d/l)² as sexagesimal strings
    COLUMN_I_SEXA = [
        (1,  "1;59,0,15"),
        (2,  "1;56,56,58,14,50,6,15"),
        (3,  "1;55,7,41,15,33,45"),
        (4,  "1;53,10,29,32,52,16"),
        (5,  "1;48,54,1,40"),
        (6,  "1;47,6,41,40"),
        (7,  "1;43,11,56,28,26,40"),
        (8,  "1;41,33,45,14,3,45"),
        (9,  "1;38,33,36,36"),
        (10, "1;35,10,2,28,27,24,26,40"),
        (11, "1;33,45"),
        (12, "1;29,21,54,2,15"),
        (13, "1;27,0,3,45"),
        (14, "1;25,48,51,35,6,40"),
        (15, "1;23,13,46,40"),
    ]

    @pytest.mark.parametrize("row_num, expected_sexa", COLUMN_I_SEXA)
    def test_column_i_values(self, original_rows, row_num, expected_sexa):
        row = original_rows[row_num - 1]
        computed = Sexa(row.d_over_l_sq)
        expected = Sexa(expected_sexa)
        assert computed == expected, (
            f"Row {row_num}: (d/l)² = {computed!r}, expected {expected_sexa}"
        )

    def test_column_i_all_greater_than_1(self, original_rows):
        """All (d/l)² values should be > 1 (since d > l)."""
        for row in original_rows:
            assert row.d_over_l_sq > 1

    def test_column_i_descending(self, original_rows):
        """Rows should be sorted by decreasing (d/l)²."""
        for i in range(len(original_rows) - 1):
            assert original_rows[i].d_over_l_sq >= original_rows[i + 1].d_over_l_sq, (
                f"Row {i+1} to {i+2}: not descending"
            )


class TestSpreads:
    """Verify spread values (the rational trig interpretation)."""

    def test_spreads_in_range(self, original_rows):
        """All spreads should be in (0, 1)."""
        for row in original_rows:
            s = row.spread_width
            assert 0 < s < 1, f"Row {row.row_number}: spread = {float(s)}"

    def test_spreads_decreasing(self, original_rows):
        """Spreads should decrease with row number (tablet ordering)."""
        for i in range(len(original_rows) - 1):
            s1 = original_rows[i].spread_width
            s2 = original_rows[i + 1].spread_width
            assert s1 >= s2, (
                f"Row {i+1} → {i+2}: spread not decreasing "
                f"({float(s1):.6f} vs {float(s2):.6f})"
            )

    def test_row_11_is_3_4_5(self, original_rows):
        """Row 11 is the (3,4,5) triple. Spread at width = 9/25."""
        row = original_rows[10]
        assert row.triple == (3, 4, 5)
        assert row.spread_width == Fraction(9, 25)

    def test_spread_width_plus_length_less_than_1(self, original_rows):
        """For any right triangle: s_width + s_length = 1
        (since sin²A + cos²A = 1, and the third spread is 1)."""
        for row in original_rows:
            total = row.spread_width + row.spread_length
            assert total == Fraction(1), (
                f"Row {row.row_number}: spreads sum to {total}, not 1"
            )


class TestGeneratingPairs:
    """Verify properties of the generating pairs (p, q)."""

    def test_p_greater_than_q(self, original_rows):
        for row in original_rows:
            assert row.p > row.q > 0

    def test_gcd_is_1(self, original_rows):
        from math import gcd
        for row in original_rows:
            assert gcd(row.p, row.q) == 1, (
                f"Row {row.row_number}: gcd({row.p}, {row.q}) ≠ 1"
            )

    def test_p_and_q_are_regular(self, original_rows):
        from cuneiform.core.smooth import is_smooth
        for row in original_rows:
            assert is_smooth(row.p), f"Row {row.row_number}: p={row.p} not regular"
            assert is_smooth(row.q), f"Row {row.row_number}: q={row.q} not regular"

    def test_p_bounded_by_125(self, original_rows):
        """Original tablet uses p ≤ 125 (= 2,05 in base 60)."""
        for row in original_rows:
            assert row.p <= 125


class TestExtendedTable:
    """Tests for the extended table generator."""

    def test_extended_at_125_contains_original(self, tablet, original_rows):
        """Extended table at bound=125 should contain all 15 original triples."""
        extended = tablet.extended(max_regular=125)
        original_triples = {r.triple for r in original_rows}
        extended_triples = {r.triple for r in extended}

        # The original triples should all appear (except row 15 which
        # isn't primitive due to both p,q being odd)
        for r in original_rows:
            if r.p % 2 == 1 and r.q % 2 == 1:
                continue  # skip non-primitive generating pairs
            assert r.triple in extended_triples, (
                f"Row {r.row_number} triple {r.triple} missing from extended"
            )

    def test_extended_all_pythagorean(self, tablet):
        extended = tablet.extended(max_regular=250)
        for row in extended:
            w, l, d = row.triple
            assert w * w + l * l == d * d

    def test_extended_sorted_descending(self, tablet):
        extended = tablet.extended(max_regular=250)
        for i in range(len(extended) - 1):
            assert extended[i].d_over_l_sq >= extended[i + 1].d_over_l_sq

    def test_extended_grows_with_bound(self, tablet):
        n125 = len(tablet.extended(max_regular=125))
        n250 = len(tablet.extended(max_regular=250))
        n500 = len(tablet.extended(max_regular=500))
        assert n125 < n250 < n500

    def test_extended_all_regular_generators(self, tablet):
        from cuneiform.core.smooth import is_smooth
        for row in tablet.extended(max_regular=250):
            assert is_smooth(row.p), f"p={row.p} not regular"
            assert is_smooth(row.q), f"q={row.q} not regular"


class TestCoverageReport:
    """Tests for coverage analysis."""

    def test_original_coverage(self, tablet):
        report = tablet.coverage_report()
        assert report["num_rows"] == 15
        assert report["max_gap"] > 0
        assert report["avg_gap"] > 0

    def test_larger_table_smaller_gaps(self, tablet):
        """Larger tables should have smaller max gaps."""
        r125 = tablet.coverage_report(tablet.extended(125))
        r500 = tablet.coverage_report(tablet.extended(500))
        assert r500["max_gap"] <= r125["max_gap"]
        assert r500["avg_gap"] <= r125["avg_gap"]


class TestDisplay:
    """Test display and export functions."""

    def test_format_table(self, tablet):
        output = tablet.format_table()
        assert "PLIMPTON 322" in output
        assert "scribal error" in output
        lines = output.strip().split("\n")
        # Header + 15 rows + blank + error header + 4 error annotations
        assert len(lines) >= 15 + 2

    def test_export_csv(self, tablet):
        csv = tablet.export_csv()
        lines = csv.strip().split("\n")
        assert len(lines) == 16  # header + 15 rows
        assert lines[0].startswith("row,")

    def test_format_row_shows_sexa(self, original_rows):
        row = original_rows[0]
        formatted = row.format_row(show_sexa=True)
        assert "1;59,0,15" in formatted  # Column I value for row 1


class TestSexagesimalDisplay:
    """Verify sexagesimal display of key tablet values."""

    def test_row1_width(self, original_rows):
        assert repr(original_rows[0].width_sexa()) == "1,59"

    def test_row1_diagonal(self, original_rows):
        assert repr(original_rows[0].diagonal_sexa()) == "2,49"

    def test_row11_is_simplest(self, original_rows):
        """Row 11 (3,4,5) should have the simplest display."""
        row = original_rows[10]
        assert repr(row.width_sexa()) == "3"
        assert repr(Sexa(row.length)) == "4"
        assert repr(row.diagonal_sexa()) == "5"
