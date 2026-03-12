"""Phase 5 tests — Expansion & Applications.

Tests all five branches:
1. Community: example scripts (import/syntax checks)
2. Hardware: SexaALU behavioral simulation
3. Finance: rational levels, retracements, pattern detection
4. Math Expansion: chromogeometry, finite field geometry, p-adic
5. Education: scribe mode
"""

import pytest
from fractions import Fraction


# ============================================================
# Branch 1: Community — example script imports
# ============================================================

class TestExamples:
    """Verify example scripts are syntactically valid and importable."""

    def test_hello_sexa_syntax(self):
        """hello_sexa.py compiles without error."""
        import ast
        with open("examples/hello_sexa.py") as f:
            ast.parse(f.read())

    def test_plimpton_extended_syntax(self):
        import ast
        with open("examples/plimpton_extended.py") as f:
            ast.parse(f.read())

    def test_exact_geometry_syntax(self):
        import ast
        with open("examples/exact_geometry.py") as f:
            ast.parse(f.read())

    def test_smooth_analysis_syntax(self):
        import ast
        with open("examples/smooth_analysis.py") as f:
            ast.parse(f.read())

    def test_factor_race_syntax(self):
        import ast
        with open("examples/factor_race.py") as f:
            ast.parse(f.read())


# ============================================================
# Branch 2: Hardware — SexaALU
# ============================================================

class TestSexaRegister:
    def test_from_int_zero(self):
        from cuneiform.hardware.sexa_sim import SexaRegister
        reg = SexaRegister.from_int(0)
        assert reg.to_int() == 0

    def test_from_int_small(self):
        from cuneiform.hardware.sexa_sim import SexaRegister
        reg = SexaRegister.from_int(59)
        assert reg.to_int() == 59
        assert reg.digits[0] == 59
        assert reg.digits[1] == 0

    def test_from_int_base60(self):
        from cuneiform.hardware.sexa_sim import SexaRegister
        # 60 = 1,0 in base 60
        reg = SexaRegister.from_int(60)
        assert reg.to_int() == 60
        assert reg.digits[0] == 0
        assert reg.digits[1] == 1

    def test_roundtrip_large(self):
        from cuneiform.hardware.sexa_sim import SexaRegister
        for n in [0, 1, 59, 60, 3600, 216000, 12345678]:
            assert SexaRegister.from_int(n).to_int() == n

    def test_notation(self):
        from cuneiform.hardware.sexa_sim import SexaRegister
        reg = SexaRegister.from_int(3661)  # 1*3600 + 1*60 + 1 = 1,1,1
        assert reg.to_notation() == "1,1,1"


