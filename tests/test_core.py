"""Tests for the core layer: Sexa, SexaRational, SmoothNumber."""

import pytest
from fractions import Fraction

from cuneiform.core.sexagesimal import Sexa, IrregularError
from cuneiform.core.rational import SexaRational
from cuneiform.core.smooth import (
    SmoothNumber,
    is_smooth,
    smooth_exponents,
    extract_smooth_part,
    generate_smooth_numbers,
    smooth_in_range,
    near_smooth,
)


# ============================================================
# SmoothNumber tests
# ============================================================

class TestIsSmooth:
    def test_powers_of_2(self):
        for n in [1, 2, 4, 8, 16, 32, 64, 1024]:
            assert is_smooth(n), f"{n} should be smooth"

    def test_powers_of_3(self):
        for n in [1, 3, 9, 27, 81, 243]:
            assert is_smooth(n), f"{n} should be smooth"

    def test_powers_of_5(self):
        for n in [1, 5, 25, 125, 625]:
            assert is_smooth(n), f"{n} should be smooth"

    def test_mixed_smooth(self):
        # 60 = 2^2 * 3 * 5
        assert is_smooth(60)
        # 3600 = 60^2
        assert is_smooth(3600)
        # 360 = 2^3 * 3^2 * 5
        assert is_smooth(360)

    def test_primes_above_5(self):
        for p in [7, 11, 13, 17, 19, 23, 29, 31]:
            assert not is_smooth(p), f"{p} should not be smooth"

    def test_composites_with_large_factors(self):
        assert not is_smooth(14)   # 2 * 7
        assert not is_smooth(21)   # 3 * 7
        assert not is_smooth(35)   # 5 * 7

    def test_one(self):
        assert is_smooth(1)


class TestSmoothExponents:
    def test_basic(self):
        assert smooth_exponents(1) == (0, 0, 0)
        assert smooth_exponents(2) == (1, 0, 0)
        assert smooth_exponents(3) == (0, 1, 0)
        assert smooth_exponents(5) == (0, 0, 1)
        assert smooth_exponents(60) == (2, 1, 1)
        assert smooth_exponents(3600) == (4, 2, 2)

    def test_non_smooth_returns_none(self):
        assert smooth_exponents(7) is None
        assert smooth_exponents(14) is None


class TestExtractSmoothPart:
    def test_smooth_number(self):
        assert extract_smooth_part(60) == (60, 1)

    def test_non_smooth(self):
        assert extract_smooth_part(7) == (1, 7)
        assert extract_smooth_part(14) == (2, 7)
        assert extract_smooth_part(21) == (3, 7)

    def test_mixed(self):
        # 420 = 2^2 * 3 * 5 * 7
        smooth, cofactor = extract_smooth_part(420)
        assert smooth == 60
        assert cofactor == 7


class TestSmoothNumber:
    def test_creation(self):
        s = SmoothNumber(2, 1, 1)
        assert s.value == 60
        assert s.exponents == (2, 1, 1)

    def test_from_int(self):
        s = SmoothNumber.from_int(60)
        assert s.a == 2
        assert s.b == 1
        assert s.c == 1

    def test_from_int_non_smooth(self):
        with pytest.raises(ValueError):
            SmoothNumber.from_int(7)

    def test_reciprocal_pair(self):
        # 12 = 2^2 * 3, reciprocal w.r.t. 60^2 = 3600
        s = SmoothNumber.from_int(12)
        r = s.reciprocal_pair(power=2)
        assert s.value * r.value == 3600

    def test_multiply(self):
        a = SmoothNumber(1, 0, 0)  # 2
        b = SmoothNumber(0, 1, 0)  # 3
        c = a * b
        assert c.value == 6

    def test_comparison(self):
        assert SmoothNumber.from_int(2) < SmoothNumber.from_int(3)


class TestGenerateSmoothNumbers:
    def test_up_to_60(self):
        result = generate_smooth_numbers(60)
        values = [s.value for s in result]
        expected = [1, 2, 3, 4, 5, 6, 8, 9, 10, 12, 15, 16, 18, 20, 24, 25,
                    27, 30, 32, 36, 40, 45, 48, 50, 54, 60]
        assert values == expected

    def test_count_up_to_1000(self):
        result = generate_smooth_numbers(1000)
        # Known: there are 86 5-smooth numbers up to 1000
        assert len(result) == 86


