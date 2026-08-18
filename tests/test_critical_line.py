"""Tests for the critical-line proportion bound history."""

from fractions import Fraction

from primes.reimann.critical_line import (
    BOUND_HISTORY,
    CLAUDE_2026,
    improvement,
    quantified_bounds,
    remaining_gap,
)


class TestBoundHistory:
    def test_chronological_order(self):
        years = [b.year for b in BOUND_HISTORY]
        assert years == sorted(years)

    def test_bounds_strictly_increase(self):
        props = [b.proportion for b in quantified_bounds()]
        assert all(a < b for a, b in zip(props, props[1:]))

    def test_claude_2026_value(self):
        latest = BOUND_HISTORY[-1]
        assert latest.year == 2026
        assert latest.proportion == Fraction(269, 400) == CLAUDE_2026
        assert float(latest.proportion) == 0.6725

    def test_previous_record_was_5_12(self):
        assert quantified_bounds()[-2].proportion == Fraction(5, 12)

    def test_all_bounds_below_rh(self):
        assert all(b.proportion < 1 for b in quantified_bounds())


class TestSexagesimal:
    def test_all_quantified_bounds_are_regular(self):
        for b in quantified_bounds():
            assert b.is_regular, f"{b.proportion} should terminate in base 60"

    def test_expansions(self):
        expected = {
            Fraction(1, 3): "0;20",
            Fraction(2, 5): "0;24",
            Fraction(5, 12): "0;25",
            Fraction(269, 400): "0;40,21",
        }
        for b in quantified_bounds():
            assert str(b.sexa) == expected[b.proportion]

    def test_unquantified_bounds_have_no_sexa(self):
        for b in BOUND_HISTORY:
            if b.proportion is None:
                assert b.sexa is None
                assert not b.is_regular


class TestArithmetic:
    def test_2026_jump(self):
        prev, latest = quantified_bounds()[-2:]
        assert improvement(prev, latest) == Fraction(307, 1200)

    def test_remaining_gap(self):
        assert remaining_gap(BOUND_HISTORY[-1]) == Fraction(131, 400)

    def test_jump_dwarfs_prior_jumps(self):
        qb = quantified_bounds()
        jumps = [improvement(a, b) for a, b in zip(qb, qb[1:])]
        assert jumps[-1] > sum(jumps[:-1])
