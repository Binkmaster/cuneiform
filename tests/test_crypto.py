"""Tests for the crypto analysis layer (Phase 4)."""

import pytest
from math import gcd

from cuneiform.crypto.scaling import ScalingAnalysis
from cuneiform.crypto.rsa_analysis import (
    RSAAnalysis, _cf_convergents, _sexa_cf_convergents, _nearest_smooth,
)
from cuneiform.crypto.lattice import (
    SexagesimalLattice, LatticeReductionComparison, lll_reduce,
)
from cuneiform.crypto.elliptic import (
    EllipticCurveRegularityAnalysis, ECDLPRegularityAttack,
    _ec_add_fp, _ec_mul_fp, _count_points_naive,
)
from cuneiform.crypto.post_quantum import PostQuantumRegularityAnalysis
from cuneiform.crypto.continued_fractions import (
    SexagesimalContinuedFractions, cf_expansion, cf_convergents,
)
from cuneiform.crypto.theoretical import TheoreticalAnalysis, dickman_rho
from cuneiform.crypto.side_channel import TimingAnalysis
from cuneiform.publication.paper import PaperGenerator
from cuneiform.publication.figures import FigureGenerator
from cuneiform.publication.tables import TableGenerator


# ─── Scaling ───────────────────────────────────────────────────────────

class TestScalingAnalysis:
    def test_smooth_density_scaling_runs(self):
        sa = ScalingAnalysis(bit_sizes=[20, 24])
        results = sa.smooth_density_scaling(trials_per_size=2, sieve_range=200)
        assert 20 in results
        assert 24 in results
        for bits, data in results.items():
            assert "tier_rates" in data
            assert "advantage_ratio" in data

    def test_compute_scaling_exponent(self):
        sa = ScalingAnalysis(bit_sizes=[20, 24, 28])
        sa.smooth_density_scaling(trials_per_size=2, sieve_range=200)
        fit = sa.compute_scaling_exponent()
        # Should have alpha and interpretation
        if "error" not in fit:
            assert "alpha" in fit
            assert "interpretation" in fit

    def test_extrapolate(self):
        sa = ScalingAnalysis(bit_sizes=[20, 24, 28])
        sa.smooth_density_scaling(trials_per_size=2, sieve_range=200)
        result = sa.extrapolate_to_rsa()
        if "error" not in result:
            assert "predictions" in result

    def test_regularity_in_sieve_region(self):
        sa = ScalingAnalysis()
        result = sa.regularity_in_sieve_region(15347, sieve_radius=500)
        assert result["total_values"] > 0
        assert "avg_tier_by_residue_mod60" in result

    def test_nfs_polynomial_distribution(self):
        sa = ScalingAnalysis()
        result = sa.nfs_polynomial_value_distribution(bits=20, trials=1)
        assert "tier_rates" in result


# ─── RSA Analysis ──────────────────────────────────────────────────────

class TestRSAAnalysis:
    def test_analyze_factored_rsa(self):
        rsa = RSAAnalysis()
        results = rsa.analyze_factored_rsa()
        assert "RSA-59" in results
        assert "RSA-100" in results
        for name, data in results.items():
            assert "n_tier" in data
            assert "phi_n_tier" in data

    def test_phi_n_regularity(self):
        # Small primes for quick test
        result = RSAAnalysis().phi_n_regularity(103, 149)
        assert result["n"] == 103 * 149
        assert "phi_n_tier" in result

    def test_public_exponent_interaction(self):
        n = 103 * 149
        result = RSAAnalysis().public_exponent_interaction(n)
        assert result["e"] == 65537
        assert "power_tiers" in result

    def test_batch_classify(self):
        result = RSAAnalysis().batch_generate_and_classify(bits=20, count=10)
        assert result["count"] == 10
        assert "tier_distribution" in result

    def test_wiener_attack_enhancement(self):
        n = 103 * 149  # 15347
        e = 65537
        result = RSAAnalysis().wiener_attack_enhancement(n, e)
        assert result["standard_convergents"] > 0
        assert result["sexagesimal_convergents"] > 0


class TestCFHelpers:
    def test_cf_convergents(self):
        # 355/113 ≈ pi, CF = [3; 7, 15, 1]
        convs = _cf_convergents(355, 113)
        assert len(convs) > 0
        # Last convergent should be 355/113
        assert convs[-1] == (355, 113)

    def test_nearest_smooth(self):
        assert _nearest_smooth(1) == 1
        assert _nearest_smooth(60) == 60  # Already smooth
        assert _nearest_smooth(7) in (6, 8)  # 6=2*3 or 8=2^3


