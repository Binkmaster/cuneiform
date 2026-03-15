"""Elliptic curve point regularity analysis.

Analyzes how rational points on elliptic curves over finite fields
relate to 5-smooth structure. Tests correlation between curve parameter
regularity and group order smoothness.
"""

from __future__ import annotations

import random
from cuneiform.core.accel import gcd, isqrt, invert

from cuneiform.number_theory.primes import is_prime, sieve_of_eratosthenes
from cuneiform.number_theory.regularity import RegularityClass
from cuneiform.number_theory.smoothness import is_b_smooth


def _random_prime(bits: int, rng: random.Random) -> int:
    """Generate a random prime of given bit size."""
    while True:
        n = rng.getrandbits(bits) | (1 << (bits - 1)) | 1
        if is_prime(n):
            return n


def _ec_add_fp(P: tuple, Q: tuple, a: int, p: int) -> tuple:
    """Add two points on y^2 = x^3 + ax + b over F_p."""
    if P == (0, 0):
        return Q
    if Q == (0, 0):
        return P

    x1, y1 = P
    x2, y2 = Q

    if x1 == x2:
        if (y1 + y2) % p == 0:
            return (0, 0)
        lam = ((3 * x1 * x1 + a) * invert(2 * y1, p)) % p
    else:
        lam = ((y2 - y1) * invert(x2 - x1, p)) % p

    x3 = (lam * lam - x1 - x2) % p
    y3 = (lam * (x1 - x3) - y1) % p
    return (x3, y3)


def _ec_mul_fp(k: int, P: tuple, a: int, p: int) -> tuple:
    """Scalar multiplication k*P on curve over F_p."""
    if k == 0:
        return (0, 0)
    result = (0, 0)
    current = P
    while k > 0:
        if k & 1:
            result = _ec_add_fp(result, current, a, p)
        current = _ec_add_fp(current, current, a, p)
        k >>= 1
    return result