# ============================================================
# SexaRational tests
# ============================================================

class TestSexaRational:
    def test_creation(self):
        r = SexaRational(1, 2)
        assert r.as_fraction == Fraction(1, 2)

    def test_regularity(self):
        assert SexaRational(1, 2).is_regular
        assert SexaRational(1, 3).is_regular
        assert SexaRational(1, 5).is_regular
        assert SexaRational(1, 60).is_regular
        assert not SexaRational(1, 7).is_regular
        assert not SexaRational(1, 11).is_regular

    def test_regularity_class(self):
        assert SexaRational(1, 1).regularity_class == 1
        assert SexaRational(1, 2).regularity_class == 2
        assert SexaRational(1, 3).regularity_class == 3
        assert SexaRational(1, 7).regularity_class == 7
        assert SexaRational(1, 91).regularity_class == 13  # 91 = 7 * 13

    def test_smooth_order(self):
        r = SexaRational(1, 60)  # 60 = 2^2 * 3 * 5
        assert r.smooth_order == (2, 1, 1)

    def test_smooth_order_irregular_raises(self):
        with pytest.raises(ValueError):
            SexaRational(1, 7).smooth_order

    def test_arithmetic(self):
        a = SexaRational(1, 3)
        b = SexaRational(1, 2)
        assert a + b == SexaRational(5, 6)
        assert a - b == SexaRational(-1, 6)
        assert a * b == SexaRational(1, 6)
        assert a / b == SexaRational(2, 3)

    def test_power(self):
        r = SexaRational(2, 3)
        assert r ** 2 == SexaRational(4, 9)

    def test_comparison(self):
        assert SexaRational(1, 3) < SexaRational(1, 2)
        assert SexaRational(1, 2) == SexaRational(2, 4)

    def test_negation(self):
        r = SexaRational(3, 4)
        assert (-r).as_fraction == Fraction(-3, 4)

    def test_int_arithmetic(self):
        r = SexaRational(1, 3)
        assert r + 1 == SexaRational(4, 3)
        assert r * 3 == SexaRational(1)
        assert 1 - r == SexaRational(2, 3)


# ============================================================
# Sexa tests
# ============================================================

class TestSexaCreation:
    def test_from_int(self):
        s = Sexa(90)  # 1*60 + 30 = 1;30
        assert s.as_fraction == Fraction(90)
        assert repr(s) == "1,30"

    def test_from_fraction(self):
        s = Sexa.from_fraction(1, 2)  # 0;30
        assert repr(s) == "0;30"

    def test_from_fraction_irregular_raises(self):
        with pytest.raises(IrregularError):
            Sexa.from_fraction(1, 7)

    def test_from_notation_integer(self):
        s = Sexa("1,30")
        assert s.as_fraction == Fraction(90)

    def test_from_notation_fractional(self):
        s = Sexa("0;30")
        assert s.as_fraction == Fraction(1, 2)

    def test_from_notation_mixed(self):
        s = Sexa("1;30")
        assert s.as_fraction == Fraction(3, 2)  # 1 + 30/60 = 1.5

    def test_from_notation_deep_fraction(self):
        # 0;0,44,26,40 = 44/3600 + 26/216000 + 40/12960000
        # This is 1/81 = 0;0,44,26,40 in base 60
        s = Sexa("0;0,44,26,40")
        assert s.as_fraction == Fraction(1, 81)


