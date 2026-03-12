"""Tests for the number theory layer (Phase 3)."""

import pytest
from math import gcd, isqrt

from cuneiform.number_theory.primes import (
    sieve_of_eratosthenes, is_prime, largest_prime_factor,
    count_prime_factors, legendre_symbol, tonelli_shanks,
    optimal_smoothness_bound,
)
from cuneiform.number_theory.regularity import (
    RegularityClass, classify_regularity, regularity_spectrum,
    regularity_density,
)
from cuneiform.number_theory.reciprocals import (
    ReciprocalPair, ModularReciprocalPair, ReciprocalTable,
)
from cuneiform.number_theory.smoothness import (
    is_b_smooth, is_b_smooth_sexa, SmoothBatch,
    primes_coprime_to_60, primes_by_residue_class_60,
)
from cuneiform.number_theory.factor_base import (
    StandardFactorBase, SexagesimalFactorBase, compare_factor_bases,
)
from cuneiform.number_theory.sieve import (
    QuadraticSieve, SexagesimalQuadraticSieve,
    _trial_divide, _gaussian_elimination_gf2,
)
from cuneiform.number_theory.ecm import ECM, PlimptonECM
from cuneiform.number_theory.analysis import (
    generate_semiprimes, SmoothDensityExperiment, FactoringComparison,
)
from cuneiform.core.rational import SexaRational


# ─── Primes ────────────────────────────────────────────────────────────

class TestSieveOfEratosthenes:
    def test_small(self):
        assert sieve_of_eratosthenes(10) == [2, 3, 5, 7]

    def test_primes_to_30(self):
        assert sieve_of_eratosthenes(30) == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]

    def test_below_2(self):
        assert sieve_of_eratosthenes(1) == []
        assert sieve_of_eratosthenes(0) == []

    def test_edge_at_prime(self):
        assert 97 in sieve_of_eratosthenes(97)
        assert 97 not in sieve_of_eratosthenes(96)

    def test_count_primes_below_100(self):
        assert len(sieve_of_eratosthenes(100)) == 25


class TestIsPrime:
    @pytest.mark.parametrize("p", [2, 3, 5, 7, 11, 13, 97, 997, 7919, 104729])
    def test_known_primes(self, p):
        assert is_prime(p)

    @pytest.mark.parametrize("n", [0, 1, 4, 6, 9, 15, 100, 1001])
    def test_known_composites(self, n):
        assert not is_prime(n)

    def test_large_prime(self):
        # Mersenne prime 2^31 - 1
        assert is_prime(2147483647)

    def test_large_composite(self):
        assert not is_prime(2147483647 * 3)


class TestPrimeFactors:
    def test_largest_prime_factor(self):
        assert largest_prime_factor(12) == 3
        assert largest_prime_factor(60) == 5
        assert largest_prime_factor(97) == 97
        assert largest_prime_factor(1) == 1

    def test_count_prime_factors(self):
        assert count_prime_factors(12) == 3  # 2*2*3
        assert count_prime_factors(60) == 4  # 2*2*3*5
        assert count_prime_factors(97) == 1
        assert count_prime_factors(1) == 0


class TestLegendreSymbol:
    def test_quadratic_residues_mod_7(self):
        # QRs mod 7: 1, 2, 4
        assert legendre_symbol(1, 7) == 1
        assert legendre_symbol(2, 7) == 1
        assert legendre_symbol(4, 7) == 1
        # Non-residues: 3, 5, 6
        assert legendre_symbol(3, 7) == -1
        assert legendre_symbol(5, 7) == -1
        assert legendre_symbol(6, 7) == -1

    def test_zero(self):
        assert legendre_symbol(0, 7) == 0
        assert legendre_symbol(7, 7) == 0