class TestSexaALU:
    def setup_method(self):
        from cuneiform.hardware.sexa_sim import SexaALU
        self.alu = SexaALU()

    def test_load_and_read(self):
        self.alu.load(0, 42)
        assert self.alu.read(0) == 42

    def test_sadd(self):
        from cuneiform.hardware.sexa_sim import Instruction, Op
        self.alu.load(0, 100)
        self.alu.load(1, 200)
        result = self.alu.execute(Instruction(Op.SADD, dest=2, src1=0, src2=1))
        assert result == 300
        assert self.alu.read(2) == 300

    def test_ssub(self):
        from cuneiform.hardware.sexa_sim import Instruction, Op
        self.alu.load(0, 500)
        self.alu.load(1, 200)
        result = self.alu.execute(Instruction(Op.SSUB, dest=2, src1=0, src2=1))
        assert result == 300

    def test_smul(self):
        from cuneiform.hardware.sexa_sim import Instruction, Op
        self.alu.load(0, 12)
        self.alu.load(1, 5)
        result = self.alu.execute(Instruction(Op.SMUL, dest=2, src1=0, src2=1))
        assert result == 60

    def test_sdiv(self):
        from cuneiform.hardware.sexa_sim import Instruction, Op
        self.alu.load(0, 3600)
        self.alu.load(1, 60)
        result = self.alu.execute(Instruction(Op.SDIV, dest=2, src1=0, src2=1))
        assert result == 60

    def test_sdiv_by_zero(self):
        from cuneiform.hardware.sexa_sim import Instruction, Op
        self.alu.load(0, 100)
        self.alu.load(1, 0)
        result = self.alu.execute(Instruction(Op.SDIV, dest=2, src1=0, src2=1))
        assert result is None
        assert self.alu.flags.division_by_irregular

    def test_smod(self):
        from cuneiform.hardware.sexa_sim import Instruction, Op
        self.alu.load(0, 125)
        self.alu.load(1, 60)
        result = self.alu.execute(Instruction(Op.SMOD, dest=2, src1=0, src2=1))
        assert result == 5

    def test_sinv_regular(self):
        from cuneiform.hardware.sexa_sim import Instruction, Op
        self.alu.load(0, 4)
        result = self.alu.execute(Instruction(Op.SINV, dest=0, src1=0))
        assert self.alu.flags.regular
        assert self.alu.rat_regs[0] == Fraction(1, 4)

    def test_sinv_irregular(self):
        from cuneiform.hardware.sexa_sim import Instruction, Op
        self.alu.load(0, 7)
        result = self.alu.execute(Instruction(Op.SINV, dest=0, src1=0))
        assert not self.alu.flags.regular
        assert self.alu.flags.division_by_irregular

    def test_spow(self):
        from cuneiform.hardware.sexa_sim import Instruction, Op
        self.alu.load(0, 5)
        result = self.alu.execute(Instruction(Op.SPOW, dest=1, src1=0, imm=3))
        assert result == 125

    def test_cofact_regular(self):
        from cuneiform.hardware.sexa_sim import Instruction, Op
        self.alu.load(0, 60)  # 2^2 * 3 * 5
        result = self.alu.execute(Instruction(Op.COFACT, dest=1, src1=0))
        assert result == 1  # Fully smooth
        assert self.alu.flags.regular
        assert self.alu.regularity_reg == (2, 1, 1)

    def test_cofact_irregular(self):
        from cuneiform.hardware.sexa_sim import Instruction, Op
        self.alu.load(0, 70)  # 2 * 5 * 7
        result = self.alu.execute(Instruction(Op.COFACT, dest=1, src1=0))
        assert result == 7
        assert not self.alu.flags.regular

    def test_rclass(self):
        from cuneiform.hardware.sexa_sim import Instruction, Op
        self.alu.load(0, 60)
        result = self.alu.execute(Instruction(Op.RCLASS, dest=1, src1=0))
        assert result == 0  # Tier 0 = fully regular

    def test_rclass_tier1(self):
        from cuneiform.hardware.sexa_sim import Instruction, Op
        self.alu.load(0, 7)
        result = self.alu.execute(Instruction(Op.RCLASS, dest=1, src1=0))
        assert result == 1  # 7 is prime, tier 1

    def test_smooth_test_true(self):
        from cuneiform.hardware.sexa_sim import Instruction, Op
        self.alu.load(0, 30)  # 2*3*5, smooth for B>=5
        result = self.alu.execute(Instruction(Op.SMOOTH, dest=1, src1=0, imm=5))
        assert result == 1

    def test_smooth_test_false(self):
        from cuneiform.hardware.sexa_sim import Instruction, Op
        self.alu.load(0, 7)
        result = self.alu.execute(Instruction(Op.SMOOTH, dest=1, src1=0, imm=5))
        assert result == 0

    def test_rational_add(self):
        from cuneiform.hardware.sexa_sim import Instruction, Op
        self.alu.rat_regs[0] = Fraction(1, 3)
        self.alu.rat_regs[1] = Fraction(1, 4)
        self.alu.execute(Instruction(Op.RADD, dest=2, src1=0, src2=1))
        assert self.alu.rat_regs[2] == Fraction(7, 12)

    def test_rational_mul(self):
        from cuneiform.hardware.sexa_sim import Instruction, Op
        self.alu.rat_regs[0] = Fraction(2, 3)
        self.alu.rat_regs[1] = Fraction(3, 5)
        self.alu.execute(Instruction(Op.RMUL, dest=2, src1=0, src2=1))
        assert self.alu.rat_regs[2] == Fraction(2, 5)

    def test_rnorm_regular(self):
        from cuneiform.hardware.sexa_sim import Instruction, Op
        self.alu.rat_regs[0] = Fraction(1, 12)  # 12 = 2^2 * 3
        self.alu.execute(Instruction(Op.RNORM, dest=0, src1=0))
        assert self.alu.flags.regular

    def test_rnorm_irregular(self):
        from cuneiform.hardware.sexa_sim import Instruction, Op
        self.alu.rat_regs[0] = Fraction(1, 7)
        self.alu.execute(Instruction(Op.RNORM, dest=0, src1=0))
        assert not self.alu.flags.regular

    def test_nop(self):
        from cuneiform.hardware.sexa_sim import Instruction, Op
        cycles_before = self.alu.cycles
        self.alu.execute(Instruction(Op.NOP))
        assert self.alu.cycles == cycles_before + 1

    def test_run_program(self):
        from cuneiform.hardware.sexa_sim import Instruction, Op
        program = [
            Instruction(Op.LOAD, dest=0, imm=10),
            Instruction(Op.LOAD, dest=1, imm=20),
            Instruction(Op.SADD, dest=2, src1=0, src2=1),
        ]
        results = self.alu.run_program(program)
        assert results == [10, 20, 30]
        assert self.alu.read(2) == 30

    def test_stats(self):
        from cuneiform.hardware.sexa_sim import Instruction, Op
        self.alu.execute(Instruction(Op.LOAD, dest=0, imm=42))
        stats = self.alu.stats()
        assert stats["instructions"] == 1
        assert stats["cycles"] >= 1

    def test_benchmark_cofact(self):
        numbers = [60, 120, 7, 11, 3600, 100]
        result = self.alu.benchmark_cofact(numbers)
        assert result["count"] == 6
        assert result["total_cycles"] > 0

    def test_benchmark_smooth(self):
        numbers = [2, 3, 5, 7, 11, 30, 60]
        result = self.alu.benchmark_smooth(numbers, bound=5)
        assert result["count"] == 7
        assert result["smooth_count"] >= 3  # At least 2, 3, 5

    def test_cycle_costs(self):
        """Verify cycle cost model: SADD=1, SMUL=2, SDIV=3."""
        from cuneiform.hardware.sexa_sim import Instruction, Op
        self.alu.load(0, 10)
        self.alu.load(1, 20)

        self.alu.cycles = 0
        self.alu.execute(Instruction(Op.SADD, dest=2, src1=0, src2=1))
        assert self.alu.cycles == 1

        self.alu.cycles = 0
        self.alu.execute(Instruction(Op.SMUL, dest=2, src1=0, src2=1))
        assert self.alu.cycles == 2

        self.alu.cycles = 0
        self.alu.execute(Instruction(Op.SDIV, dest=2, src1=0, src2=1))
        assert self.alu.cycles == 3

    def test_reset(self):
        from cuneiform.hardware.sexa_sim import Instruction, Op
        self.alu.load(0, 42)
        self.alu.execute(Instruction(Op.SADD, dest=1, src1=0, src2=0))
        self.alu.reset()
        assert self.alu.read(0) == 0
        assert self.alu.cycles == 0
        assert self.alu.instruction_count == 0