class TestSexaArithmetic:
    def test_addition(self):
        a = Sexa("0;30")  # 1/2
        b = Sexa("0;20")  # 1/3
        c = a + b
        assert c.as_fraction == Fraction(5, 6)

    def test_subtraction(self):
        a = Sexa("1")
        b = Sexa("0;30")
        assert (a - b).as_fraction == Fraction(1, 2)

    def test_multiplication(self):
        a = Sexa("0;30")  # 1/2
        b = Sexa("0;20")  # 1/3
        c = a * b
        assert c.as_fraction == Fraction(1, 6)

    def test_division(self):
        a = Sexa(3)
        b = Sexa(2)
        assert (a / b).as_fraction == Fraction(3, 2)

    def test_power(self):
        a = Sexa("0;30")  # 1/2
        assert (a ** 2).as_fraction == Fraction(1, 4)

    def test_int_arithmetic(self):
        a = Sexa("0;30")
        assert (a + 1).as_fraction == Fraction(3, 2)
        assert (2 * a).as_fraction == Fraction(1)


class TestSexaProperties:
    def test_is_regular(self):
        assert Sexa.from_fraction(1, 2).is_regular
        assert Sexa.from_fraction(1, 3).is_regular
        assert Sexa(1).is_regular
        # Sexa from division can be irregular
        s = Sexa._from_frac(Fraction(1, 7))
        assert not s.is_regular

    def test_reciprocal(self):
        s = Sexa(2)
        r = s.reciprocal
        assert r.as_fraction == Fraction(1, 2)
        assert repr(r) == "0;30"

    def test_reciprocal_irregular_raises(self):
        s = Sexa(7)
        with pytest.raises(IrregularError):
            s.reciprocal

    def test_digits(self):
        s = Sexa("1;30,15")
        int_d, frac_d, neg = s.digits()
        assert int_d == [1]
        assert frac_d == [30, 15]
        assert neg is False

    def test_digits_negative(self):
        s = -Sexa("1;30")
        int_d, frac_d, neg = s.digits()
        assert neg is True


class TestSexaDisplay:
    def test_repr_integer(self):
        assert repr(Sexa(0)) == "0"
        assert repr(Sexa(1)) == "1"
        assert repr(Sexa(59)) == "59"
        assert repr(Sexa(60)) == "1,0"
        assert repr(Sexa(61)) == "1,1"
        assert repr(Sexa(3600)) == "1,0,0"

    def test_repr_fraction(self):
        assert repr(Sexa.from_fraction(1, 2)) == "0;30"
        assert repr(Sexa.from_fraction(1, 3)) == "0;20"
        assert repr(Sexa.from_fraction(1, 4)) == "0;15"
        assert repr(Sexa.from_fraction(1, 5)) == "0;12"
        assert repr(Sexa.from_fraction(1, 6)) == "0;10"

    def test_cuneiform_output(self):
        s = Sexa(1)
        c = s.cuneiform()
        assert len(c) > 0  # Just verify it produces output