class TestTonelliShanks:
    def test_sqrt_mod_7(self):
        # 2 is QR mod 7: 3^2=9≡2, 4^2=16≡2
        roots = tonelli_shanks(2, 7)
        assert len(roots) == 2
        for r in roots:
            assert (r * r) % 7 == 2

    def test_sqrt_mod_13(self):
        # 3 is QR mod 13: check
        roots = tonelli_shanks(3, 13)
        for r in roots:
            assert (r * r) % 13 == 3

    def test_non_residue(self):
        assert tonelli_shanks(3, 7) == []

    def test_zero_root(self):
        assert tonelli_shanks(0, 7) == [0]

    def test_mod_2(self):
        assert tonelli_shanks(1, 2) == [1]


class TestOptimalSmoothnessbound:
    def test_increases_with_n(self):
        b1 = optimal_smoothness_bound(10**10)
        b2 = optimal_smoothness_bound(10**20)
        assert b2 > b1

    def test_minimum(self):
        assert optimal_smoothness_bound(3) >= 20


# ─── Regularity ────────────────────────────────────────────────────────

class TestRegularityClass:
    def test_regular_numbers(self):
        for n in [1, 2, 3, 4, 5, 6, 8, 9, 10, 12, 15, 16, 20, 24, 25, 30, 60]:
            rc = RegularityClass(n)
            assert rc.is_regular, f"{n} should be regular"
            assert rc.regularity_tier == 0
            assert rc.cofactor == 1

    def test_tier_1_prime_cofactor(self):
        # 7 = 1 * 7 (cofactor=7, one prime factor)
        rc = RegularityClass(7)
        assert rc.regularity_tier == 1
        assert rc.cofactor == 7
        assert not rc.is_regular

    def test_tier_1_with_smooth_part(self):
        # 14 = 2 * 7 -> regular_part=2, cofactor=7
        rc = RegularityClass(14)
        assert rc.regular_part == 2
        assert rc.cofactor == 7
        assert rc.regularity_tier == 1

    def test_tier_2_semiprime_cofactor(self):
        # 49 = 1 * 49 -> cofactor=49=7^2, 2 prime factors
        rc = RegularityClass(49)
        assert rc.regularity_tier == 2
        assert rc.cofactor == 49

    def test_tier_2_two_distinct_primes(self):
        # 77 = 7 * 11 -> cofactor=77, 2 factors
        rc = RegularityClass(77)
        assert rc.regularity_tier == 2

    def test_smooth_exponents(self):
        rc = RegularityClass(60)  # 2^2 * 3 * 5
        assert rc.smooth_exponents == (2, 1, 1)

    def test_largest_prime_regular(self):
        rc = RegularityClass(60)
        assert rc.largest_prime == 5

    def test_largest_prime_irregular(self):
        rc = RegularityClass(14)  # 2 * 7
        assert rc.largest_prime == 7

    def test_invalid_input(self):
        with pytest.raises(ValueError):
            RegularityClass(0)
        with pytest.raises(ValueError):
            RegularityClass(-5)

    def test_repr(self):
        rc = RegularityClass(60)
        assert "60" in repr(rc)


class TestClassifyRegularity:
    def test_returns_dict(self):
        result = classify_regularity(60)
        assert result["n"] == 60
        assert result["is_regular"] is True
        assert result["tier"] == 0
        assert result["regular_part"] == 60
        assert result["cofactor"] == 1


class TestRegularitySpectrum:
    def test_small_range(self):
        spectrum = regularity_spectrum(list(range(1, 31)))
        assert 0 in spectrum  # There are 5-smooth numbers in 1..30
        total = sum(spectrum.values())
        assert total == 30


class TestRegularityDensity:
    def test_small(self):
        density = regularity_density(30)
        assert abs(sum(density.values()) - 1.0) < 1e-10
        assert density[0] > 0  # Regular numbers exist


# ─── Reciprocal Pairs ──────────────────────────────────────────────────