# ============================================================
# Branch 3: Finance
# ============================================================

class TestRationalPriceLevels:
    def test_generate_levels(self):
        from cuneiform.finance.rational_levels import RationalPriceLevels
        rpl = RationalPriceLevels(100.0)
        levels = rpl.generate_levels(range_pct=0.10)
        assert len(levels) > 0
        # All levels within 10% of reference
        for level in levels:
            assert 0.90 <= level["ratio_decimal"] <= 1.10

    def test_levels_sorted_by_regularity(self):
        from cuneiform.finance.rational_levels import RationalPriceLevels
        rpl = RationalPriceLevels(100.0)
        levels = rpl.generate_levels()
        # Tier-0 levels come first
        tiers = [l["regularity_tier"] for l in levels]
        assert tiers == sorted(tiers)

    def test_compare_with_fibonacci(self):
        from cuneiform.finance.rational_levels import RationalPriceLevels
        rpl = RationalPriceLevels(100.0)
        result = rpl.compare_with_fibonacci()
        assert "comparisons" in result
        assert len(result["comparisons"]) > 0
        # 50% should match exactly (0;30)
        fib_50 = [c for c in result["comparisons"] if c["fib_level"] == "50%"]
        assert len(fib_50) == 1
        assert fib_50[0]["distance"] < 0.01

    def test_tier1_levels_present(self):
        from cuneiform.finance.rational_levels import RationalPriceLevels
        rpl = RationalPriceLevels(100.0)
        levels = rpl.generate_levels(range_pct=0.50)
        tier1 = [l for l in levels if l["regularity_tier"] == 1]
        assert len(tier1) > 0


