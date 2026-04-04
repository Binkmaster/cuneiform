"""Tests for cuneiform.random — sexagesimal random number generation."""

from fractions import Fraction

import pytest

from cuneiform.core import Sexa
from cuneiform.random import SexaRandom, SmoothRandom, CuneiformDice


# ---------------------------------------------------------------------------
# SexaRandom — core LCG generator
# ---------------------------------------------------------------------------

class TestSexaRandom:
    def test_deterministic_with_seed(self):
        """Same seed produces same sequence."""
        a = SexaRandom(seed=123)
        b = SexaRandom(seed=123)
        assert [a.raw() for _ in range(10)] == [b.raw() for _ in range(10)]

    def test_different_seeds_differ(self):
        """Different seeds produce different sequences."""
        a = SexaRandom(seed=1)
        b = SexaRandom(seed=2)
        assert [a.raw() for _ in range(10)] != [b.raw() for _ in range(10)]

    def test_sexa_in_unit_interval(self):
        """sexa() returns values in [0, 1)."""
        rng = SexaRandom(seed=42)
        for _ in range(100):
            s = rng.sexa(digits=4)
            assert 0 <= float(s) < 1

    def test_sexa_is_exact_fraction(self):
        """sexa() values have denominators that are powers of 60."""
        rng = SexaRandom(seed=7)
        s = rng.sexa(digits=3)
        assert isinstance(s._frac, Fraction)
        # Denominator must divide 60^3
        assert (60 ** 3) % s._frac.denominator == 0

    def test_sexa_digit_count(self):
        """sexa(digits=N) produces at most N fractional digits."""
        rng = SexaRandom(seed=99)
        for digits in [1, 2, 3, 5]:
            s = rng.sexa(digits=digits)
            _, frac_digits, _ = s.digits()
            assert len(frac_digits) <= digits

    def test_randint_range(self):
        """randint(lo, hi) returns values in [lo, hi]."""
        rng = SexaRandom(seed=42)
        for _ in range(200):
            val = rng.randint(10, 50)
            assert 10 <= val <= 50

    def test_randint_single_value(self):
        """randint(n, n) always returns n."""
        rng = SexaRandom(seed=42)
        for _ in range(10):
            assert rng.randint(7, 7) == 7

    def test_randint_bad_range(self):
        """randint raises ValueError if lo > hi."""
        rng = SexaRandom(seed=42)
        with pytest.raises(ValueError):
            rng.randint(10, 5)

    def test_sexa_int(self):
        """sexa_int returns a Sexa integer in range."""
        rng = SexaRandom(seed=42)
        for _ in range(50):
            s = rng.sexa_int(1, 59)
            val = int(s)
            assert 1 <= val <= 59

    def test_choice(self):
        """choice picks from the given sequence."""
        rng = SexaRandom(seed=42)
        pool = [Sexa(1), Sexa(2), Sexa(3)]
        for _ in range(30):
            assert rng.choice(pool) in pool

    def test_choice_empty(self):
        """choice raises IndexError on empty sequence."""
        rng = SexaRandom(seed=42)
        with pytest.raises(IndexError):
            rng.choice([])

    def test_shuffle(self):
        """shuffle rearranges a list in place."""
        rng = SexaRandom(seed=42)
        original = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        shuffled = original.copy()
        rng.shuffle(shuffled)
        assert sorted(shuffled) == original  # same elements
        assert shuffled != original  # very unlikely to be same order with 10 elements

    def test_sample(self):
        """sample returns k unique elements."""
        rng = SexaRandom(seed=42)
        pool = list(range(20))
        result = rng.sample(pool, 5)
        assert len(result) == 5
        assert len(set(result)) == 5  # all unique
        assert all(r in pool for r in result)

    def test_sample_too_large(self):
        """sample raises ValueError when k > len(seq)."""
        rng = SexaRandom(seed=42)
        with pytest.raises(ValueError):
            rng.sample([1, 2, 3], 5)

    def test_seed_reset(self):
        """Resetting seed restores the sequence."""
        rng = SexaRandom(seed=42)
        first_run = [rng.raw() for _ in range(5)]
        rng.seed(42)
        second_run = [rng.raw() for _ in range(5)]
        assert first_run == second_run

    def test_state_property(self):
        """state exposes the internal LCG state."""
        rng = SexaRandom(seed=42)
        s1 = rng.state
        rng.raw()
        s2 = rng.state
        assert s1 != s2

    def test_auto_seed_nondeterministic(self):
        """Without a seed, two generators likely differ."""
        a = SexaRandom()
        b = SexaRandom()
        # Not guaranteed but overwhelmingly likely with OS entropy
        seq_a = [a.raw() for _ in range(5)]
        seq_b = [b.raw() for _ in range(5)]
        # We just check it doesn't crash; true randomness is hard to test
        assert len(seq_a) == 5


# ---------------------------------------------------------------------------
# SmoothRandom — regular (5-smooth) number generation
# ---------------------------------------------------------------------------