# ─── Lattice ───────────────────────────────────────────────────────────

class TestLLLReduce:
    def test_identity(self):
        basis = [[1, 0], [0, 1]]
        reduced, stats = lll_reduce(basis)
        assert reduced == [[1, 0], [0, 1]]
        assert stats["swaps"] == 0

    def test_simple_reduction(self):
        # Classic example: should reduce [[1, 0], [1, 2]] stays same
        basis = [[1, 1], [0, 2]]
        reduced, stats = lll_reduce(basis)
        # Reduced basis should have shorter vectors
        norm = lambda v: sum(x * x for x in v)
        assert norm(reduced[0]) <= norm(basis[0]) + norm(basis[1])

    def test_3d(self):
        basis = [[1, 0, 0], [0, 1, 0], [100, 100, 1]]
        reduced, stats = lll_reduce(basis)
        # Should produce reasonable vectors
        assert len(reduced) == 3
        assert all(len(v) == 3 for v in reduced)


class TestSexagesimalLattice:
    def test_from_random(self):
        lat = SexagesimalLattice.from_random(5, 10)
        assert lat.dim == 5
        assert len(lat.basis) == 5

    def test_regularity_profile(self):
        lat = SexagesimalLattice.from_random(4, 8)
        profile = lat.regularity_profile()
        assert profile["total_entries"] > 0
        assert 0 <= profile["smooth_fraction"] <= 1

    def test_reorder_by_regularity(self):
        lat = SexagesimalLattice.from_random(5, 10)
        reordered = lat.reorder_by_regularity()
        assert len(reordered.basis) == 5

    def test_reduce(self):
        lat = SexagesimalLattice.from_random(4, 8)
        reduced, stats = lat.reduce()
        assert reduced.dim == 4
        assert stats["swaps"] >= 0

    def test_from_reciprocal_pairs(self):
        lat = SexagesimalLattice.from_reciprocal_pairs(60, 4)
        assert lat.dim == 4
        profile = lat.regularity_profile()
        assert profile["total_entries"] > 0

    def test_shortest_vector_norm(self):
        lat = SexagesimalLattice.from_random(3, 8)
        norm = lat.shortest_vector_norm()
        assert norm > 0


class TestLatticeComparison:
    def test_run_comparison(self):
        lrc = LatticeReductionComparison(dimensions=[4, 5])
        result = lrc.run_lll_comparison(4, trials=3, entry_bits=8)
        assert "standard" in result
        assert "regularity_reordered" in result
        assert result["dimension"] == 4

    def test_run_all(self):
        lrc = LatticeReductionComparison(dimensions=[4, 5])
        results = lrc.run_all(trials=2)
        assert 4 in results
        assert 5 in results

    def test_reciprocal_pair_analysis(self):
        lrc = LatticeReductionComparison()
        results = lrc.reciprocal_pair_lattice_analysis(moduli=[60], dim=4)
        assert 60 in results


# ─── Elliptic Curves ──────────────────────────────────────────────────

class TestECArithmetic:
    def test_point_addition(self):
        # y^2 = x^3 + 2x + 3 over F_97
        a, p = 2, 97
        P = (3, 6)
        # Verify point is on curve
        assert (P[1] ** 2) % p == (P[0] ** 3 + a * P[0] + 3) % p
        # Add to identity
        assert _ec_add_fp((0, 0), P, a, p) == P
        assert _ec_add_fp(P, (0, 0), a, p) == P

    def test_point_doubling(self):
        a, p = 2, 97
        P = (3, 6)
        Q = _ec_add_fp(P, P, a, p)
        assert Q != (0, 0)

    def test_scalar_mul(self):
        a, p = 2, 97
        P = (3, 6)
        assert _ec_mul_fp(0, P, a, p) == (0, 0)
        assert _ec_mul_fp(1, P, a, p) == P
        # 2P should equal P+P
        assert _ec_mul_fp(2, P, a, p) == _ec_add_fp(P, P, a, p)

    def test_point_count_small(self):
        # y^2 = x^3 + x + 1 over F_5
        count = _count_points_naive(1, 1, 5)
        assert count > 0
        # Hasse bound: |count - 6| <= 2*sqrt(5) ≈ 4.47
        assert abs(count - 6) <= 5