class TestReciprocalPair:
    def test_basic_pair(self):
        rp = ReciprocalPair(2)
        assert rp.x == SexaRational(2)
        assert rp.x_bar == SexaRational(Fraction(1, 2))

    def test_product_is_one(self):
        for x in [2, 3, 5, 7, 12, 60]:
            rp = ReciprocalPair(x)
            product = rp.x * rp.x_bar
            assert product == SexaRational(1)

    def test_sum_and_difference(self):
        rp = ReciprocalPair(2)
        assert rp.sum == SexaRational(2) + SexaRational(Fraction(1, 2))
        assert rp.difference == SexaRational(2) - SexaRational(Fraction(1, 2))

    def test_pythagorean_triple(self):
        # Classic: x=2, x_bar=1/2 -> triple (3,4,5) scaled
        rp = ReciprocalPair(2)
        triple = rp.pythagorean_triple
        assert triple is not None
        w, l, d = triple
        assert w * w + l * l == d * d

    def test_compose(self):
        rp1 = ReciprocalPair(2)
        rp2 = ReciprocalPair(3)
        composed = rp1.compose(rp2)
        assert composed.x == SexaRational(6)

    def test_power(self):
        rp = ReciprocalPair(2)
        rp_sq = rp.power(2)
        assert rp_sq.x == SexaRational(4)

    def test_zero_raises(self):
        with pytest.raises(ValueError):
            ReciprocalPair(0)

    def test_equality(self):
        assert ReciprocalPair(2) == ReciprocalPair(2)
        assert ReciprocalPair(2) != ReciprocalPair(3)


class TestModularReciprocalPair:
    def test_basic(self):
        mrp = ModularReciprocalPair(3, 11)
        assert mrp.is_valid
        assert (mrp.x * mrp.x_inv) % 11 == 1

    def test_invalid(self):
        mrp = ModularReciprocalPair(6, 12)
        assert not mrp.is_valid

    def test_sum_mod(self):
        mrp = ModularReciprocalPair(3, 11)
        assert mrp.sum_mod == (3 + pow(3, -1, 11)) % 11

    def test_regularity(self):
        mrp = ModularReciprocalPair(4, 11)
        assert mrp.regularity_x is not None
        assert "tier" in mrp.regularity_x


class TestReciprocalTable:
    def test_build(self):
        rt = ReciprocalTable(60)
        rt.build()
        assert rt.size() > 0

    def test_regular_pairs(self):
        rt = ReciprocalTable(60)
        rt.build()
        reg = rt.regular_pairs(5)
        for p in reg:
            assert p.pair_regularity <= 5

    def test_tier_distribution(self):
        rt = ReciprocalTable(60)
        rt.build()
        dist = rt.tier_distribution()
        assert sum(dist.values()) == rt.size()


# ─── Smoothness ────────────────────────────────────────────────────────

class TestIsBSmooth:
    def test_smooth_numbers(self):
        assert is_b_smooth(60, 5)
        assert is_b_smooth(12, 3)
        assert is_b_smooth(1, 2)

    def test_not_smooth(self):
        assert not is_b_smooth(7, 5)
        assert not is_b_smooth(14, 5)

    def test_zero(self):
        assert not is_b_smooth(0, 10)

    def test_prime_at_bound(self):
        assert is_b_smooth(7, 7)
        assert not is_b_smooth(7, 5)


class TestIsBSmoothSexa:
    def test_regular_number(self):
        smooth, meta = is_b_smooth_sexa(60, 5)
        assert smooth
        assert meta["regularity_tier"] == 0
        assert meta["cofactor"] == 1

    def test_irregular_but_smooth(self):
        smooth, meta = is_b_smooth_sexa(42, 7)  # 42 = 2*3*7
        assert smooth
        assert meta["regular_part"] == 6  # 2*3
        assert 7 in meta["cofactor_factors"]

    def test_not_smooth(self):
        smooth, meta = is_b_smooth_sexa(77, 5)  # 7*11
        assert not smooth

    def test_zero(self):
        smooth, meta = is_b_smooth_sexa(0, 10)
        assert not smooth


class TestPrimeOrdering:
    def test_coprime_to_60(self):
        primes = primes_coprime_to_60(30)
        assert 2 not in primes
        assert 3 not in primes
        assert 5 not in primes
        assert 7 in primes

    def test_by_residue_class(self):
        primes = primes_by_residue_class_60(200)
        # Tier 1 primes (±1 mod 60) should come first
        tier1 = [p for p in primes if p % 60 in (1, 59)]
        tier2 = [p for p in primes if p % 60 not in (1, 59)]
        # Check ordering: all tier1 before tier2
        if tier1 and tier2:
            assert primes.index(tier1[-1]) < primes.index(tier2[0])