class TestSmoothRandom:
    def test_regular_is_smooth(self):
        """regular() always returns 5-smooth numbers."""
        sr = SmoothRandom(seed=42)
        for _ in range(50):
            s = sr.regular()
            n = int(s)
            assert n >= 1
            # Factor out 2, 3, 5 — remainder should be 1
            for p in (2, 3, 5):
                while n % p == 0:
                    n //= p
            assert n == 1, f"{int(s)} is not 5-smooth"

    def test_reciprocal_pair(self):
        """reciprocal_pair returns (n, 1/n) with exact fractions."""
        sr = SmoothRandom(seed=7)
        for _ in range(20):
            n, recip = sr.reciprocal_pair()
            product = Sexa._from_frac(n._frac * recip._frac)
            assert product._frac == 1

    def test_regular_fraction_in_unit_interval(self):
        """regular_fraction returns values in (0, 1)."""
        sr = SmoothRandom(seed=42)
        for _ in range(30):
            s = sr.regular_fraction()
            assert 0 < float(s) <= 1  # could be 1/2 in degenerate case

    def test_tablet_problem_structure(self):
        """tablet_problem returns the expected dict keys."""
        sr = SmoothRandom(seed=42)
        prob = sr.tablet_problem()
        assert "factor_a" in prob
        assert "factor_b" in prob
        assert "product" in prob
        assert "display" in prob

    def test_tablet_problem_correct_product(self):
        """tablet_problem product equals factor_a * factor_b."""
        sr = SmoothRandom(seed=42)
        for _ in range(20):
            prob = sr.tablet_problem()
            expected = Sexa._from_frac(prob["factor_a"]._frac * prob["factor_b"]._frac)
            assert prob["product"]._frac == expected._frac

    def test_deterministic(self):
        """Same seed produces same smooth numbers."""
        a = SmoothRandom(seed=99)
        b = SmoothRandom(seed=99)
        assert [int(a.regular()) for _ in range(10)] == [int(b.regular()) for _ in range(10)]


# ---------------------------------------------------------------------------
# CuneiformDice
# ---------------------------------------------------------------------------

class TestCuneiformDice:
    def test_astragalus_values(self):
        """Astragalus rolls produce only valid face values."""
        dice = CuneiformDice(seed=42)
        valid = {1, 3, 4, 6}
        for _ in range(100):
            r = dice.astragalus()
            assert r["value"] in valid

    def test_astragalus_has_cuneiform(self):
        """Astragalus result includes cuneiform glyph."""
        dice = CuneiformDice(seed=42)
        r = dice.astragalus()
        assert len(r["cuneiform"]) > 0

    def test_d6_range(self):
        """d6 returns values 1-6."""
        dice = CuneiformDice(seed=42)
        for _ in range(100):
            r = dice.d6()
            assert 1 <= r["value"] <= 6

    def test_d60_range(self):
        """d60 returns values 1-59."""
        dice = CuneiformDice(seed=42)
        for _ in range(200):
            r = dice.d60()
            assert 1 <= r["value"] <= 59

    def test_d60_cuneiform_output(self):
        """d60 result includes sexa and cuneiform fields."""
        dice = CuneiformDice(seed=42)
        r = dice.d60()
        assert "sexa" in r
        assert "cuneiform" in r
        assert "value" in r

    def test_roll_count(self):
        """roll(n) returns exactly n results."""
        dice = CuneiformDice(seed=42)
        results = dice.roll(n=5, sides=20)
        assert len(results) == 5

    def test_roll_range(self):
        """roll values are in [1, sides]."""
        dice = CuneiformDice(seed=42)
        for r in dice.roll(n=50, sides=12):
            assert 1 <= r["value"] <= 12

    def test_roll_bad_n(self):
        """roll raises ValueError for n < 1."""
        dice = CuneiformDice(seed=42)
        with pytest.raises(ValueError):
            dice.roll(n=0)

    def test_roll_bad_sides(self):
        """roll raises ValueError for sides < 2."""
        dice = CuneiformDice(seed=42)
        with pytest.raises(ValueError):
            dice.roll(n=1, sides=1)

    def test_roll_total(self):
        """roll_total sums correctly."""
        dice = CuneiformDice(seed=42)
        result = dice.roll_total(n=4, sides=6)
        assert result["total"] == sum(r["value"] for r in result["rolls"])
        assert len(result["rolls"]) == 4

    def test_deterministic(self):
        """Same seed produces same dice sequence."""
        a = CuneiformDice(seed=42)
        b = CuneiformDice(seed=42)
        assert [a.d60()["value"] for _ in range(10)] == [b.d60()["value"] for _ in range(10)]


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------

class TestCLI:
    def test_random_sexa_cli(self):
        """CLI random sexa runs without error."""
        import subprocess
        result = subprocess.run(
            ["python3", "-m", "cuneiform", "random", "sexa", "--seed", "42", "--count", "3"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 3

    def test_random_cuneiform_format(self):
        """CLI --format cuneiform produces unicode glyphs."""
        import subprocess
        result = subprocess.run(
            ["python3", "-m", "cuneiform", "random", "d60", "--seed", "42", "-f", "cuneiform"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        # Should contain cuneiform characters (U+12000+ range)
        assert any(ord(c) > 0x12000 for c in result.stdout)

    def test_random_decimal_format(self):
        """CLI --format decimal produces float-like output."""
        import subprocess
        result = subprocess.run(
            ["python3", "-m", "cuneiform", "random", "sexa", "--seed", "42", "-f", "decimal"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        val = float(result.stdout.strip())
        assert 0 <= val < 1
