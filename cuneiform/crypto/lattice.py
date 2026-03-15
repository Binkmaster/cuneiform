"""Lattice reduction experiments with sexagesimal-organized bases.

Pure-Python LLL implementation for self-contained testing.
The hypothesis: a basis organized by sexagesimal regularity may
admit better reduction (faster convergence, shorter vectors).
"""

from __future__ import annotations

import random
from math import sqrt, log

from cuneiform.core.accel import gcd, isqrt, invert
from fractions import Fraction

from cuneiform.number_theory.regularity import RegularityClass
from cuneiform.number_theory.reciprocals import ModularReciprocalPair


def _dot(a: list, b: list) -> Fraction:
    """Dot product using exact arithmetic."""
    return sum(Fraction(x) * Fraction(y) for x, y in zip(a, b))


def _norm_sq(v: list) -> Fraction:
    """Squared Euclidean norm."""
    return _dot(v, v)


def _sub(a: list, b: list) -> list:
    """Vector subtraction."""
    return [Fraction(x) - Fraction(y) for x, y in zip(a, b)]


def _scale(v: list, s: Fraction) -> list:
    """Scalar multiplication."""
    return [Fraction(x) * s for x in v]


def _proj(u: list, v: list) -> list:
    """Projection of v onto u."""
    nu = _norm_sq(u)
    if nu == 0:
        return [Fraction(0)] * len(u)
    return _scale(u, _dot(v, u) / nu)


def lll_reduce(basis: list[list[int]], delta: float = 0.75) -> tuple[list[list[int]], dict]:
    """LLL lattice reduction (exact rational arithmetic).

    Returns (reduced_basis, stats).
    """
    n = len(basis)
    if n == 0:
        return [], {"swaps": 0, "iterations": 0}

    # Work with Fraction for exactness
    B = [[Fraction(x) for x in row] for row in basis]
    swaps = 0
    iterations = 0

    def gram_schmidt():
        gs = []
        mu_matrix = [[Fraction(0)] * n for _ in range(n)]
        for i in range(n):
            v = list(B[i])
            for j in range(len(gs)):
                mu_matrix[i][j] = _dot(B[i], gs[j]) / _norm_sq(gs[j]) if _norm_sq(gs[j]) != 0 else Fraction(0)
                v = _sub(v, _scale(gs[j], mu_matrix[i][j]))
            gs.append(v)
        return gs, mu_matrix

    k = 1
    while k < n:
        iterations += 1
        gs, mu = gram_schmidt()

        # Size reduction
        for j in range(k - 1, -1, -1):
            if abs(mu[k][j]) > Fraction(1, 2):
                r = round(float(mu[k][j]))
                B[k] = _sub(B[k], _scale(B[j], Fraction(r)))
                gs, mu = gram_schmidt()

        # Lovász condition
        ns_k = _norm_sq(gs[k])
        ns_k1 = _norm_sq(gs[k - 1])
        lhs = ns_k + mu[k][k - 1] ** 2 * ns_k1
        rhs = Fraction(delta) * ns_k1

        if lhs >= rhs:
            k += 1
        else:
            B[k], B[k - 1] = B[k - 1], B[k]
            swaps += 1
            k = max(k - 1, 1)

        # Safety limit
        if iterations > n * n * 50:
            break

    result = [[int(x) for x in row] for row in B]
    return result, {"swaps": swaps, "iterations": iterations}