class TestSexaKnownBabylonianValues:
    """Test against values known from OB tablets."""

    def test_reciprocal_of_2(self):
        # 1/2 = 0;30
        assert repr(Sexa.from_fraction(1, 2)) == "0;30"

    def test_reciprocal_of_3(self):
        # 1/3 = 0;20
        assert repr(Sexa.from_fraction(1, 3)) == "0;20"

    def test_reciprocal_of_4(self):
        # 1/4 = 0;15
        assert repr(Sexa.from_fraction(1, 4)) == "0;15"

    def test_reciprocal_of_5(self):
        # 1/5 = 0;12
        assert repr(Sexa.from_fraction(1, 5)) == "0;12"

    def test_reciprocal_of_6(self):
        # 1/6 = 0;10
        assert repr(Sexa.from_fraction(1, 6)) == "0;10"

    def test_reciprocal_of_8(self):
        # 1/8 = 0;7,30
        assert repr(Sexa.from_fraction(1, 8)) == "0;7,30"

    def test_reciprocal_of_9(self):
        # 1/9 = 0;6,40
        assert repr(Sexa.from_fraction(1, 9)) == "0;6,40"

    def test_reciprocal_of_10(self):
        # 1/10 = 0;6
        assert repr(Sexa.from_fraction(1, 10)) == "0;6"

    def test_reciprocal_of_12(self):
        # 1/12 = 0;5
        assert repr(Sexa.from_fraction(1, 12)) == "0;5"

    def test_reciprocal_of_15(self):
        # 1/15 = 0;4
        assert repr(Sexa.from_fraction(1, 15)) == "0;4"

    def test_reciprocal_of_16(self):
        # 1/16 = 0;3,45
        assert repr(Sexa.from_fraction(1, 16)) == "0;3,45"

    def test_reciprocal_of_18(self):
        # 1/18 = 0;3,20
        assert repr(Sexa.from_fraction(1, 18)) == "0;3,20"

    def test_reciprocal_of_20(self):
        # 1/20 = 0;3
        assert repr(Sexa.from_fraction(1, 20)) == "0;3"

    def test_reciprocal_of_24(self):
        # 1/24 = 0;2,30
        assert repr(Sexa.from_fraction(1, 24)) == "0;2,30"

    def test_reciprocal_of_25(self):
        # 1/25 = 0;2,24
        assert repr(Sexa.from_fraction(1, 25)) == "0;2,24"

    def test_reciprocal_of_27(self):
        # 1/27 = 0;2,13,20
        assert repr(Sexa.from_fraction(1, 27)) == "0;2,13,20"

    def test_reciprocal_of_30(self):
        # 1/30 = 0;2
        assert repr(Sexa.from_fraction(1, 30)) == "0;2"

    def test_reciprocal_of_32(self):
        # 1/32 = 0;1,52,30
        assert repr(Sexa.from_fraction(1, 32)) == "0;1,52,30"

    def test_reciprocal_of_36(self):
        # 1/36 = 0;1,40
        assert repr(Sexa.from_fraction(1, 36)) == "0;1,40"

    def test_reciprocal_of_40(self):
        # 1/40 = 0;1,30
        assert repr(Sexa.from_fraction(1, 40)) == "0;1,30"

    def test_reciprocal_of_45(self):
        # 1/45 = 0;1,20
        assert repr(Sexa.from_fraction(1, 45)) == "0;1,20"

    def test_reciprocal_of_48(self):
        # 1/48 = 0;1,15
        assert repr(Sexa.from_fraction(1, 48)) == "0;1,15"

    def test_reciprocal_of_50(self):
        # 1/50 = 0;1,12
        assert repr(Sexa.from_fraction(1, 50)) == "0;1,12"

    def test_reciprocal_of_54(self):
        # 1/54 = 0;1,6,40
        assert repr(Sexa.from_fraction(1, 54)) == "0;1,6,40"

    def test_reciprocal_of_60(self):
        # 1/60 = 0;1
        assert repr(Sexa.from_fraction(1, 60)) == "0;1"

    def test_reciprocal_of_64(self):
        # 1/64 = 0;0,56,15
        assert repr(Sexa.from_fraction(1, 64)) == "0;0,56,15"

    def test_reciprocal_of_81(self):
        # 1/81 = 0;0,44,26,40
        assert repr(Sexa.from_fraction(1, 81)) == "0;0,44,26,40"

    def test_reciprocal_roundtrip(self):
        """n * (1/n) should always give exactly 1 for regular n."""
        regular_numbers = [2, 3, 4, 5, 6, 8, 9, 10, 12, 15, 16, 18, 20,
                          24, 25, 27, 30, 32, 36, 40, 45, 48, 50, 54, 60]
        for n in regular_numbers:
            s = Sexa(n)
            r = s.reciprocal
            product = s * r
            assert product == 1, f"{n} * (1/{n}) should be 1, got {product}"


class TestSexaNotationRoundtrip:
    """Test that notation parsing and display are consistent."""

    def test_integer_roundtrip(self):
        for n in [0, 1, 59, 60, 61, 119, 3599, 3600, 3661]:
            s = Sexa(n)
            s2 = Sexa(repr(s))
            assert s == s2, f"Roundtrip failed for {n}: {repr(s)} -> {s2}"

    def test_fraction_roundtrip(self):
        fractions = [
            (1, 2), (1, 3), (1, 4), (1, 5), (1, 6),
            (1, 8), (1, 9), (1, 10), (1, 12), (1, 15),
            (1, 60), (1, 81), (7, 12), (5, 8),
        ]
        for num, den in fractions:
            s = Sexa.from_fraction(num, den)
            s2 = Sexa(repr(s))
            assert s == s2, f"Roundtrip failed for {num}/{den}: {repr(s)} -> {s2}"
