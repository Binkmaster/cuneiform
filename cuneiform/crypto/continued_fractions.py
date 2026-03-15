"""Continued fraction analysis with sexagesimal awareness.

CFs are used in Wiener's attack on RSA, lattice reduction,
and Diophantine approximation. The Stern-Brocot tree organizes
all positive rationals; the 5-smooth subtree has special structure.
"""

from __future__ import annotations

from fractions import Fraction
from cuneiform.core.accel import gcd

from cuneiform.core.smooth import is_smooth, generate_smooth_numbers


def cf_expansion(p: int, q: int, max_terms: int = 100) -> list[int]:
    """Standard continued fraction expansion of p/q."""
    terms = []
    while q != 0 and len(terms) < max_terms:
        a = p // q
        terms.append(a)
        p, q = q, p - a * q
    return terms


def cf_convergents(terms: list[int]) -> list[tuple[int, int]]:
    """Compute convergents h_k/k_k from CF terms."""
    convergents = []
    h_prev, h_curr = 0, 1
    k_prev, k_curr = 1, 0

    for a in terms:
        h_prev, h_curr = h_curr, a * h_curr + h_prev
        k_prev, k_curr = k_curr, a * k_curr + k_prev
        if k_curr > 0:
            convergents.append((h_curr, k_curr))

    return convergents


def _nearest_smooth_quick(n: int) -> int:
    """Find nearest 5-smooth number to n (fast heuristic)."""
    if n <= 1:
        return 1
    if is_smooth(n):
        return n

    best = 1
    best_dist = abs(n - 1)

    # Generate 5-smooth numbers near n
    limit = n * 3
    a = 1
    while a <= limit:
        b = a
        while b <= limit:
            c = b
            while c <= limit:
                d = abs(c - n)
                if d < best_dist:
                    best = c
                    best_dist = d
                c *= 5
            b *= 3
        a *= 2

    return best