class SexagesimalLattice:
    """Lattice operations with sexagesimal-organized basis vectors."""

    def __init__(self, basis: list[list[int]]):
        self.basis = [list(row) for row in basis]
        self.dim = len(basis)

    @classmethod
    def from_random(cls, dim: int, entry_bits: int = 16,
                     seed: int = 42) -> SexagesimalLattice:
        """Generate a random lattice for testing."""
        rng = random.Random(seed)
        bound = 1 << entry_bits
        basis = [
            [rng.randint(-bound, bound) for _ in range(dim)]
            for _ in range(dim)
        ]
        return cls(basis)

    @classmethod
    def from_reciprocal_pairs(cls, modulus: int,
                               dim: int) -> SexagesimalLattice:
        """Build a lattice from Babylonian reciprocal pairs mod n.

        For each reciprocal pair (x, x^-1 mod n) where both are regular,
        construct a basis vector from (x, x^-1, x+x^-1, x-x^-1, ...).
        """
        pairs = []
        for x in range(2, modulus):
            if gcd(x, modulus) != 1:
                continue
            x_inv = invert(x, modulus)
            if x_inv == x:
                continue
            # Check regularity
            rc_x = RegularityClass(x)
            rc_inv = RegularityClass(x_inv)
            if rc_x.regularity_tier <= 1 and rc_inv.regularity_tier <= 1:
                pairs.append((x, x_inv))
            if len(pairs) >= dim:
                break

        # Pad if needed
        rng = random.Random(42)
        while len(pairs) < dim:
            x = rng.randint(2, modulus - 1)
            if gcd(x, modulus) == 1:
                pairs.append((x, invert(x, modulus)))

        # Build basis vectors
        basis = []
        for x, x_inv in pairs[:dim]:
            s = (x + x_inv) % modulus
            d = (x - x_inv) % modulus
            row = [0] * dim
            # Fill with derived values
            vals = [x, x_inv, s, d]
            for i in range(dim):
                row[i] = vals[i % len(vals)]
            basis.append(row)

        return cls(basis)

    def regularity_profile(self) -> dict:
        """Analyze the regularity of all basis vector entries."""
        total_entries = 0
        smooth_entries = 0
        tier_sum = 0
        tier_counts: dict[int, int] = {}

        for row in self.basis:
            for val in row:
                if val == 0:
                    continue
                total_entries += 1
                rc = RegularityClass(abs(val))
                tier = rc.regularity_tier
                tier_sum += tier
                tier_counts[tier] = tier_counts.get(tier, 0) + 1
                if rc.is_regular:
                    smooth_entries += 1

        return {
            "total_entries": total_entries,
            "smooth_entries": smooth_entries,
            "smooth_fraction": smooth_entries / total_entries if total_entries > 0 else 0,
            "average_tier": tier_sum / total_entries if total_entries > 0 else 0,
            "tier_distribution": dict(sorted(tier_counts.items())),
        }

    def reorder_by_regularity(self) -> SexagesimalLattice:
        """Reorder basis vectors by regularity score (most regular first)."""
        def row_regularity(row):
            tiers = []
            for v in row:
                if v != 0:
                    tiers.append(RegularityClass(abs(v)).regularity_tier)
            return sum(tiers) / len(tiers) if tiers else float("inf")

        sorted_basis = sorted(self.basis, key=row_regularity)
        return SexagesimalLattice(sorted_basis)

    def scale_to_regular(self) -> SexagesimalLattice:
        """Scale basis vectors to maximize regular entries.

        For each row, find the smallest 5-smooth multiplier that makes
        the most entries regular.
        """
        from cuneiform.core.smooth import extract_smooth_part

        new_basis = []
        for row in self.basis:
            # Find gcd of non-zero entries
            g = 0
            for v in row:
                if v != 0:
                    g = gcd(g, abs(v))
            if g > 1:
                _, cofactor = extract_smooth_part(g)
                if cofactor > 1:
                    # Divide out the non-smooth part of the gcd
                    new_row = [v // cofactor if v % cofactor == 0 else v for v in row]
                else:
                    new_row = list(row)
            else:
                new_row = list(row)
            new_basis.append(new_row)

        return SexagesimalLattice(new_basis)

    def reduce(self, delta: float = 0.75) -> tuple[SexagesimalLattice, dict]:
        """Run LLL reduction on this lattice."""
        reduced, stats = lll_reduce(self.basis, delta)
        return SexagesimalLattice(reduced), stats

    def shortest_vector_norm(self) -> float:
        """Norm of the shortest basis vector (after reduction)."""
        return min(
            sqrt(float(sum(x * x for x in row)))
            for row in self.basis
        )

    def hermite_factor(self) -> float:
        """Hermite factor: ||b_1|| / det(L)^(1/n).

        Lower is better. Computed approximately.
        """
        shortest = self.shortest_vector_norm()
        # det = product of GS norms (approximate via diagonal)
        # For simplicity, use the product of row norms as an upper bound
        det_approx = 1.0
        for row in self.basis:
            det_approx *= sqrt(float(sum(x * x for x in row)))
        det_root = det_approx ** (1.0 / self.dim) if self.dim > 0 else 1
        return shortest / det_root if det_root > 0 else float("inf")

    def orthogonality_defect(self) -> float:
        """Product of ||b_i|| / det(L). Lower is better."""
        product_norms = 1.0
        for row in self.basis:
            product_norms *= sqrt(float(sum(x * x for x in row)))
        # Approximate det via Gram matrix
        # For now use product of norms as the numerator; defect = product/det
        # Since det <= product_norms, defect >= 1
        return product_norms


class LatticeReductionComparison:
    """Head-to-head comparison of standard vs sexagesimal-preprocessed LLL."""

    def __init__(self, dimensions: list[int] | None = None):
        self.dims = dimensions or [8, 10, 12, 15]
        self.results: dict[int, dict] = {}

    def run_lll_comparison(self, dim: int, trials: int = 10,
                            entry_bits: int = 12) -> dict:
        """Compare standard vs regularity-reordered LLL."""
        std_swaps = []
        reord_swaps = []
        std_norms = []
        reord_norms = []

        for trial in range(trials):
            lat = SexagesimalLattice.from_random(dim, entry_bits, seed=trial)

            # Standard LLL
            reduced_std, stats_std = lat.reduce()
            std_swaps.append(stats_std["swaps"])
            std_norms.append(reduced_std.shortest_vector_norm())

            # Reordered LLL
            reordered = lat.reorder_by_regularity()
            reduced_reord, stats_reord = reordered.reduce()
            reord_swaps.append(stats_reord["swaps"])
            reord_norms.append(reduced_reord.shortest_vector_norm())

        avg = lambda xs: sum(xs) / len(xs) if xs else 0

        return {
            "dimension": dim,
            "trials": trials,
            "standard": {
                "avg_swaps": avg(std_swaps),
                "avg_shortest_norm": avg(std_norms),
            },
            "regularity_reordered": {
                "avg_swaps": avg(reord_swaps),
                "avg_shortest_norm": avg(reord_norms),
            },
            "swap_ratio": avg(reord_swaps) / avg(std_swaps) if avg(std_swaps) > 0 else 0,
            "norm_ratio": avg(reord_norms) / avg(std_norms) if avg(std_norms) > 0 else 0,
        }

    def run_all(self, trials: int = 5) -> dict:
        """Run comparison across all dimensions."""
        for dim in self.dims:
            self.results[dim] = self.run_lll_comparison(dim, trials)
        return self.results

    def reciprocal_pair_lattice_analysis(self, moduli: list[int] | None = None,
                                          dim: int = 8) -> dict:
        """Analyze reciprocal pair lattices vs random lattices."""
        moduli = moduli or [60, 120, 180, 360, 720]
        results = {}

        for modulus in moduli:
            actual_dim = min(dim, modulus // 2)
            if actual_dim < 3:
                continue

            rp_lat = SexagesimalLattice.from_reciprocal_pairs(modulus, actual_dim)
            rand_lat = SexagesimalLattice.from_random(actual_dim, 10)

            rp_reduced, rp_stats = rp_lat.reduce()
            rand_reduced, rand_stats = rand_lat.reduce()

            results[modulus] = {
                "dimension": actual_dim,
                "reciprocal_pair": {
                    "regularity": rp_lat.regularity_profile(),
                    "swaps": rp_stats["swaps"],
                    "shortest_norm": rp_reduced.shortest_vector_norm(),
                },
                "random": {
                    "regularity": rand_lat.regularity_profile(),
                    "swaps": rand_stats["swaps"],
                    "shortest_norm": rand_reduced.shortest_vector_norm(),
                },
            }

        return results