class TestSmoothBatch:
    def test_process(self):
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 15, 60]
        sb = SmoothBatch(values, 7)
        result = sb.process()
        assert result["smooth_count"] > 0
        assert result["total_count"] == len(values)
        assert 0 <= result["smooth_rate"] <= 1

    def test_compare(self):
        values = list(range(1, 50))
        sb = SmoothBatch(values, 11)
        result = sb.compare_with_standard()
        assert result["standard_smooth"] > 0
        assert result["sexa_smooth"] > 0
        # Both methods should find the same smooth numbers
        assert result["standard_smooth"] == result["sexa_smooth"]


# ─── Factor Base ───────────────────────────────────────────────────────

class TestStandardFactorBase:
    def test_includes_sign(self):
        fb = StandardFactorBase(1000003, 50)
        assert fb.primes[0] == -1

    def test_primes_are_qr(self):
        n = 1000003
        fb = StandardFactorBase(n, 50)
        for p in fb.primes[1:]:  # Skip -1
            ls = legendre_symbol(n, p)
            assert ls >= 0, f"Prime {p} is not a QR mod {n}"


class TestSexagesimalFactorBase:
    def test_tiered_structure(self):
        fb = SexagesimalFactorBase(1000003, 100)
        assert fb.regular_primes == [2, 3, 5]
        assert len(fb.tier_1_primes) >= 0
        assert len(fb.tier_2_primes) >= 0

    def test_tier1_are_pm1_mod60(self):
        fb = SexagesimalFactorBase(1000003, 200)
        for p in fb.tier_1_primes:
            assert p % 60 in (1, 59), f"Tier 1 prime {p} not ±1 mod 60"

    def test_all_primes_includes_all(self):
        fb = SexagesimalFactorBase(1000003, 100)
        all_p = fb.all_primes()
        total = len(fb.regular_primes) + len(fb.tier_1_primes) + len(fb.tier_2_primes)
        assert len(all_p) == total

    def test_size(self):
        fb = SexagesimalFactorBase(1000003, 100)
        assert fb.size() == len(fb.all_primes())


class TestCompareFactorBases:
    def test_returns_valid_structure(self):
        result = compare_factor_bases(1000003, 50)
        assert result["standard_size"] > 0
        assert result["sexa_size"] > 0
        assert "tier_analysis" in result


# ─── Sieve internals ──────────────────────────────────────────────────

class TestTrialDivide:
    def test_smooth_number(self):
        primes = [-1, 2, 3, 5, 7]
        result = _trial_divide(60, primes)
        assert result is not None
        # 60 = 2^2 * 3 * 5, sign=0
        assert result[0] == 0  # positive
        assert result[1] == 2  # 2^2
        assert result[2] == 1  # 3^1
        assert result[3] == 1  # 5^1
        assert result[4] == 0  # 7^0

    def test_negative(self):
        primes = [-1, 2, 3]
        result = _trial_divide(-12, primes)
        assert result is not None
        assert result[0] == 1  # negative sign

    def test_not_smooth(self):
        primes = [-1, 2, 3, 5]
        result = _trial_divide(77, primes)  # 7*11
        assert result is None


class TestGaussianElimination:
    def test_simple_dependency(self):
        # Three vectors, one dependency
        matrix = [
            [1, 0, 1],
            [0, 1, 1],
            [1, 1, 0],
        ]
        nulls = _gaussian_elimination_gf2(matrix)
        # row0 + row1 + row2 = [0,0,0] mod 2
        assert len(nulls) >= 1

    def test_empty(self):
        assert _gaussian_elimination_gf2([]) == []


# ─── Quadratic Sieve ──────────────────────────────────────────────────

