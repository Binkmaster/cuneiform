"""RSA parameter analysis through the sexagesimal lens.

Analyzes the structure of RSA parameters — not trying to factor them,
but looking for regularity patterns that characterize the problem space.
"""

from __future__ import annotations

import random
from math import log

from cuneiform.core.accel import gcd, isqrt

from cuneiform.number_theory.primes import is_prime, optimal_smoothness_bound
from cuneiform.number_theory.regularity import RegularityClass, classify_regularity
from cuneiform.number_theory.smoothness import is_b_smooth
from cuneiform.number_theory.analysis import generate_semiprimes


# Known RSA challenge factorizations (small ones for analysis)
_RSA_CHALLENGES = {
    "RSA-59": {
        "n": 71641520761751435455133616475667090434063332228247871795429,
        "p": 857504083339712752489993810777,
        "q": 83547839397735738685817975613,
    },
    "RSA-100": {
        "n": 1522605027922533360535618378132637429718068114961380688657908494580122963258952897654000350692006139,
        "p": 37975227936943673922808872755445627854565536638199,
        "q": 40094690950920881030683735292761468389214899724061,
    },
}


class RSAAnalysis:
    """Analyze RSA moduli through the sexagesimal lens."""

    def __init__(self):
        self.known_factorizations = dict(_RSA_CHALLENGES)

    def analyze_factored_rsa(self) -> dict:
        """For each factored RSA challenge, classify by regularity."""
        results = {}
        for name, data in self.known_factorizations.items():
            n, p, q = data["n"], data["p"], data["q"]
            phi_n = (p - 1) * (q - 1)

            rc_n = RegularityClass(n)
            rc_p = RegularityClass(p)
            rc_q = RegularityClass(q)
            rc_p1 = RegularityClass(p - 1)
            rc_q1 = RegularityClass(q - 1)
            rc_phi = RegularityClass(phi_n)

            results[name] = {
                "n_bits": n.bit_length(),
                "n_tier": rc_n.regularity_tier,
                "n_cofactor": rc_n.cofactor,
                "p_tier": rc_p.regularity_tier,
                "q_tier": rc_q.regularity_tier,
                "p_minus_1_tier": rc_p1.regularity_tier,
                "q_minus_1_tier": rc_q1.regularity_tier,
                "p_minus_1_smooth_part": rc_p1.regular_part,
                "q_minus_1_smooth_part": rc_q1.regular_part,
                "phi_n_tier": rc_phi.regularity_tier,
                "phi_n_smooth_part": rc_phi.regular_part,
                "n_mod_60": n % 60,
                "p_mod_60": p % 60,
                "q_mod_60": q % 60,
            }

        return results

    def phi_n_regularity(self, p: int, q: int) -> dict:
        """Analyze the regularity structure of phi(n) = (p-1)(q-1).

        If phi(n) has large 5-smooth factors, certain attacks (Pollard p-1)
        become easier. Does the regularity of n correlate with regularity
        of phi(n)?
        """
        n = p * q
        phi_n = (p - 1) * (q - 1)

        rc_n = RegularityClass(n)
        rc_phi = RegularityClass(phi_n)
        rc_p1 = RegularityClass(p - 1)
        rc_q1 = RegularityClass(q - 1)

        return {
            "n": n,
            "n_tier": rc_n.regularity_tier,
            "phi_n": phi_n,
            "phi_n_tier": rc_phi.regularity_tier,
            "phi_n_smooth_fraction": rc_phi.regular_part / phi_n,
            "p_minus_1_smooth_fraction": rc_p1.regular_part / (p - 1),
            "q_minus_1_smooth_fraction": rc_q1.regular_part / (q - 1),
            "pollard_p1_vulnerable": (
                rc_p1.regularity_tier <= 2 or rc_q1.regularity_tier <= 2
            ),
        }

    def public_exponent_interaction(self, n: int, e: int = 65537) -> dict:
        """Analyze interaction between public exponent e and n in
        sexagesimal representation."""
        rc_e = RegularityClass(e)
        rc_n = RegularityClass(n)

        # e^k mod n for small k
        powers = {}
        for k in range(1, 11):
            ek = pow(e, k, n)
            rc_ek = RegularityClass(ek)
            powers[k] = {
                "value_mod_60": ek % 60,
                "tier": rc_ek.regularity_tier,
            }

        return {
            "e": e,
            "e_mod_60": e % 60,
            "e_tier": rc_e.regularity_tier,
            "n_mod_60": n % 60,
            "n_tier": rc_n.regularity_tier,
            "power_tiers": powers,
        }

    def wiener_attack_enhancement(self, n: int, e: int) -> dict:
        """Wiener's attack using standard vs sexagesimal CF convergents.

        Standard Wiener: expand e/n as CF, check convergents for d.
        """
        # Standard continued fraction expansion of e/n
        std_convergents = _cf_convergents(e, n)

        # Sexagesimal CF: round quotients to nearest 5-smooth
        sexa_convergents = _sexa_cf_convergents(e, n)

        return {
            "n_bits": n.bit_length(),
            "standard_convergents": len(std_convergents),
            "sexagesimal_convergents": len(sexa_convergents),
            "standard_first_10": std_convergents[:10],
            "sexagesimal_first_10": sexa_convergents[:10],
        }

    def batch_generate_and_classify(self, bits: int = 40,
                                     count: int = 50) -> dict:
        """Generate many RSA moduli and build a statistical profile
        of their sexagesimal properties."""
        semiprimes = generate_semiprimes(bits, count)
        tier_dist: dict[int, int] = {}
        mod60_dist: dict[int, int] = {}

        for n in semiprimes:
            rc = RegularityClass(n)
            tier = rc.regularity_tier
            tier_dist[tier] = tier_dist.get(tier, 0) + 1
            r = n % 60
            mod60_dist[r] = mod60_dist.get(r, 0) + 1

        return {
            "bits": bits,
            "count": count,
            "tier_distribution": dict(sorted(tier_dist.items())),
            "mod60_distribution": dict(sorted(mod60_dist.items())),
            "avg_tier": sum(
                RegularityClass(n).regularity_tier for n in semiprimes
            ) / len(semiprimes),
        }