class SexagesimalContinuedFractions:
    """CF analysis with sexagesimal awareness."""

    def sexagesimal_cf_expansion(self, p: int, q: int,
                                  max_terms: int = 100) -> list[int]:
        """CF expansion where quotients are rounded to nearest 5-smooth.

        This produces different convergents that may approach the true
        value faster for fractions related to 5-smooth numbers.
        """
        terms = []
        while q != 0 and len(terms) < max_terms:
            a = p // q
            if a > 0:
                a_smooth = _nearest_smooth_quick(a)
            else:
                a_smooth = 0

            terms.append(a_smooth)
            r = p - a_smooth * q
            if r < 0:
                # Fall back to standard quotient
                terms[-1] = a
                r = p - a * q
            p, q = q, abs(r)

        return terms

    def convergent_quality_comparison(self, target_p: int,
                                       target_q: int) -> dict:
        """Compare standard vs sexagesimal CF convergent quality.

        Measures approximation error and denominator size.
        """
        target = Fraction(target_p, target_q)

        # Standard CF
        std_terms = cf_expansion(target_p, target_q)
        std_convs = cf_convergents(std_terms)

        # Sexagesimal CF
        sexa_terms = self.sexagesimal_cf_expansion(target_p, target_q)
        sexa_convs = cf_convergents(sexa_terms)

        def quality_metrics(convs):
            metrics = []
            for h, k in convs:
                if k == 0:
                    continue
                error = abs(target - Fraction(h, k))
                quality = float(Fraction(k) * error) if error > 0 else 0
                metrics.append({
                    "h": h, "k": k,
                    "error": float(error),
                    "quality": float(quality),
                })
            return metrics

        std_metrics = quality_metrics(std_convs)
        sexa_metrics = quality_metrics(sexa_convs)

        # Compare: for same number of convergents, which has lower error?
        min_len = min(len(std_metrics), len(sexa_metrics))
        sexa_better = 0
        std_better = 0
        for i in range(min_len):
            if sexa_metrics[i]["error"] < std_metrics[i]["error"]:
                sexa_better += 1
            elif std_metrics[i]["error"] < sexa_metrics[i]["error"]:
                std_better += 1

        return {
            "target": f"{target_p}/{target_q}",
            "standard_terms": len(std_terms),
            "sexagesimal_terms": len(sexa_terms),
            "standard_convergents": len(std_convs),
            "sexagesimal_convergents": len(sexa_convs),
            "sexa_better_count": sexa_better,
            "std_better_count": std_better,
            "standard_metrics": std_metrics[:10],
            "sexagesimal_metrics": sexa_metrics[:10],
        }

    def stern_brocot_smooth_subtree(self, depth: int = 8) -> dict:
        """Analyze the 5-smooth subtree of the Stern-Brocot tree.

        The Stern-Brocot tree organizes all positive rationals.
        We identify nodes where both numerator and denominator are 5-smooth.
        """
        # Build tree level by level
        # Each node is a fraction h/k between left and right parents
        smooth_nodes = []
        total_nodes = 0

        # Start with 0/1 and 1/0 as sentinels
        # Level 0: 1/1
        queue = [(0, 1, 1, 0, 1, 1)]  # (lh, lk, rh, rk, h, k)
        level_stats: dict[int, dict] = {}

        for d in range(depth):
            next_queue = []
            level_smooth = 0
            level_total = 0

            for lh, lk, rh, rk, h, k in queue:
                level_total += 1
                total_nodes += 1

                if is_smooth(h) and is_smooth(k):
                    smooth_nodes.append((h, k, d))
                    level_smooth += 1

                # Left child: mediant of (lh/lk, h/k)
                lc_h, lc_k = lh + h, lk + k
                # Right child: mediant of (h/k, rh/rk)
                rc_h, rc_k = h + rh, k + rk

                if d < depth - 1:
                    next_queue.append((lh, lk, h, k, lc_h, lc_k))
                    next_queue.append((h, k, rh, rk, rc_h, rc_k))

            level_stats[d] = {
                "total": level_total,
                "smooth": level_smooth,
                "smooth_fraction": level_smooth / level_total if level_total > 0 else 0,
            }
            queue = next_queue

        return {
            "depth": depth,
            "total_nodes": total_nodes,
            "smooth_nodes": len(smooth_nodes),
            "overall_smooth_fraction": len(smooth_nodes) / total_nodes if total_nodes > 0 else 0,
            "level_stats": level_stats,
            "sample_smooth_fractions": [
                f"{h}/{k}" for h, k, _ in smooth_nodes[:20]
            ],
        }

    def wiener_attack_enhanced(self, n: int, e: int) -> dict:
        """Wiener's attack: compare standard vs sexagesimal CF convergents.

        Standard: expand e/n as CF, check if convergent k/d gives valid RSA key.
        Enhanced: try sexagesimal convergents too.
        """
        def check_convergent(k, d, n, e):
            """Check if d is the RSA private key."""
            if d == 0 or k == 0:
                return False
            # phi_n = (e*d - 1) / k
            ed_minus_1 = e * d - 1
            if ed_minus_1 % k != 0:
                return False
            phi_n = ed_minus_1 // k
            # n - phi_n + 1 = p + q
            s = n - phi_n + 1
            # p, q are roots of x^2 - s*x + n = 0
            disc = s * s - 4 * n
            if disc < 0:
                return False
            from math import isqrt
            sqrt_disc = isqrt(disc)
            if sqrt_disc * sqrt_disc != disc:
                return False
            p = (s + sqrt_disc) // 2
            q = (s - sqrt_disc) // 2
            return p * q == n and p > 1 and q > 1

        # Standard CF convergents
        std_terms = cf_expansion(e, n)
        std_convs = cf_convergents(std_terms)
        std_found = None
        for i, (k, d) in enumerate(std_convs):
            if check_convergent(k, d, n, e):
                std_found = {"index": i, "k": k, "d": d}
                break

        # Sexagesimal CF convergents
        sexa_terms = self.sexagesimal_cf_expansion(e, n)
        sexa_convs = cf_convergents(sexa_terms)
        sexa_found = None
        for i, (k, d) in enumerate(sexa_convs):
            if check_convergent(k, d, n, e):
                sexa_found = {"index": i, "k": k, "d": d}
                break

        return {
            "n_bits": n.bit_length(),
            "standard_found": std_found is not None,
            "standard_result": std_found,
            "standard_convergents_checked": len(std_convs),
            "sexagesimal_found": sexa_found is not None,
            "sexagesimal_result": sexa_found,
            "sexagesimal_convergents_checked": len(sexa_convs),
        }