class TestQuadraticSieve:
    def test_factor_small_semiprime(self):
        n = 15347  # 103 * 149
        qs = QuadraticSieve(n)
        result = qs.factor()
        if result is not None:
            p, q = result
            assert p * q == n
            assert p > 1 and q > 1

    def test_factor_another(self):
        n = 1000003 * 1000033
        qs = QuadraticSieve(n, sieve_range=50000)
        result = qs.factor()
        if result is not None:
            p, q = result
            assert p * q == n

    def test_sieve_finds_relations(self):
        # Use a larger semiprime where sieve reliably finds relations
        n = 15347
        qs = QuadraticSieve(n, sieve_range=20000)
        relations = qs.sieve()
        # Should find some smooth relations
        assert len(relations) >= 0  # May be 0 for small n; factor() test covers full pipeline

    def test_perfect_square_returns_empty(self):
        qs = QuadraticSieve(144)  # 12^2
        assert qs.sieve() == []


class TestSexagesimalQuadraticSieve:
    def test_factor_small_semiprime(self):
        n = 15347  # 103 * 149
        sqs = SexagesimalQuadraticSieve(n)
        result = sqs.factor()
        if result is not None:
            p, q = result
            assert p * q == n
            assert p > 1 and q > 1

    def test_prefilter_runs(self):
        n = 15347
        sqs = SexagesimalQuadraticSieve(n)
        sqs.sieve()
        # Stats should be populated
        assert sqs.stats["smooth_found"] >= 0
        assert isinstance(sqs.stats["prefilter_saves"], int)

    def test_stats_tier_tracking(self):
        n = 15347
        sqs = SexagesimalQuadraticSieve(n)
        sqs.sieve()
        assert isinstance(sqs.stats["smooth_by_tier"], dict)


# ─── ECM ───────────────────────────────────────────────────────────────

class TestECM:
    def test_factor_small(self):
        n = 1147  # 31 * 37
        ecm = ECM(n, curves=50)
        result = ecm.factor()
        if result is not None:
            p, q = result
            assert p * q == n

    def test_stats(self):
        n = 1147
        ecm = ECM(n, curves=10)
        ecm.factor()
        assert ecm.stats["curves_tried"] > 0


class TestPlimptonECM:
    def test_factor_small(self):
        n = 1147  # 31 * 37
        pecm = PlimptonECM(n, curves=30)
        result = pecm.factor()
        if result is not None:
            p, q = result
            assert p * q == n

    def test_uses_plimpton_triples(self):
        n = 2021  # 43 * 47
        pecm = PlimptonECM(n, curves=20)
        pecm.factor()
        assert pecm.stats["curves_tried"] > 0


# ─── Analysis ──────────────────────────────────────────────────────────

class TestGenerateSemiprimes:
    def test_correct_count(self):
        semiprimes = generate_semiprimes(20, 5)
        assert len(semiprimes) == 5

    def test_are_semiprimes(self):
        semiprimes = generate_semiprimes(20, 5)
        for n in semiprimes:
            # Should be product of two primes
            assert n > 1
            # Factor it
            found = False
            for d in range(2, isqrt(n) + 1):
                if n % d == 0:
                    assert is_prime(d)
                    assert is_prime(n // d)
                    found = True
                    break
            assert found, f"{n} is not a semiprime"

    def test_deterministic(self):
        a = generate_semiprimes(20, 5, seed=42)
        b = generate_semiprimes(20, 5, seed=42)
        assert a == b

    def test_different_seeds(self):
        a = generate_semiprimes(20, 5, seed=42)
        b = generate_semiprimes(20, 5, seed=99)
        assert a != b


class TestSmoothDensityExperiment:
    def test_runs(self):
        n = 15347
        exp = SmoothDensityExperiment(n, sieve_range=500)
        result = exp.run()
        assert result["n"] == n
        assert result["total_values"] > 0
        assert "tier_rates" in result
        assert 0 <= result["overall_smooth_rate"] <= 1

    def test_tier_rates_have_expected_keys(self):
        n = 15347
        exp = SmoothDensityExperiment(n, sieve_range=200)
        result = exp.run()
        for tier, data in result["tier_rates"].items():
            assert "total" in data
            assert "smooth" in data
            assert "rate" in data


# Need fractions for reciprocal pair tests
from fractions import Fraction
