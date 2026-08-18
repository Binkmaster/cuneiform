"""Tests for ideas/taylor_series.py — Taylor series in sexagesimal cuneiform."""

import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cuneiform.core.smooth import is_smooth
from ideas.taylor_series import (
    arctan_coeffs,
    basel_partial_sums,
    cos_coeffs,
    cuneiform_str,
    exp_coeffs,
    factorial,
    ln1p_coeffs,
    pi_squared_over_six,
    regular_label,
    sexa_str,
    sin_coeffs,
)


# ---------------------------------------------------------------------------
# Coefficient generators
# ---------------------------------------------------------------------------

class TestCoefficients:
    def test_exp_coeffs(self):
        assert exp_coeffs(5) == [Fraction(1), Fraction(1), Fraction(1, 2),
                                 Fraction(1, 6), Fraction(1, 24)]

    def test_sin_coeffs_signs_and_powers(self):
        pairs = sin_coeffs(3)
        assert pairs == [(1, Fraction(1)),
                         (3, Fraction(-1, 6)),
                         (5, Fraction(1, 120))]

    def test_cos_coeffs_signs_and_powers(self):
        pairs = cos_coeffs(3)
        assert pairs == [(0, Fraction(1)),
                         (2, Fraction(-1, 2)),
                         (4, Fraction(1, 24))]

    def test_ln1p_coeffs_alternate(self):
        pairs = ln1p_coeffs(4)
        assert pairs == [(1, Fraction(1)), (2, Fraction(-1, 2)),
                         (3, Fraction(1, 3)), (4, Fraction(-1, 4))]

    def test_arctan_coeffs(self):
        pairs = arctan_coeffs(3)
        assert pairs == [(1, Fraction(1)), (3, Fraction(-1, 3)),
                         (5, Fraction(1, 5))]

    def test_factorial(self):
        assert factorial(0) == 1
        assert factorial(6) == 720
        assert factorial(7) == 5040


# ---------------------------------------------------------------------------
# The regularity boundary: 1/k! terminates in base 60 iff k <= 6
# ---------------------------------------------------------------------------

class TestFactorialRegularity:
    def test_factorials_regular_through_six(self):
        for k in range(7):
            assert is_smooth(factorial(k)), f"{k}! should be 5-smooth"

    def test_factorials_irregular_from_seven(self):
        for k in range(7, 15):
            assert not is_smooth(factorial(k)), f"{k}! should not be 5-smooth"

    def test_regular_label(self):
        assert regular_label(Fraction(1, 720)) == "REGULAR"
        assert regular_label(Fraction(1, 5040)) == "irregular"


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

class TestRendering:
    def test_terminating_shows_all_digits(self):
        assert sexa_str(Fraction(1, 2)) == "0;30"
        assert sexa_str(Fraction(1, 720)) == "0;0,5"
        assert sexa_str(Fraction(3, 2)) == "1;30"

    def test_integer_has_no_fractional_part(self):
        assert sexa_str(Fraction(2)) == "2"
        assert ";" not in cuneiform_str(Fraction(2))

    def test_negative(self):
        assert sexa_str(Fraction(-1, 6)) == "-0;10"
        assert cuneiform_str(Fraction(-1, 6)).startswith("-")

    def test_nonterminating_is_marked(self):
        s = sexa_str(Fraction(1, 7), frac_places=4)
        assert s.endswith(",...")
        assert s == "0;8,34,17,8,..."
        assert cuneiform_str(Fraction(1, 7), frac_places=4).endswith("...")

    def test_terminating_never_marked(self):
        assert "..." not in sexa_str(Fraction(1, 120))
        assert "..." not in cuneiform_str(Fraction(1, 120))

    def test_cuneiform_uses_cuneiform_block(self):
        # 1/2 = 0;30 → placeholder + thirty wedge
        assert cuneiform_str(Fraction(1, 2)) == "\U0001243F ; \U0001243A"


# ---------------------------------------------------------------------------
# Partial sums of e
# ---------------------------------------------------------------------------

class TestPartialSums:
    def test_seven_term_sum_is_last_regular(self):
        total = Fraction(0)
        for k in range(7):
            total += Fraction(1, factorial(k))
        assert total == Fraction(1957, 720)
        assert is_smooth(total.denominator)
        assert sexa_str(total) == "2;43,5"

        total += Fraction(1, factorial(7))
        assert not is_smooth(total.denominator)

    def test_seven_term_error_below_one_over_3600(self):
        # e - 2;43,5 < 1/60^2: the tail 1/7! + 1/8! + ... is bounded by the
        # geometric series (1/7!)(1 + 1/8 + 1/8^2 + ...) = (1/7!)(8/7) = 1/4410
        tail_bound = Fraction(8, 7 * factorial(7))
        assert tail_bound == Fraction(1, 4410)
        assert tail_bound < Fraction(1, 3600)


# ---------------------------------------------------------------------------
# The Basel problem: sum 1/n^2 = pi^2/6
# ---------------------------------------------------------------------------

class TestBasel:
    def test_partial_sums_exact(self):
        sums = basel_partial_sums(6)
        assert sums[0] == Fraction(1)
        assert sums[1] == Fraction(5, 4)
        assert sums[3] == Fraction(205, 144)
        assert sums[5] == Fraction(5369, 3600)

    def test_sums_regular_exactly_through_six(self):
        sums = basel_partial_sums(12)
        for k, s in enumerate(sums, start=1):
            assert is_smooth(s.denominator) == (k <= 6)

    def test_s6_is_two_sexagesimal_digits(self):
        s6 = basel_partial_sums(6)[-1]
        assert sexa_str(s6) == "1;29,29"

    def test_pi_squared_over_six_value(self):
        target = pi_squared_over_six()
        # pi^2/6 = 1.6449340668...; check to 10 decimal places
        assert abs(target - Fraction("1.6449340668")) < Fraction(1, 10**9)
        assert sexa_str(target, 4) == "1;38,41,45,45,..."

    def test_terms_regular_iff_n_smooth(self):
        for n in [1, 2, 3, 4, 5, 6, 8, 9, 10, 12, 15, 16]:
            assert is_smooth(Fraction(1, n * n).denominator)
        for n in [7, 11, 13, 14, 21, 22]:
            assert not is_smooth(Fraction(1, n * n).denominator)


# ---------------------------------------------------------------------------
# CAS integration: degree-6 Taylor polynomial of e^x
# ---------------------------------------------------------------------------

class TestCASIntegration:
    def test_taylor_polynomial_matches_partial_sum(self):
        from cuneiform.cas.ratcalculus import RationalTaylorSeries

        series = RationalTaylorSeries([1] * 7, center=0)
        value = series.evaluate(1)
        assert Fraction(value.numerator, value.denominator) == Fraction(1957, 720)

    def test_taylor_at_regular_point_is_regular(self):
        from cuneiform.cas.ratcalculus import RationalTaylorSeries

        series = RationalTaylorSeries([1] * 7, center=0)
        value = series.evaluate(Fraction(3, 2))
        f = Fraction(value.numerator, value.denominator)
        # Regular input through regular coefficients stays regular
        assert is_smooth(f.denominator)
        assert sexa_str(f) == "4;28,39,8,26,15"