class TestECRegularity:
    def test_group_order_correlation(self):
        ecra = EllipticCurveRegularityAnalysis(field_size_bits=10)
        result = ecra.group_order_regularity_correlation(num_curves=50)
        assert result["total_curves"] > 0

    def test_plimpton_curve_analysis(self):
        ecra = EllipticCurveRegularityAnalysis()
        result = ecra.plimpton_curve_order_analysis()
        assert result["plimpton_curves"] > 0
        assert result["random_curves"] > 0

    def test_standard_curve_audit(self):
        ecra = EllipticCurveRegularityAnalysis()
        result = ecra.standard_curve_audit()
        assert "secp256k1" in result
        assert "P-256" in result
        assert "Curve25519" in result
        # All should have prime order
        for name, data in result.items():
            assert "order_is_prime" in data


class TestECDLPAttack:
    def test_head_to_head_small(self):
        # y^2 = x^3 + 2x + 3 over F_1009
        a, b, p = 2, 3, 1009
        order = _count_points_naive(a, b, p)
        # Find a generator (just use first point)
        G = None
        for x in range(p):
            rhs = (x ** 3 + a * x + b) % p
            ls = pow(rhs, (p - 1) // 2, p)
            if ls == 1:
                y = pow(rhs, (p + 1) // 4, p)  # works when p ≡ 3 mod 4
                if (y * y) % p == rhs:
                    G = (x, y)
                    break
        if G is not None and order > 2:
            attack = ECDLPRegularityAttack(a, b, p, G, order)
            result = attack.head_to_head(trials=3)
            assert "standard" in result
            assert "regularity" in result


# ─── Post-Quantum ──────────────────────────────────────────────────────

class TestPostQuantum:
    def test_parameter_survey(self):
        pq = PostQuantumRegularityAnalysis()
        result = pq.parameter_regularity_survey()
        assert "ML-KEM-512" in result
        assert "Falcon-512" in result
        assert "Dilithium2" in result
        for name, data in result.items():
            assert "q_tier" in data
            assert "q_mod_60" in data

    def test_kyber_analysis(self):
        pq = PostQuantumRegularityAnalysis()
        result = pq.kyber_specific_analysis()
        assert result["q"] == 3329
        assert "observation" in result

    def test_falcon_analysis(self):
        pq = PostQuantumRegularityAnalysis()
        result = pq.falcon_specific_analysis()
        assert result["q"] == 12289
        # q-1 = 12288 = 2^12 * 3, which IS 5-smooth
        assert result["q_minus_1_is_regular"]

    def test_dilithium_analysis(self):
        pq = PostQuantumRegularityAnalysis()
        result = pq.dilithium_specific_analysis()
        assert result["q"] == 8380417

    def test_full_survey(self):
        pq = PostQuantumRegularityAnalysis()
        result = pq.full_survey()
        assert "parameter_survey" in result
        assert "kyber" in result
        assert "falcon" in result


# ─── Continued Fractions ───────────────────────────────────────────────

class TestCFExpansion:
    def test_standard_cf(self):
        # 355/113 = [3; 7, 16]
        terms = cf_expansion(355, 113)
        assert terms == [3, 7, 16]

    def test_cf_convergents(self):
        terms = [3, 7, 15, 1]
        convs = cf_convergents(terms)
        assert convs[-1] == (355, 113)
        assert convs[0] == (3, 1)

    def test_integer(self):
        terms = cf_expansion(5, 1)
        assert terms == [5]


class TestSexaCF:
    def test_sexa_cf_expansion(self):
        scf = SexagesimalContinuedFractions()
        terms = scf.sexagesimal_cf_expansion(355, 113)
        assert len(terms) > 0

    def test_convergent_quality(self):
        scf = SexagesimalContinuedFractions()
        result = scf.convergent_quality_comparison(355, 113)
        assert result["standard_convergents"] > 0
        assert result["sexagesimal_convergents"] > 0

    def test_stern_brocot(self):
        scf = SexagesimalContinuedFractions()
        result = scf.stern_brocot_smooth_subtree(depth=5)
        assert result["total_nodes"] > 0
        assert result["smooth_nodes"] > 0
        assert 0 < result["overall_smooth_fraction"] <= 1

    def test_wiener_attack(self):
        # Small RSA-like numbers for testing
        p, q = 61, 53
        n = p * q  # 3233
        e = 17
        scf = SexagesimalContinuedFractions()
        result = scf.wiener_attack_enhanced(n, e)
        assert "standard_found" in result
        assert "sexagesimal_found" in result


# ─── Theoretical ───────────────────────────────────────────────────────

class TestDickmanRho:
    def test_values(self):
        assert dickman_rho(0) == 1.0
        assert dickman_rho(1) == 1.0
        assert 0 < dickman_rho(2) < 1  # 1 - ln(2) ≈ 0.307
        assert dickman_rho(3) < dickman_rho(2)

    def test_monotone_decreasing(self):
        prev = dickman_rho(1)
        for u in [2, 3, 4, 5]:
            curr = dickman_rho(u)
            assert curr <= prev
            prev = curr


class TestTheoreticalAnalysis:
    def test_tier_distribution(self):
        ta = TheoreticalAnalysis()
        result = ta.regularity_tier_distribution_theorem(N=1000)
        assert "empirical" in result
        assert "theorem_statement" in result

    def test_smooth_bounds(self):
        ta = TheoreticalAnalysis()
        result = ta.smooth_rate_by_tier_bound(10**6, 100)
        assert result["tier_0"]["smooth_probability"] == 1.0
        assert "predicted_advantage" in result

    def test_asymptotic(self):
        ta = TheoreticalAnalysis()
        result = ta.asymptotic_advantage_analysis(64)
        assert result["asymptotic_class_change"] is False
        assert result["speedup_factor_c"] >= 1.0

    def test_reciprocal_independence(self):
        ta = TheoreticalAnalysis()
        result = ta.reciprocal_pair_independence_analysis(modulus=1009)
        assert result["total_pairs"] > 0
        assert "correlation" in result


# ─── Side Channel ──────────────────────────────────────────────────────

class TestTimingAnalysis:
    def test_division_timing(self):
        numbers = list(range(1, 101))
        ta = TimingAnalysis()
        result = ta.division_timing(numbers, 7, iterations=100)
        assert result["regular_count"] > 0
        assert result["irregular_count"] > 0

    def test_smooth_extraction_timing(self):
        numbers = list(range(1, 51))
        ta = TimingAnalysis()
        result = ta.smooth_extraction_timing(numbers, iterations=10)
        assert 0 in result  # Should have tier 0 entries


# ─── Publication ───────────────────────────────────────────────────────

class TestPaperGenerator:
    def test_generate_latex(self):
        pg = PaperGenerator()
        latex = pg.generate_latex()
        assert r"\documentclass" in latex
        assert r"\begin{document}" in latex
        assert r"\end{document}" in latex
        assert "Plimpton" in latex

    def test_paper_type(self):
        pg = PaperGenerator()
        ptype = pg.determine_paper_type()
        assert ptype in ("breakthrough", "technique", "theoretical", "negative")


class TestFigureGenerator:
    def test_smooth_density_figure(self):
        fg = FigureGenerator()
        tier_rates = {
            0: {"rate": 1.0, "total": 100, "smooth": 100},
            1: {"rate": 0.5, "total": 200, "smooth": 100},
            2: {"rate": 0.3, "total": 300, "smooth": 90},
        }
        latex = fg.smooth_density_by_tier(tier_rates)
        assert r"\begin{tikzpicture}" in latex
        assert "Smooth Density" in latex

    def test_scaling_figure(self):
        fg = FigureGenerator()
        data = {
            32: {"advantage_ratio": 2.5},
            64: {"advantage_ratio": 2.3},
            128: {"advantage_ratio": 2.1},
        }
        latex = fg.scaling_curve(data)
        assert r"\begin{tikzpicture}" in latex

    def test_pqc_table(self):
        fg = FigureGenerator()
        data = {
            "ML-KEM-512": {"q": 3329, "q_mod_60": 29, "q_tier": 1,
                           "q_minus_1_smooth_fraction": 0.0769},
        }
        latex = fg.pqc_parameter_chart(data)
        assert "ML-KEM-512" in latex


class TestTableGenerator:
    def test_smooth_density_table(self):
        tg = TableGenerator()
        tier_rates = {
            0: {"total": 100, "smooth": 100, "rate": 1.0},
            1: {"total": 200, "smooth": 100, "rate": 0.5},
        }
        latex = tg.smooth_density_table(tier_rates)
        assert r"\begin{table}" in latex

    def test_scaling_table(self):
        tg = TableGenerator()
        data = {
            32: {"low_tier_rate": 0.5, "high_tier_rate": 0.2, "advantage_ratio": 2.5},
        }
        latex = tg.scaling_table(data)
        assert "32" in latex