def _count_points_naive(a: int, b: int, p: int) -> int:
    """Count points on y^2 = x^3 + ax + b over F_p (naive, for small p)."""
    count = 1  # point at infinity
    for x in range(p):
        rhs = (x * x * x + a * x + b) % p
        if rhs == 0:
            count += 1
        else:
            # Check if rhs is a QR mod p
            ls = pow(rhs, (p - 1) // 2, p)
            if ls == 1:
                count += 2
    return count


def _count_points_bsgs(a: int, b: int, p: int) -> int:
    """Baby-step giant-step point counting for medium-sized primes.

    Uses Hasse's theorem: |#E - (p+1)| <= 2*sqrt(p).
    """
    if p < 1000:
        return _count_points_naive(a, b, p)

    # For larger p, use naive for now (Schoof would be ideal but complex)
    # We limit to p < 2^20 for feasibility
    if p > (1 << 20):
        # Approximate using random sampling
        return _count_points_sample(a, b, p)

    return _count_points_naive(a, b, p)


def _count_points_sample(a: int, b: int, p: int, samples: int = 2000) -> int:
    """Estimate point count by sampling."""
    rng = random.Random(42)
    qr_count = 0
    zero_count = 0

    for _ in range(samples):
        x = rng.randint(0, p - 1)
        rhs = (x * x * x + a * x + b) % p
        if rhs == 0:
            zero_count += 1
        else:
            ls = pow(rhs, (p - 1) // 2, p)
            if ls == 1:
                qr_count += 1

    # Extrapolate: each QR gives 2 points, each zero gives 1
    est_per_x = (2 * qr_count + zero_count) / samples
    return 1 + round(est_per_x * p)  # +1 for infinity


class EllipticCurveRegularityAnalysis:
    """Analyze elliptic curves over finite fields through regularity."""

    def __init__(self, field_size_bits: int = 16):
        self.bits = field_size_bits

    def group_order_regularity_correlation(self,
                                            num_curves: int = 200) -> dict:
        """The main experiment: does parameter regularity correlate
        with group order smoothness?

        For random curves E: y^2 = x^3 + ax + b over F_p:
        1. Compute #E(F_p) (group order)
        2. Classify a, b by regularity
        3. Classify #E(F_p) by regularity
        4. Measure correlation
        """
        rng = random.Random(42)
        results = []

        for _ in range(num_curves):
            p = _random_prime(self.bits, rng)
            a = rng.randint(1, p - 1)
            b = rng.randint(1, p - 1)
            if (4 * a ** 3 + 27 * b ** 2) % p == 0:
                continue  # Singular

            order = _count_points_bsgs(a, b, p)
            if order <= 1:
                continue

            rc_a = RegularityClass(a)
            rc_b = RegularityClass(b)
            rc_order = RegularityClass(order)

            results.append({
                "p": p,
                "a": a,
                "b": b,
                "order": order,
                "a_tier": rc_a.regularity_tier,
                "b_tier": rc_b.regularity_tier,
                "ab_combined_tier": rc_a.regularity_tier + rc_b.regularity_tier,
                "order_tier": rc_order.regularity_tier,
                "order_smooth_fraction": rc_order.regular_part / order,
            })

        if not results:
            return {"error": "No valid curves generated"}

        # Compute correlation between parameter regularity and order regularity
        low_param_orders = [
            r["order_tier"] for r in results if r["ab_combined_tier"] <= 2
        ]
        high_param_orders = [
            r["order_tier"] for r in results if r["ab_combined_tier"] > 4
        ]

        avg = lambda xs: sum(xs) / len(xs) if xs else 0

        return {
            "total_curves": len(results),
            "low_param_regularity": {
                "count": len(low_param_orders),
                "avg_order_tier": avg(low_param_orders),
            },
            "high_param_regularity": {
                "count": len(high_param_orders),
                "avg_order_tier": avg(high_param_orders),
            },
            "correlation_signal": (
                avg(high_param_orders) - avg(low_param_orders)
                if low_param_orders and high_param_orders else None
            ),
        }

    def plimpton_curve_order_analysis(self) -> dict:
        """Analyze curves derived from Plimpton triples vs random curves."""
        from cuneiform.tablet.plimpton322 import Plimpton322

        rng = random.Random(42)
        tablet = Plimpton322()
        rows = tablet.original()

        plimpton_orders = []
        random_orders = []

        for row in rows:
            w, l, d = row.triple
            # Use small primes for feasible point counting
            for p in [997, 1009, 1013, 1021]:
                a = (w * l) % p
                b = (d * d) % p
                if a == 0 or (4 * a ** 3 + 27 * b ** 2) % p == 0:
                    continue
                order = _count_points_naive(a, b, p)
                if order > 1:
                    plimpton_orders.append({
                        "order": order,
                        "tier": RegularityClass(order).regularity_tier,
                        "smooth_fraction": RegularityClass(order).regular_part / order,
                    })

        # Random curves for comparison
        for _ in range(len(plimpton_orders)):
            p = [997, 1009, 1013, 1021][rng.randint(0, 3)]
            a = rng.randint(1, p - 1)
            b = rng.randint(1, p - 1)
            if (4 * a ** 3 + 27 * b ** 2) % p == 0:
                continue
            order = _count_points_naive(a, b, p)
            if order > 1:
                random_orders.append({
                    "order": order,
                    "tier": RegularityClass(order).regularity_tier,
                    "smooth_fraction": RegularityClass(order).regular_part / order,
                })

        avg = lambda xs: sum(xs) / len(xs) if xs else 0

        return {
            "plimpton_curves": len(plimpton_orders),
            "random_curves": len(random_orders),
            "plimpton_avg_order_tier": avg([o["tier"] for o in plimpton_orders]),
            "random_avg_order_tier": avg([o["tier"] for o in random_orders]),
            "plimpton_avg_smooth_fraction": avg(
                [o["smooth_fraction"] for o in plimpton_orders]),
            "random_avg_smooth_fraction": avg(
                [o["smooth_fraction"] for o in random_orders]),
        }

    def standard_curve_audit(self) -> dict:
        """Analyze standard ECC curves used in practice."""
        # Standard curve parameters (a, b, p, order)
        curves = {
            "secp256k1": {
                "a": 0,
                "b": 7,
                "p": 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F,
                "order": 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141,
            },
            "P-256": {
                "a": 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFC,
                "b": 0x5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B,
                "p": 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF,
                "order": 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551,
            },
            "Curve25519": {
                "a": 486662,  # Montgomery form parameter A
                "b": 1,
                "p": 2**255 - 19,
                "order": 2**252 + 27742317777372353535851937790883648493,
            },
        }

        results = {}
        for name, params in curves.items():
            rc_p = RegularityClass(params["p"])
            rc_order = RegularityClass(params["order"])

            # Analyze distance of p from multiples of 60
            p_mod_60 = params["p"] % 60
            order_mod_60 = params["order"] % 60

            results[name] = {
                "p_bits": params["p"].bit_length(),
                "p_mod_60": p_mod_60,
                "p_tier": rc_p.regularity_tier,
                "order_mod_60": order_mod_60,
                "order_tier": rc_order.regularity_tier,
                "order_is_prime": is_prime(params["order"]),
                "a_tier": RegularityClass(params["a"]).regularity_tier if params["a"] > 0 else 0,
                "b_tier": RegularityClass(params["b"]).regularity_tier,
                "security_note": (
                    "Prime order — maximally resistant to Pohlig-Hellman"
                    if is_prime(params["order"])
                    else "Non-prime order — check subgroup structure"
                ),
            }

        return results


class ECDLPRegularityAttack:
    """Compare standard vs regularity-guided Pollard rho for small ECDLP."""

    def __init__(self, a: int, b: int, p: int,
                 generator: tuple, order: int):
        self.a = a
        self.b = b
        self.p = p
        self.G = generator
        self.order = order

    def standard_rho(self, target: tuple,
                      max_steps: int = 100000) -> dict:
        """Standard Pollard rho with x-mod-3 partition."""
        # Floyd's cycle detection
        def step(P, aP, bP):
            x = P[0] % 3 if P != (0, 0) else 0
            if x == 0:
                P = _ec_add_fp(P, self.G, self.a, self.p)
                aP = (aP + 1) % self.order
            elif x == 1:
                P = _ec_add_fp(P, P, self.a, self.p)
                aP = (aP * 2) % self.order
                bP = (bP * 2) % self.order
            else:
                P = _ec_add_fp(P, target, self.a, self.p)
                bP = (bP + 1) % self.order
            return P, aP, bP

        # Start from generator
        tortoise = (self.G, 1, 0)
        hare = (self.G, 1, 0)

        for steps in range(1, max_steps):
            tortoise = step(*tortoise)
            hare = step(*step(*hare))

            if tortoise[0] == hare[0]:
                # Collision: a1*G + b1*T = a2*G + b2*T
                da = (tortoise[1] - hare[1]) % self.order
                db = (hare[2] - tortoise[2]) % self.order
                if db != 0 and gcd(db, self.order) == 1:
                    k = (da * invert(db, self.order)) % self.order
                    return {"steps": steps, "found": True, "k": k}
                return {"steps": steps, "found": False, "reason": "bad collision"}

        return {"steps": max_steps, "found": False, "reason": "max_steps"}

    def regularity_rho(self, target: tuple,
                        max_steps: int = 100000) -> dict:
        """Regularity-guided Pollard rho: partition by x mod 60."""
        def step(P, aP, bP):
            if P == (0, 0):
                r = 0
            else:
                r = P[0] % 60
            # Regular residues mod 60: divisible by only 2,3,5
            if r % 2 == 0 or r % 3 == 0 or r % 5 == 0:
                # "Regular" partition: add generator
                P = _ec_add_fp(P, self.G, self.a, self.p)
                aP = (aP + 1) % self.order
            elif r % 60 in (1, 59, 7, 53, 11, 49, 13, 47):
                # "Near-regular" partition: double
                P = _ec_add_fp(P, P, self.a, self.p)
                aP = (aP * 2) % self.order
                bP = (bP * 2) % self.order
            else:
                # "Irregular" partition: add target
                P = _ec_add_fp(P, target, self.a, self.p)
                bP = (bP + 1) % self.order
            return P, aP, bP

        tortoise = (self.G, 1, 0)
        hare = (self.G, 1, 0)

        for steps in range(1, max_steps):
            tortoise = step(*tortoise)
            hare = step(*step(*hare))

            if tortoise[0] == hare[0]:
                da = (tortoise[1] - hare[1]) % self.order
                db = (hare[2] - tortoise[2]) % self.order
                if db != 0 and gcd(db, self.order) == 1:
                    k = (da * invert(db, self.order)) % self.order
                    return {"steps": steps, "found": True, "k": k}
                return {"steps": steps, "found": False, "reason": "bad collision"}

        return {"steps": max_steps, "found": False, "reason": "max_steps"}

    def head_to_head(self, trials: int = 10) -> dict:
        """Compare step counts for standard vs regularity rho."""
        rng = random.Random(42)
        std_steps = []
        reg_steps = []

        for _ in range(trials):
            k = rng.randint(2, self.order - 1)
            target = _ec_mul_fp(k, self.G, self.a, self.p)

            std = self.standard_rho(target, max_steps=50000)
            reg = self.regularity_rho(target, max_steps=50000)

            if std["found"]:
                std_steps.append(std["steps"])
            if reg["found"]:
                reg_steps.append(reg["steps"])

        avg = lambda xs: sum(xs) / len(xs) if xs else 0

        return {
            "trials": trials,
            "standard": {
                "success_count": len(std_steps),
                "avg_steps": avg(std_steps),
            },
            "regularity": {
                "success_count": len(reg_steps),
                "avg_steps": avg(reg_steps),
            },
            "step_ratio": avg(reg_steps) / avg(std_steps) if avg(std_steps) > 0 else 0,
        }