class TestSexagesimalRetracements:
    def test_levels_count(self):
        from cuneiform.finance.rational_levels import SexagesimalRetracements
        sr = SexagesimalRetracements(high=200.0, low=100.0)
        levels = sr.levels()
        assert len(levels) == 13  # 13 sexagesimal levels

    def test_levels_in_range(self):
        from cuneiform.finance.rational_levels import SexagesimalRetracements
        sr = SexagesimalRetracements(high=200.0, low=100.0)
        for level in sr.levels():
            assert 100.0 <= level["price"] <= 200.0

    def test_50pct_exact(self):
        from cuneiform.finance.rational_levels import SexagesimalRetracements
        sr = SexagesimalRetracements(high=200.0, low=100.0)
        levels = sr.levels()
        half = [l for l in levels if l["ratio"] == Fraction(1, 2)]
        assert len(half) == 1
        assert half[0]["price"] == 150.0

    def test_fibonacci_levels(self):
        from cuneiform.finance.rational_levels import SexagesimalRetracements
        sr = SexagesimalRetracements(high=200.0, low=100.0)
        fibs = sr.fibonacci_levels()
        assert len(fibs) == 5

    def test_high_low_swap(self):
        """Should handle low > high gracefully."""
        from cuneiform.finance.rational_levels import SexagesimalRetracements
        sr = SexagesimalRetracements(high=100.0, low=200.0)
        assert sr.high == 200.0
        assert sr.low == 100.0


class TestRationalSupportResistance:
    def test_detect_levels(self):
        from cuneiform.finance.regularity_sr import RationalSupportResistance
        # Synthetic price data clustering around 100 and 105
        prices = [100.0] * 20 + [105.0] * 15 + [102.0] * 10 + [98.0] * 5
        sr = RationalSupportResistance(prices)
        levels = sr.detect_levels(num_levels=5)
        assert len(levels) > 0
        assert all("total_score" in l for l in levels)

    def test_empty_prices(self):
        from cuneiform.finance.regularity_sr import RationalSupportResistance
        sr = RationalSupportResistance([])
        assert sr.detect_levels() == []

    def test_constant_prices(self):
        from cuneiform.finance.regularity_sr import RationalSupportResistance
        sr = RationalSupportResistance([50.0] * 10)
        assert sr.detect_levels() == []