def _cf_convergents(a: int, b: int, max_terms: int = 50) -> list[tuple[int, int]]:
    """Standard continued fraction convergents of a/b."""
    convergents = []
    h_prev, h_curr = 0, 1
    k_prev, k_curr = 1, 0

    while b != 0 and len(convergents) < max_terms:
        q = a // b
        a, b = b, a - q * b
        h_prev, h_curr = h_curr, q * h_curr + h_prev
        k_prev, k_curr = k_curr, q * k_curr + k_prev
        if k_curr > 0:
            convergents.append((h_curr, k_curr))

    return convergents


def _nearest_smooth(n: int) -> int:
    """Find the nearest 5-smooth number to n."""
    if n <= 1:
        return 1
    # Generate 5-smooth numbers up to 2*n and find closest
    smooths = []
    limit = max(n * 2, 60)
    a = 1
    while a <= limit:
        b = a
        while b <= limit:
            c = b
            while c <= limit:
                smooths.append(c)
                c *= 5
            b *= 3
        a *= 2
    if not smooths:
        return 1
    return min(smooths, key=lambda s: abs(s - n))


def _sexa_cf_convergents(a: int, b: int,
                          max_terms: int = 50) -> list[tuple[int, int]]:
    """Sexagesimal continued fraction: round quotients to nearest 5-smooth."""
    convergents = []
    h_prev, h_curr = 0, 1
    k_prev, k_curr = 1, 0

    while b != 0 and len(convergents) < max_terms:
        q = a // b
        q_smooth = _nearest_smooth(q) if q > 0 else 0
        # Use the smooth approximation
        r = a - q_smooth * b
        if r < 0:
            # Fall back to standard quotient if smooth overshoots
            q_smooth = q
            r = a - q * b
        a, b = b, abs(r)
        h_prev, h_curr = h_curr, q_smooth * h_curr + h_prev
        k_prev, k_curr = k_curr, q_smooth * k_curr + k_prev
        if k_curr > 0:
            convergents.append((h_curr, k_curr))

    return convergents