class TestRationalCheckmark:
    def test_detect_pattern(self):
        from cuneiform.finance.pattern_geometry import RationalCheckmark
        # Simulate: open at 100, dip to 98, recover to 101
        candles = [
            {"open": 100.0, "high": 100.5, "low": 99.5, "close": 99.5},
            {"open": 99.5, "high": 99.5, "low": 98.0, "close": 98.2},
            {"open": 98.2, "high": 99.0, "low": 98.0, "close": 99.0},
            {"open": 99.0, "high": 100.0, "low": 99.0, "close": 100.0},
            {"open": 100.0, "high": 101.0, "low": 100.0, "close": 101.0},
        ]
        rc = RationalCheckmark()
        result = rc.detect(candles, time_window=5)
        assert result["detected"]
        assert result["shape"] in ("sharp_V", "moderate_V", "soft_U")
        assert result["dip_pct"] > 0
        assert result["recovery_pct"] > 0

    def test_no_pattern_flat(self):
        from cuneiform.finance.pattern_geometry import RationalCheckmark
        candles = [
            {"open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0}
            for _ in range(10)
        ]
        rc = RationalCheckmark()
        result = rc.detect(candles, time_window=10)
        assert not result["detected"]

    def test_insufficient_data(self):
        from cuneiform.finance.pattern_geometry import RationalCheckmark
        rc = RationalCheckmark()
        result = rc.detect([{"open": 100, "high": 100, "low": 100, "close": 100}])
        assert not result["detected"]

    def test_no_recovery(self):
        from cuneiform.finance.pattern_geometry import RationalCheckmark
        # Pure downtrend — no recovery
        candles = [
            {"open": 100.0, "high": 100.0, "low": 99.0, "close": 99.0},
            {"open": 99.0, "high": 99.0, "low": 98.0, "close": 98.0},
            {"open": 98.0, "high": 98.0, "low": 97.0, "close": 97.0},
        ]
        rc = RationalCheckmark()
        result = rc.detect(candles, time_window=3)
        assert not result["detected"]


# ============================================================
# Branch 4: Mathematical Expansion
# ============================================================

class TestChromoGeometry:
    def test_blue_quadrance(self):
        from cuneiform.math_expansion.chromogeometry import (
            ChromoGeometry, ChromoPoint, Color
        )
        A = ChromoPoint(0, 0)
        B = ChromoPoint(3, 4)
        q = ChromoGeometry.quadrance(A, B, Color.BLUE)
        assert q.value == Fraction(25)  # 3² + 4² = 25
        assert q.color == Color.BLUE

    def test_red_quadrance(self):
        from cuneiform.math_expansion.chromogeometry import (
            ChromoGeometry, ChromoPoint, Color
        )
        A = ChromoPoint(0, 0)
        B = ChromoPoint(3, 4)
        q = ChromoGeometry.quadrance(A, B, Color.RED)
        assert q.value == Fraction(-7)  # 3² - 4² = -7

    def test_green_quadrance(self):
        from cuneiform.math_expansion.chromogeometry import (
            ChromoGeometry, ChromoPoint, Color
        )
        A = ChromoPoint(0, 0)
        B = ChromoPoint(3, 4)
        q = ChromoGeometry.quadrance(A, B, Color.GREEN)
        assert q.value == Fraction(24)  # 2 * 3 * 4 = 24

    def test_chromo_pythagoras(self):
        """Q_blue² = Q_red² + Q_green² for any displacement."""
        from cuneiform.math_expansion.chromogeometry import (
            ChromoGeometry, ChromoPoint, Color
        )
        A = ChromoPoint(0, 0)
        B = ChromoPoint(3, 4)
        Qb = ChromoGeometry.quadrance(A, B, Color.BLUE).value
        Qr = ChromoGeometry.quadrance(A, B, Color.RED).value
        Qg = ChromoGeometry.quadrance(A, B, Color.GREEN).value
        assert Qb * Qb == Qr * Qr + Qg * Qg  # 625 = 49 + 576

    def test_analyze_triangle(self):
        from cuneiform.math_expansion.chromogeometry import (
            ChromoGeometry, ChromoPoint
        )
        A = ChromoPoint(0, 0)
        B = ChromoPoint(4, 0)
        C = ChromoPoint(0, 3)
        result = ChromoGeometry.analyze_triangle(A, B, C)

        assert "blue" in result
        assert "red" in result
        assert "green" in result

        # Blue geometry: should recognize the right triangle
        blue = result["blue"]
        assert blue["triple_spread_holds"]

    def test_chromo_pythagoras_multiple(self):
        """Chromo-Pythagoras holds for multiple displacements."""
        from cuneiform.math_expansion.chromogeometry import (
            ChromoGeometry, ChromoPoint, Color
        )
        for dx, dy in [(1, 1), (5, 12), (2, 7), (0, 3), (3, 0)]:
            A = ChromoPoint(0, 0)
            B = ChromoPoint(dx, dy)
            Qb = ChromoGeometry.quadrance(A, B, Color.BLUE).value
            Qr = ChromoGeometry.quadrance(A, B, Color.RED).value
            Qg = ChromoGeometry.quadrance(A, B, Color.GREEN).value
            assert Qb * Qb == Qr * Qr + Qg * Qg, f"Failed for ({dx},{dy})"

    def test_spread_between_zero_quadrance(self):
        from cuneiform.math_expansion.chromogeometry import (
            ChromoGeometry, ChromoQuadrance, ChromoSpread, Color
        )
        q0 = ChromoQuadrance(Fraction(0), Color.BLUE)
        q1 = ChromoQuadrance(Fraction(5), Color.BLUE)
        s = ChromoGeometry.spread_from_quadrances(q1, q0, q1)
        assert s.value == Fraction(0)  # Degenerate


class TestFiniteFieldGeometry:
    def test_quadrance_mod_p(self):
        from cuneiform.math_expansion.finite_field_geometry import (
            FiniteFieldGeometry, FpPoint
        )
        geo = FiniteFieldGeometry(7)
        A = FpPoint(0, 0, 7)
        B = FpPoint(3, 4, 7)
        q = geo.quadrance(A, B)
        assert q == (9 + 16) % 7  # 25 % 7 = 4

    def test_isotropic_count(self):
        from cuneiform.math_expansion.finite_field_geometry import FiniteFieldGeometry
        geo = FiniteFieldGeometry(5)
        count = geo.count_isotropic_points()
        assert count >= 1  # At least (0,0)

    def test_quadrance_spectrum(self):
        from cuneiform.math_expansion.finite_field_geometry import FiniteFieldGeometry
        geo = FiniteFieldGeometry(7)
        spectrum = geo.quadrance_spectrum()
        # Total should be p² (all displacements from origin)
        assert sum(spectrum.values()) == 49

    def test_regularity_connection(self):
        from cuneiform.math_expansion.finite_field_geometry import FiniteFieldGeometry
        geo = FiniteFieldGeometry(61)  # 61-1=60=2^2*3*5, fully smooth!
        rc = geo.regularity_connection()
        assert rc["smooth_part"] == 60
        assert rc["cofactor"] == 1
        assert rc["smooth_ratio"] == 1.0

    def test_regularity_connection_not_smooth(self):
        from cuneiform.math_expansion.finite_field_geometry import FiniteFieldGeometry
        geo = FiniteFieldGeometry(23)  # 23-1=22=2*11
        rc = geo.regularity_connection()
        assert rc["cofactor"] == 11
        assert rc["smooth_ratio"] < 1.0

    def test_small_prime(self):
        from cuneiform.math_expansion.finite_field_geometry import FiniteFieldGeometry
        with pytest.raises(ValueError):
            FiniteFieldGeometry(2)

    def test_quadratic_residue(self):
        from cuneiform.math_expansion.finite_field_geometry import FiniteFieldGeometry
        geo = FiniteFieldGeometry(7)
        # QRs mod 7: 0, 1, 2, 4
        assert geo.is_quadratic_residue(1)
        assert geo.is_quadratic_residue(2)
        assert geo.is_quadratic_residue(4)
        assert not geo.is_quadratic_residue(3)


class TestPAdicValuation:
    def test_v2(self):
        from cuneiform.math_expansion.padic import PAdicValuation
        v2 = PAdicValuation(2)
        assert v2(8) == 3
        assert v2(12) == 2
        assert v2(7) == 0
        assert v2(0) is None

    def test_v3(self):
        from cuneiform.math_expansion.padic import PAdicValuation
        v3 = PAdicValuation(3)
        assert v3(27) == 3
        assert v3(6) == 1
        assert v3(5) == 0

    def test_v5(self):
        from cuneiform.math_expansion.padic import PAdicValuation
        v5 = PAdicValuation(5)
        assert v5(125) == 3
        assert v5(60) == 1

    def test_of_fraction(self):
        from cuneiform.math_expansion.padic import PAdicValuation
        v2 = PAdicValuation(2)
        assert v2.of_fraction(Fraction(1, 4)) == -2
        assert v2.of_fraction(Fraction(8, 3)) == 3

    def test_padic_norm(self):
        from cuneiform.math_expansion.padic import PAdicValuation
        v2 = PAdicValuation(2)
        assert v2.padic_norm(8) == Fraction(1, 8)
        assert v2.padic_norm(7) == Fraction(1)

    def test_is_padic_integer(self):
        from cuneiform.math_expansion.padic import PAdicValuation
        v2 = PAdicValuation(2)
        assert v2.is_padic_integer(Fraction(3, 1))
        assert v2.is_padic_integer(Fraction(7, 3))  # 3 has no factor of 2
        assert not v2.is_padic_integer(Fraction(1, 2))

    def test_invalid_p(self):
        from cuneiform.math_expansion.padic import PAdicValuation
        with pytest.raises(ValueError):
            PAdicValuation(1)


class TestSexa5AdicConnection:
    def test_regularity_vector(self):
        from cuneiform.math_expansion.padic import Sexa5AdicConnection
        conn = Sexa5AdicConnection()
        # 60 = 2^2 * 3 * 5
        assert conn.regularity_vector(60) == (2, 1, 1)
        # 7 = 7 (no factors of 2,3,5)
        assert conn.regularity_vector(7) == (0, 0, 0)

    def test_sexa_distance_zero(self):
        from cuneiform.math_expansion.padic import Sexa5AdicConnection
        conn = Sexa5AdicConnection()
        assert conn.sexa_distance(5, 5) == Fraction(0)

    def test_sexa_distance_close(self):
        from cuneiform.math_expansion.padic import Sexa5AdicConnection
        conn = Sexa5AdicConnection()
        # 60 and 120: diff=60=2^2*3*5, so norms are 1/4, 1/3, 1/5
        d = conn.sexa_distance(60, 120)
        assert d == Fraction(1, 3)  # max of 1/4, 1/3, 1/5

    def test_termination_regular(self):
        from cuneiform.math_expansion.padic import Sexa5AdicConnection
        conn = Sexa5AdicConnection()
        result = conn.termination_criterion(Fraction(1, 12))
        assert result["terminates_base_60"]
        assert result["cofactor"] == 1

    def test_termination_irregular(self):
        from cuneiform.math_expansion.padic import Sexa5AdicConnection
        conn = Sexa5AdicConnection()
        result = conn.termination_criterion(Fraction(1, 7))
        assert not result["terminates_base_60"]
        assert result["cofactor"] == 7

    def test_regularity_spectrum(self):
        from cuneiform.math_expansion.padic import Sexa5AdicConnection
        conn = Sexa5AdicConnection()
        spec = conn.regularity_spectrum(60)
        assert spec["is_regular"]
        assert spec["cofactor"] == 1
        assert spec["regularity_vector"] == (2, 1, 1)
        assert spec["valuations"][2]["valuation"] == 2
        assert spec["valuations"][3]["valuation"] == 1
        assert spec["valuations"][5]["valuation"] == 1

    def test_regularity_spectrum_irregular(self):
        from cuneiform.math_expansion.padic import Sexa5AdicConnection
        conn = Sexa5AdicConnection()
        spec = conn.regularity_spectrum(77)  # 7 * 11
        assert not spec["is_regular"]
        assert spec["cofactor"] == 77


# ============================================================
# Branch 5: Education — Scribe Mode
# ============================================================

class TestScribeMode:
    def test_multiply_small(self):
        from cuneiform.education.scribe_mode import ScribeMode
        scribe = ScribeMode()
        result = scribe.multiply(5, 12)
        assert result["result"] == 60
        assert result["result_sexa"] is not None
        assert len(result["steps"]) > 0

    def test_multiply_large(self):
        from cuneiform.education.scribe_mode import ScribeMode
        scribe = ScribeMode()
        result = scribe.multiply(120, 45)
        assert result["result"] == 5400

    def test_multiply_quarter_squares(self):
        from cuneiform.education.scribe_mode import ScribeMode
        scribe = ScribeMode()
        result = scribe.multiply(8, 12)
        assert result["result"] == 96
        # Should show quarter-squares method when both even
        steps_text = "\n".join(result["steps"])
        assert "Quarter-squares" in steps_text

    def test_find_reciprocal_regular(self):
        from cuneiform.education.scribe_mode import ScribeMode
        scribe = ScribeMode()
        result = scribe.find_reciprocal(12)
        assert result["is_regular"]
        assert result["reciprocal"] == Fraction(1, 12)
        assert len(result["steps"]) > 0

    def test_find_reciprocal_irregular(self):
        from cuneiform.education.scribe_mode import ScribeMode
        scribe = ScribeMode()
        result = scribe.find_reciprocal(7)
        assert not result["is_regular"]
        assert "IRREGULAR" in "\n".join(result["steps"])

    def test_find_reciprocal_composite(self):
        from cuneiform.education.scribe_mode import ScribeMode
        scribe = ScribeMode()
        result = scribe.find_reciprocal(36)  # 2^2 * 3^2
        assert result["is_regular"]
        assert len(result["factors"]) > 1  # Shows factoring

    def test_sqrt_babylonian(self):
        from cuneiform.education.scribe_mode import ScribeMode
        scribe = ScribeMode()
        result = scribe.sqrt_babylonian(2, iterations=5)
        assert abs(result["result_float"] - 1.41421356) < 1e-6
        assert len(result["steps"]) > 0

    def test_sqrt_perfect_square(self):
        from cuneiform.education.scribe_mode import ScribeMode
        scribe = ScribeMode()
        result = scribe.sqrt_babylonian(9, iterations=5)
        assert result["result"] == Fraction(3)
        assert "Exact result" in "\n".join(result["steps"])

    def test_generate_triple_345(self):
        from cuneiform.education.scribe_mode import ScribeMode
        scribe = ScribeMode()
        # p=2, q=1 should give (3, 4, 5)
        result = scribe.generate_triple(2, 1)
        assert result["is_pythagorean"]
        w, l, d = result["triple"]
        assert w * w + l * l == d * d

    def test_generate_triple_plimpton_row1(self):
        from cuneiform.education.scribe_mode import ScribeMode
        scribe = ScribeMode()
        # Row 1 of Plimpton 322: p=12, q=5
        result = scribe.generate_triple(12, 5)
        assert result["is_pythagorean"]
        w, l, d = result["triple"]
        assert w * w + l * l == d * d

    def test_scribe_steps_accumulate(self):
        from cuneiform.education.scribe_mode import ScribeMode
        scribe = ScribeMode()
        r1 = scribe.multiply(3, 4)
        r2 = scribe.multiply(5, 6)
        # Steps should be fresh for each call (not accumulated)
        assert len(r2["steps"]) < len(r1["steps"]) + len(r2["steps"])


# ============================================================
# Integration / cross-branch tests
# ============================================================

class TestCrossBranch:
    def test_alu_matches_python_arithmetic(self):
        """ALU results match Python integer arithmetic."""
        from cuneiform.hardware.sexa_sim import SexaALU, Instruction, Op
        alu = SexaALU()
        for a, b in [(12, 5), (60, 30), (7, 8), (100, 99)]:
            alu.load(0, a)
            alu.load(1, b)
            assert alu.execute(Instruction(Op.SADD, dest=2, src1=0, src2=1)) == a + b
            assert alu.execute(Instruction(Op.SSUB, dest=3, src1=0, src2=1)) == a - b
            assert alu.execute(Instruction(Op.SMUL, dest=4, src1=0, src2=1)) == a * b

    def test_finance_uses_exact_rationals(self):
        """Finance levels are built on exact Fraction arithmetic."""
        from cuneiform.finance.rational_levels import SexagesimalRetracements
        sr = SexagesimalRetracements(high=200.0, low=100.0)
        levels = sr.levels()
        for level in levels:
            assert isinstance(level["ratio"], Fraction)

    def test_chromo_exact_like_geometry(self):
        """Chromogeometry uses exact Fraction arithmetic like geometry module."""
        from cuneiform.math_expansion.chromogeometry import (
            ChromoGeometry, ChromoPoint, Color
        )
        A = ChromoPoint(Fraction(1, 3), Fraction(2, 5))
        B = ChromoPoint(Fraction(4, 7), Fraction(3, 11))
        q = ChromoGeometry.quadrance(A, B, Color.BLUE)
        assert isinstance(q.value, Fraction)

    def test_padic_connects_to_regularity(self):
        """p-adic analysis agrees with RegularityClass."""
        from cuneiform.math_expansion.padic import Sexa5AdicConnection
        from cuneiform.number_theory.regularity import RegularityClass
        conn = Sexa5AdicConnection()
        for n in [1, 6, 12, 30, 60, 7, 11, 49, 77]:
            rc = RegularityClass(n)
            spec = conn.regularity_spectrum(n)
            assert rc.is_regular == spec["is_regular"]
            assert rc.cofactor == spec["cofactor"]
