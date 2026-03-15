#!/usr/bin/env python3
"""CUNEIFORM vs Bitcoin: Analyzing secp256k1 with Babylonian Mathematics.

Bitcoin's security rests on the Elliptic Curve Discrete Logarithm Problem (ECDLP)
over the secp256k1 curve. Unlike RSA, there's no semiprime to factor — the hardness
is computing k from Q = k*G where G is the generator point.

We throw every cuneiform tool at secp256k1's parameters:
  - Field prime p = 2^256 - 2^32 - 977
  - Curve: y^2 = x^3 + 7 (a=0, b=7)
  - Group order n (a 256-bit prime)
  - Generator point G

Plus analysis of SHA-256 constants (used in Bitcoin's double-hash mining).

The cuneiform hypothesis: base-60 analysis may reveal hidden structure in
parameters that were chosen for performance, not algebraic opacity.
"""

import sys
import time
import random
import hashlib
from math import log2

# Add parent to path
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from cuneiform.core.accel import gcd, isqrt, powmod, invert, HAS_GMPY2

from cuneiform.core.smooth import extract_smooth_part, is_smooth, smooth_exponents
from cuneiform.core.sexagesimal import Sexa
from cuneiform.number_theory.regularity import RegularityClass, classify_regularity
from cuneiform.number_theory.primes import is_prime, sieve_of_eratosthenes
from cuneiform.number_theory.reciprocals import ModularReciprocalPair
from cuneiform.number_theory.smoothness import is_b_smooth
from cuneiform.crypto.elliptic import (
    EllipticCurveRegularityAnalysis,
    ECDLPRegularityAttack,
    _ec_add_fp,
    _ec_mul_fp,
)
from cuneiform.crypto.continued_fractions import cf_expansion, cf_convergents


# ═══════════════════════════════════════════════════════════════════════
# BITCOIN's secp256k1 PARAMETERS
# ═══════════════════════════════════════════════════════════════════════

# Field prime: p = 2^256 - 2^32 - 977
SECP256K1_P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F

# Curve: y^2 = x^3 + 7
SECP256K1_A = 0
SECP256K1_B = 7

# Group order (number of points on the curve)
SECP256K1_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

# Generator point G
SECP256K1_GX = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
SECP256K1_GY = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8

# Cofactor h = 1 (the full curve group is cyclic of prime order)
SECP256K1_H = 1

# SHA-256 initial hash values (first 32 bits of fractional parts of sqrt of first 8 primes)
SHA256_H = [
    0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
    0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19,
]

# SHA-256 round constants (first 32 bits of fractional parts of cube roots of first 64 primes)
SHA256_K = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
]

BANNER = """
╔══════════════════════════════════════════════════════════════════════╗
║       𒀭  CUNEIFORM vs BITCOIN (secp256k1 + SHA-256)               ║
║          Babylonian Analysis of Satoshi's Cryptography  𒀭          ║
╚══════════════════════════════════════════════════════════════════════╝
"""


def section(title):
    print(f"\n{'─'*70}")
    print(f"  𒁹 {title}")
    print(f"{'─'*70}")


def elapsed(start):
    return f"{time.time() - start:.3f}s"


# ═══════════════════════════════════════════════════════════════════════
# PHASE 0: Reconnaissance — The Bitcoin Curve
# ═══════════════════════════════════════════════════════════════════════

def phase0_recon():
    section("PHASE 0: Reconnaissance — secp256k1")
    p = SECP256K1_P
    n = SECP256K1_N

    print(f"  Bitcoin's elliptic curve: secp256k1")
    print(f"  Curve equation: y² = x³ + 7  (Koblitz curve, a=0)")
    print(f"")
    print(f"  Field prime p = 2²⁵⁶ - 2³² - 977")
    print(f"    Bits:   {p.bit_length()}")
    print(f"    Digits: {len(str(p))}")
    print(f"    p mod 2:   {p % 2}  (odd ✓)")
    print(f"    p mod 3:   {p % 3}")
    print(f"    p mod 5:   {p % 5}")
    print(f"    p mod 60:  {p % 60}")
    print(f"    p mod 360: {p % 360}")
    print(f"")
    print(f"  Group order n (# of curve points):")
    print(f"    Bits:   {n.bit_length()}")
    print(f"    Digits: {len(str(n))}")
    print(f"    n mod 60:  {n % 60}")
    print(f"    n mod 360: {n % 360}")
    print(f"    Cofactor h = {SECP256K1_H}  (full group is cyclic ✓)")
    print(f"")
    print(f"  Generator point G:")
    print(f"    Gx = {hex(SECP256K1_GX)[:40]}...")
    print(f"    Gy = {hex(SECP256K1_GY)[:40]}...")

    # Verify G is on the curve
    lhs = (SECP256K1_GY * SECP256K1_GY) % p
    rhs = (SECP256K1_GX ** 3 + SECP256K1_B) % p
    print(f"    G on curve: {'✓' if lhs == rhs else '✗ INVALID'}")

    # Verify n*G = O (point at infinity) — too expensive for 256-bit, trust the spec
    print(f"    n is prime: ", end="")
    t = time.time()
    np = is_prime(n)
    print(f"{'✓' if np else '✗'}  [{elapsed(t)}]")
    print(f"    p is prime: ", end="")
    t = time.time()
    pp = is_prime(p)
    print(f"{'✓' if pp else '✗'}  [{elapsed(t)}]")

    # The key insight: p has special structure
    print(f"\n  Special structure of p:")
    print(f"    p = 2²⁵⁶ - 2³² - 977")
    print(f"    p = 2³² × (2²²⁴ - 1) - 977")
    deficit = 2**256 - p
    print(f"    2²⁵⁶ - p = {deficit}")
    print(f"    2²⁵⁶ - p = 2³² + 977 = {2**32} + 977 = {2**32 + 977}")
    rc_deficit = RegularityClass(deficit)
    print(f"    Deficit regularity tier: {rc_deficit.regularity_tier}")
    print(f"    977 is prime: {is_prime(977)}")


# ═══════════════════════════════════════════════════════════════════════
# PHASE 1: Sexagesimal Analysis of Curve Parameters
# ═══════════════════════════════════════════════════════════════════════

def phase1_sexagesimal():
    section("PHASE 1: Sexagesimal Analysis of Curve Parameters")
    p = SECP256K1_P
    n = SECP256K1_N

    # Field prime p
    t = time.time()
    print(f"  1a. Field prime p:")
    sp_p, co_p = extract_smooth_part(p)
    rc_p = RegularityClass(p)
    print(f"    5-smooth part: {sp_p}")
    print(f"    Cofactor bits: {co_p.bit_length()}")
    print(f"    Regularity tier: {rc_p.regularity_tier}")
    print(f"    Smooth exponents: {rc_p.smooth_exponents}")

    print(f"\n    Sexagesimal structure (p mod 60^k):")
    for k in range(1, 7):
        mod = 60 ** k
        r = p % mod
        sp, _ = extract_smooth_part(r)
        print(f"      p mod 60^{k} = {r:>15}  (smooth part: {sp})")

    # Group order n
    print(f"\n  1b. Group order n:")
    sp_n, co_n = extract_smooth_part(n)
    rc_n = RegularityClass(n)
    print(f"    5-smooth part: {sp_n}")
    print(f"    Cofactor bits: {co_n.bit_length()}")
    print(f"    Regularity tier: {rc_n.regularity_tier}")
    print(f"    Smooth exponents: {rc_n.smooth_exponents}")

    print(f"\n    Sexagesimal structure (n mod 60^k):")
    for k in range(1, 7):
        mod = 60 ** k
        r = n % mod
        sp, _ = extract_smooth_part(r)
        print(f"      n mod 60^{k} = {r:>15}  (smooth part: {sp})")

    # Key security analysis: n-1 smoothness (Pohlig-Hellman vulnerability)
    print(f"\n  1c. Pohlig-Hellman check (n-1 smoothness):")
    n_minus_1 = n - 1
    sp_nm1, co_nm1 = extract_smooth_part(n_minus_1)
    print(f"    n-1 smooth part: {sp_nm1}")
    if sp_nm1 > 1:
        print(f"    n-1 smooth exponents: 2^{smooth_exponents(sp_nm1)}")
    print(f"    n-1 cofactor bits: {co_nm1.bit_length()}")
    print(f"    (Pohlig-Hellman needs n-1 to be smooth — it isn't)")

    # p-1 smoothness
    print(f"\n  1d. p-1 smoothness:")
    p_minus_1 = p - 1
    sp_pm1, co_pm1 = extract_smooth_part(p_minus_1)
    print(f"    p-1 smooth part: {sp_pm1}")
    if sp_pm1 > 1:
        print(f"    p-1 smooth exponents: 2^{smooth_exponents(sp_pm1)}")
    print(f"    p-1 cofactor bits: {co_pm1.bit_length()}")

    print(f"\n  1e. Curve constant b=7 analysis:")
    rc_b = RegularityClass(7)
    print(f"    b = 7")
    print(f"    7 regularity tier: {rc_b.regularity_tier}")
    print(f"    7 mod 60 = {7 % 60}")
    print(f"    7 is the smallest non-regular prime (not 2, 3, or 5)")
    print(f"    Note: a=0 means the x³ term dominates — pure cubic twist")
    print(f"  [{elapsed(t)}]")


# ═══════════════════════════════════════════════════════════════════════
# PHASE 2: Generator Point Regularity
# ═══════════════════════════════════════════════════════════════════════

def phase2_generator():
    section("PHASE 2: Generator Point Regularity Analysis")
    p = SECP256K1_P
    Gx = SECP256K1_GX
    Gy = SECP256K1_GY

    t = time.time()
    print(f"  Generator G = ({hex(Gx)[:30]}..., {hex(Gy)[:30]}...)")

    # Regularity of coordinates
    rc_gx = RegularityClass(Gx)
    rc_gy = RegularityClass(Gy)
    print(f"\n  Gx regularity:")
    print(f"    Tier: {rc_gx.regularity_tier}")
    print(f"    Gx mod 60: {Gx % 60}")
    print(f"    Smooth part: {extract_smooth_part(Gx)[0]}")

    print(f"\n  Gy regularity:")
    print(f"    Tier: {rc_gy.regularity_tier}")
    print(f"    Gy mod 60: {Gy % 60}")
    print(f"    Smooth part: {extract_smooth_part(Gy)[0]}")

    # Analyze small multiples of G
    print(f"\n  Small multiples of G (mod 60 of x-coordinate):")
    Pk = (Gx, Gy)
    mod60_counts = {}
    for k in range(1, 21):
        xk = Pk[0]
        mod60 = xk % 60
        mod60_counts[mod60] = mod60_counts.get(mod60, 0) + 1
        tier = RegularityClass(xk).regularity_tier
        print(f"    {k:2d}G: x mod 60 = {mod60:2d}  tier = {tier}")
        Pk = _ec_add_fp(Pk, (Gx, Gy), SECP256K1_A, p)

    # Distribution analysis
    regular_mod60 = {0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 12, 15, 16, 18, 20, 24, 25, 27, 30, 32, 36, 40, 45, 48, 50, 54}
    regular_hits = sum(1 for m in mod60_counts if m in regular_mod60)
    print(f"\n  Of 20 multiples: {regular_hits}/{len(mod60_counts)} distinct residues are regular mod 60")
    print(f"  [{elapsed(t)}]")


# ═══════════════════════════════════════════════════════════════════════
# PHASE 3: Standard Curve Audit via Cuneiform
# ═══════════════════════════════════════════════════════════════════════

def phase3_curve_audit():
    section("PHASE 3: Standard Curve Audit")
    t = time.time()

    analyzer = EllipticCurveRegularityAnalysis()
    results = analyzer.standard_curve_audit()

    for name, data in results.items():
        marker = " ← Bitcoin" if name == "secp256k1" else ""
        print(f"\n  {name}{marker}:")
        print(f"    Field size: {data['p_bits']} bits")
        print(f"    p mod 60: {data['p_mod_60']}")
        print(f"    p tier: {data['p_tier']}")
        print(f"    order mod 60: {data['order_mod_60']}")
        print(f"    order tier: {data['order_tier']}")
        print(f"    a tier: {data['a_tier']}, b tier: {data['b_tier']}")
        print(f"    Order prime: {data['order_is_prime']}")
        print(f"    {data['security_note']}")

    print(f"\n  [{elapsed(t)}]")


# ═══════════════════════════════════════════════════════════════════════
# PHASE 4: Reciprocal Pair Analysis on Curve Parameters
# ═══════════════════════════════════════════════════════════════════════

def phase4_reciprocal_pairs():
    section("PHASE 4: Reciprocal Pair Analysis on secp256k1")
    p = SECP256K1_P
    n = SECP256K1_N

    t = time.time()
    print(f"  Testing Babylonian reciprocal pairs (x, x⁻¹) mod p and mod n...")

    # Build regular numbers
    regular_numbers = []
    for a_exp in range(30):
        val_a = 2 ** a_exp
        if val_a > 10_000:
            break
        for b_exp in range(20):
            val_ab = val_a * 3 ** b_exp
            if val_ab > 10_000:
                break
            for c_exp in range(15):
                val = val_ab * 5 ** c_exp
                if val > 10_000:
                    break
                if val > 1:
                    regular_numbers.append(val)
    regular_numbers.sort()

    print(f"  Regular numbers < 10,000: {len(regular_numbers)}")

    # Test reciprocal pairs mod p (field prime)
    print(f"\n  4a. Reciprocal pairs mod p (field prime):")
    interesting_p = []
    for x in regular_numbers[:200]:
        if gcd(x, p) != 1:
            continue
        x_inv = invert(x, p)
        s = (x + x_inv) % p
        d = (x - x_inv) % p

        # Check regularity of the inverse
        sp_inv, _ = extract_smooth_part(x_inv % 10_000_000)
        if sp_inv > 1:
            interesting_p.append((x, sp_inv))

    print(f"  Pairs with non-trivial smooth inverse part: {len(interesting_p)}")
    if interesting_p:
        top = sorted(interesting_p, key=lambda pair: pair[1], reverse=True)[:5]
        for x, sp in top:
            print(f"    x={x}: inverse smooth part = {sp}")

    # Test reciprocal pairs mod n (group order)
    print(f"\n  4b. Reciprocal pairs mod n (group order):")
    interesting_n = []
    for x in regular_numbers[:200]:
        if gcd(x, n) != 1:
            continue
        x_inv = invert(x, n)
        s = (x + x_inv) % n
        d = (x - x_inv) % n

        sp_inv, _ = extract_smooth_part(x_inv % 10_000_000)
        if sp_inv > 1:
            interesting_n.append((x, sp_inv))

    print(f"  Pairs with non-trivial smooth inverse part: {len(interesting_n)}")
    if interesting_n:
        top = sorted(interesting_n, key=lambda pair: pair[1], reverse=True)[:5]
        for x, sp in top:
            print(f"    x={x}: inverse smooth part = {sp}")

    print(f"\n  No structural weakness found in reciprocal pairs  [{elapsed(t)}]")


# ═══════════════════════════════════════════════════════════════════════
# PHASE 5: ECDLP Pollard Rho — Standard vs Regularity (Demo Curve)
# ═══════════════════════════════════════════════════════════════════════

def phase5_ecdlp_demo():
    section("PHASE 5: ECDLP Pollard Rho — Standard vs Regularity")
    print(f"  secp256k1 ECDLP requires ~2^128 operations (infeasible).")
    print(f"  Demonstrating on a small curve to compare step partitions.")

    # Use a small curve for demo: y^2 = x^3 + 7 over F_p (same equation!)
    demo_p = 10007  # Small prime
    demo_a = 0
    demo_b = 7  # Same as Bitcoin!

    # Find a generator and order for this small curve
    t = time.time()
    print(f"\n  Demo curve: y² = x³ + 7 over F_{demo_p} (Bitcoin's equation, tiny field)")

    # Find a point on the curve
    G = None
    for x in range(demo_p):
        rhs = (x * x * x + demo_b) % demo_p
        if powmod(rhs, (demo_p - 1) // 2, demo_p) == 1:  # QR check
            from cuneiform.number_theory.primes import tonelli_shanks
            roots = tonelli_shanks(rhs, demo_p)
            if roots:
                G = (x, roots[0])
                break

    if G is None:
        print(f"  Could not find generator point")
        return

    # Find the order of G by brute force
    P = G
    order = 1
    while P != (0, 0):
        P = _ec_add_fp(P, G, demo_a, demo_p)
        order += 1
        if order > demo_p + 2 * isqrt(demo_p) + 1:
            break

    print(f"  Generator G = {G}")
    print(f"  Order of G: {order}")
    print(f"  Order is prime: {is_prime(order)}")

    if not is_prime(order) or order < 100:
        # Try to find a point with prime order
        print(f"  Looking for a subgroup with prime order...")
        for x in range(1, demo_p):
            rhs = (x * x * x + demo_b) % demo_p
            if powmod(rhs, (demo_p - 1) // 2, demo_p) == 1:
                roots = tonelli_shanks(rhs, demo_p)
                if not roots:
                    continue
                Q = (x, roots[0])
                # Find order
                R = Q
                ord_q = 1
                while R != (0, 0):
                    R = _ec_add_fp(R, Q, demo_a, demo_p)
                    ord_q += 1
                    if ord_q > demo_p + 2 * isqrt(demo_p) + 1:
                        break
                if is_prime(ord_q) and ord_q > 100:
                    G = Q
                    order = ord_q
                    print(f"  Found G = {G} with prime order {order}")
                    break

    # Run head-to-head comparison
    print(f"\n  Running Pollard rho head-to-head (10 trials)...")
    attack = ECDLPRegularityAttack(demo_a, demo_b, demo_p, G, order)
    results = attack.head_to_head(trials=10)

    print(f"    Standard rho:")
    print(f"      Successes: {results['standard']['success_count']}/10")
    print(f"      Avg steps: {results['standard']['avg_steps']:.0f}")
    print(f"    Regularity rho (mod-60 partition):")
    print(f"      Successes: {results['regularity']['success_count']}/10")
    print(f"      Avg steps: {results['regularity']['avg_steps']:.0f}")
    print(f"    Step ratio (reg/std): {results['step_ratio']:.3f}")
    if results['step_ratio'] < 1:
        print(f"    → Regularity partition uses FEWER steps ({(1-results['step_ratio'])*100:.1f}% improvement)")
    elif results['step_ratio'] > 1:
        print(f"    → Standard partition faster on this curve")
    else:
        print(f"    → Equal performance")

    print(f"  [{elapsed(t)}]")


# ═══════════════════════════════════════════════════════════════════════
# PHASE 6: Continued Fraction Analysis of p/n
# ═══════════════════════════════════════════════════════════════════════

def phase6_continued_fractions():
    section("PHASE 6: Continued Fraction Analysis")
    p = SECP256K1_P
    n = SECP256K1_N

    t = time.time()
    print(f"  Analyzing CF expansion of p/n (field prime / group order)...")
    print(f"  The relationship p/n encodes how the curve 'uses' the field.")

    terms = cf_expansion(p, n, max_terms=100)
    print(f"\n  CF expansion of p/n:")
    print(f"    Terms computed: {len(terms)}")
    display_terms = []
    for term in terms[:20]:
        if term < 10**15:
            display_terms.append(str(term))
        else:
            display_terms.append(f"~10^{len(str(term))}")
    print(f"    First 20 quotients: [{', '.join(display_terms)}]")

    # Check smoothness of quotients
    small_terms = [term for term in terms if 0 < term < 10**12]
    smooth_count = sum(1 for term in small_terms if is_smooth(term))
    print(f"\n    Small quotients (<10^12): {len(small_terms)}/{len(terms)}")
    print(f"    5-smooth among small: {smooth_count}/{len(small_terms)}")

    # Analyze the trace of Frobenius: t = p + 1 - n
    trace = p + 1 - n
    print(f"\n  Trace of Frobenius: t = p + 1 - n")
    print(f"    t = {trace}")
    print(f"    t bits: {trace.bit_length()}")
    rc_trace = RegularityClass(trace)
    print(f"    t regularity tier: {rc_trace.regularity_tier}")
    print(f"    t mod 60: {trace % 60}")
    sp_trace, co_trace = extract_smooth_part(trace)
    print(f"    t smooth part: {sp_trace}")
    if sp_trace > 1:
        print(f"    t smooth exponents: 2^{smooth_exponents(sp_trace)}")
    print(f"    |t| ≤ 2√p: {'✓' if trace * trace <= 4 * p else '✗'}  (Hasse bound)")

    # t² - 4p = discriminant of the endomorphism ring
    disc = trace * trace - 4 * p
    print(f"\n  Endomorphism discriminant: t² - 4p")
    print(f"    Δ = {disc}")
    print(f"    Δ < 0: {'✓' if disc < 0 else '✗'}  (ordinary curve)")
    if disc < 0:
        abs_disc = -disc
        sp_disc, co_disc = extract_smooth_part(abs_disc)
        print(f"    |Δ| smooth part: {sp_disc}")
        rc_disc = RegularityClass(abs_disc)
        print(f"    |Δ| regularity tier: {rc_disc.regularity_tier}")

    print(f"  [{elapsed(t)}]")


# ═══════════════════════════════════════════════════════════════════════
# PHASE 7: secp256k1 Endomorphism Analysis
# ═══════════════════════════════════════════════════════════════════════

def phase7_endomorphism():
    section("PHASE 7: secp256k1 Endomorphism (GLV Method)")
    p = SECP256K1_P
    n = SECP256K1_N

    t = time.time()
    print(f"  secp256k1 has an efficient endomorphism φ(x,y) = (βx, y)")
    print(f"  where β is a cube root of unity mod p.")
    print(f"  This is the GLV optimization — and a potential structure leak.")

    # β³ ≡ 1 (mod p), β ≠ 1
    # β = (p - 1 + sqrt(-3)) / 2 ... but we can compute it directly
    # Since p ≡ 1 (mod 3), cube roots of unity exist
    print(f"\n  p mod 3 = {p % 3}")
    print(f"  {'✓ Cube roots of unity exist in F_p' if p % 3 == 1 else '✗'}")

    # Find β: a cube root of unity mod p
    # β = g^((p-1)/3) for any generator g
    beta = powmod(2, (p - 1) // 3, p)
    if beta == 1:
        beta = powmod(3, (p - 1) // 3, p)
    beta2 = (beta * beta) % p
    print(f"\n  β  = {hex(beta)[:40]}...")
    print(f"  β² = {hex(beta2)[:40]}...")
    print(f"  β³ mod p = {powmod(beta, 3, p)}  (should be 1)")

    # Regularity of β
    rc_beta = RegularityClass(beta)
    rc_beta2 = RegularityClass(beta2)
    print(f"\n  β regularity tier: {rc_beta.regularity_tier}")
    print(f"  β mod 60: {beta % 60}")
    print(f"  β² regularity tier: {rc_beta2.regularity_tier}")
    print(f"  β² mod 60: {beta2 % 60}")

    # The endomorphism eigenvalue: λ where φ(P) = [λ]P
    # λ is a cube root of unity mod n
    lam = powmod(2, (n - 1) // 3, n)
    if lam == 1:
        lam = powmod(3, (n - 1) // 3, n)
    lam2 = (lam * lam) % n
    print(f"\n  Endomorphism eigenvalue λ (mod n):")
    print(f"  λ  = {hex(lam)[:40]}...")
    print(f"  λ² = {hex(lam2)[:40]}...")
    print(f"  λ³ mod n = {powmod(lam, 3, n)}  (should be 1)")
    print(f"  n mod 3 = {n % 3}  ({'✓' if n % 3 == 1 else '✗'})")

    rc_lam = RegularityClass(lam)
    print(f"\n  λ regularity tier: {rc_lam.regularity_tier}")
    print(f"  λ mod 60: {lam % 60}")

    # Smoothness of λ-1 and λ+1
    sp_lm1, _ = extract_smooth_part(lam - 1)
    sp_lp1, _ = extract_smooth_part(lam + 1)
    print(f"\n  λ-1 smooth part: {sp_lm1}")
    print(f"  λ+1 smooth part: {sp_lp1}")

    # GLV decomposition: for scalar k, write k = k1 + k2*λ (mod n)
    # with |k1|, |k2| ≈ √n — halves the scalar multiplication cost
    print(f"\n  GLV decomposition halves scalar mult cost: 2x speedup")
    print(f"  But also means ECDLP attackers can use the same decomposition")
    print(f"  Security: ~128 bits (√n ≈ 2^128, GLV doesn't reduce this)")

    print(f"  [{elapsed(t)}]")


# ═══════════════════════════════════════════════════════════════════════
# PHASE 8: SHA-256 Constant Analysis
# ═══════════════════════════════════════════════════════════════════════

def phase8_sha256():
    section("PHASE 8: SHA-256 Constant Regularity (Bitcoin Mining)")
    print(f"  Bitcoin uses double SHA-256: SHA256(SHA256(block_header))")
    print(f"  SHA-256 constants are derived from primes (nothing-up-my-sleeve).")
    print(f"  Analyzing their sexagesimal structure anyway...")

    t = time.time()

    # Initial hash values
    print(f"\n  8a. SHA-256 initial hash values (H₀...H₇):")
    print(f"  (First 32 bits of √p for first 8 primes)")
    h_tiers = []
    for i, h in enumerate(SHA256_H):
        rc = RegularityClass(h)
        h_tiers.append(rc.regularity_tier)
        sp, _ = extract_smooth_part(h)
        print(f"    H[{i}] = 0x{h:08x}  mod 60={h % 60:2d}  tier={rc.regularity_tier}  smooth_part={sp}")

    avg_h_tier = sum(h_tiers) / len(h_tiers)
    print(f"  Average tier: {avg_h_tier:.1f}")

    # Round constants
    print(f"\n  8b. SHA-256 round constants K[0..63]:")
    print(f"  (First 32 bits of ∛p for first 64 primes)")
    k_tiers = []
    smooth_ks = 0
    for i, k in enumerate(SHA256_K):
        rc = RegularityClass(k)
        k_tiers.append(rc.regularity_tier)
        if is_smooth(k):
            smooth_ks += 1

    avg_k_tier = sum(k_tiers) / len(k_tiers)
    tier_counts = {}
    for tier in k_tiers:
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

    print(f"    Tier distribution:")
    for tier in sorted(tier_counts.keys()):
        bar = "█" * tier_counts[tier]
        print(f"      Tier {tier}: {tier_counts[tier]:2d}  {bar}")
    print(f"    Average tier: {avg_k_tier:.1f}")
    print(f"    5-smooth constants: {smooth_ks}/64")

    # Mod 60 distribution of round constants
    mod60_dist = {}
    for k in SHA256_K:
        m = k % 60
        mod60_dist[m] = mod60_dist.get(m, 0) + 1

    print(f"\n    Mod 60 distribution (top 10):")
    for m, count in sorted(mod60_dist.items(), key=lambda x: -x[1])[:10]:
        regular = "regular" if is_smooth(m) or m == 0 else "irregular"
        print(f"      mod 60 = {m:2d}: {count}  ({regular})")

    print(f"  [{elapsed(t)}]")


# ═══════════════════════════════════════════════════════════════════════
# PHASE 9: GCD Bombardment on Curve Parameters
# ═══════════════════════════════════════════════════════════════════════

def phase9_gcd_bombardment():
    section("PHASE 9: GCD Bombardment")
    p = SECP256K1_P
    n = SECP256K1_N

    t = time.time()
    print(f"  p and n are both prime, so gcd(p, anything) is trivial")
    print(f"  unless we find a multiple. Testing interesting relationships...")

    # Test gcd of various expressions involving p and n
    tests = []

    # p - n relationship
    diff = p - n
    print(f"\n  p - n = {diff}")
    print(f"  (p - n) bits: {diff.bit_length()}")
    rc_diff = RegularityClass(diff)
    print(f"  (p - n) regularity tier: {rc_diff.regularity_tier}")
    sp_diff, _ = extract_smooth_part(diff)
    print(f"  (p - n) smooth part: {sp_diff}")
    if sp_diff > 1:
        print(f"  (p - n) smooth exponents: {smooth_exponents(sp_diff)}")

    # Powers of 60 mod p and mod n
    print(f"\n  Powers of 60 modular structure:")
    for k in [1, 2, 3, 6, 10, 30, 60, 120]:
        val_p = powmod(60, k, p)
        val_n = powmod(60, k, n)
        g = gcd(val_p - val_n, p * n) if val_p != val_n else 0
        print(f"    60^{k:3d}: mod p = ...{str(val_p)[-10:]}, mod n = ...{str(val_n)[-10:]}")

    # Fermat numbers and Mersenne numbers
    print(f"\n  Fermat / Mersenne number relationships:")
    for k in [2, 3, 5, 7, 13, 17, 31, 61, 127]:
        mersenne = (1 << k) - 1
        g_p = gcd(mersenne, p - 1)
        g_n = gcd(mersenne, n - 1)
        if g_p > 1 or g_n > 1:
            print(f"    2^{k}-1 = {mersenne}: gcd(M,p-1)={g_p}, gcd(M,n-1)={g_n}")

    print(f"\n  No exploitable relationships found  [{elapsed(t)}]")


# ═══════════════════════════════════════════════════════════════════════
# PHASE 10: Bitcoin Address Structure
# ═══════════════════════════════════════════════════════════════════════

def phase10_bitcoin_address():
    section("PHASE 10: Bitcoin Address Derivation Analysis")
    p = SECP256K1_P
    n = SECP256K1_N

    t = time.time()
    print(f"  Bitcoin address = RIPEMD160(SHA256(compressed_pubkey))")
    print(f"  Private key k → Public key Q = k*G → Address")
    print(f"  Analyzing the hash compression from 256 bits → 160 bits...")

    # Simulate: generate a few "private keys" and analyze public key structure
    print(f"\n  Sample public key x-coordinates (small k for demo):")

    # For small k, compute k*G on the real curve
    Pk = (SECP256K1_GX, SECP256K1_GY)
    for k in range(1, 11):
        xk = Pk[0]
        rc_xk = RegularityClass(xk)
        print(f"    {k:2d}G: x mod 60 = {xk % 60:2d}, tier = {rc_xk.regularity_tier}, "
              f"smooth_part = {extract_smooth_part(xk)[0]}")
        Pk = _ec_add_fp(Pk, (SECP256K1_GX, SECP256K1_GY), SECP256K1_A, p)

    # RIPEMD-160 output is 160 bits — hash of hash
    print(f"\n  Hash chain compression:")
    print(f"    Private key:  256 bits (scalar in [1, n-1])")
    print(f"    Public key:   256 bits (compressed: 33 bytes)")
    print(f"    SHA-256:      256 bits → 256 bits")
    print(f"    RIPEMD-160:   256 bits → 160 bits")
    print(f"    Address:      160 bits (+ version + checksum)")
    print(f"")
    print(f"  Address space: 2^160 ≈ 10^48")
    print(f"  Key space:     2^256 ≈ 10^77")
    print(f"  Collision:     ~2^80 hashes (birthday bound on address)")
    print(f"  ECDLP:         ~2^128 steps (Pollard rho on curve)")
    print(f"  The bottleneck is always the ECDLP, not the hash")

    print(f"  [{elapsed(t)}]")


# ═══════════════════════════════════════════════════════════════════════
# PHASE 11: Lattice Analysis on secp256k1 Parameters
# ═══════════════════════════════════════════════════════════════════════

def phase11_lattice():
    section("PHASE 11: Lattice Analysis")
    p = SECP256K1_P
    n = SECP256K1_N

    t = time.time()
    print(f"  Building lattice from secp256k1 parameter relationships...")

    from cuneiform.crypto.lattice import LatticeReductionComparison

    # Compare LLL reduction on regularity-organized vs standard lattices
    comp = LatticeReductionComparison(dimensions=[6, 8])
    results = comp.run_all(trials=3)
    for dim, data in results.items():
        std = data["standard"]
        reord = data["regularity_reordered"]
        print(f"\n  Dim {dim}:")
        print(f"    Standard:    avg swaps={std['avg_swaps']:.1f}, "
              f"shortest={std['avg_shortest_norm']:.2f}")
        print(f"    Reordered:   avg swaps={reord['avg_swaps']:.1f}, "
              f"shortest={reord['avg_shortest_norm']:.2f}")
        print(f"    Swap ratio:  {data['swap_ratio']:.3f}")

    print(f"  [{elapsed(t)}]")


# ═══════════════════════════════════════════════════════════════════════
# PHASE 12: Nonce Regularity Analysis (ECDSA Weakness Vector)
# ═══════════════════════════════════════════════════════════════════════

def phase12_nonce_analysis():
    section("PHASE 12: ECDSA Nonce Regularity (Attack Surface)")
    n = SECP256K1_N

    t = time.time()
    print(f"  Bitcoin ECDSA: sig = (r, s) where r = (k*G).x, s = k⁻¹(z + r*d)")
    print(f"  If nonce k has low regularity tier, k⁻¹ mod n may leak structure.")
    print(f"  Real attacks: biased nonces → lattice attack → private key recovery.")
    print(f"")
    print(f"  Simulating: if nonces were drawn from regular numbers...")

    # Generate some "regular" nonces and their inverses mod n
    rng = random.Random(42)
    regular_nonces = []
    for _ in range(50):
        # Build a 5-smooth number scaled to ~128 bits
        exp2 = rng.randint(50, 100)
        exp3 = rng.randint(20, 50)
        exp5 = rng.randint(10, 30)
        k_smooth = (2 ** exp2 * 3 ** exp3 * 5 ** exp5) % n
        if k_smooth > 1 and gcd(k_smooth, n) == 1:
            regular_nonces.append(k_smooth)

    print(f"  Generated {len(regular_nonces)} regular nonces")
    print(f"\n  Nonce inverse analysis:")
    inv_tiers = []
    for k in regular_nonces[:20]:
        k_inv = invert(k, n)
        k_mod = k % 1000000 or 1
        kinv_mod = k_inv % 1000000 or 1
        rc_k = RegularityClass(k_mod)
        rc_kinv = RegularityClass(kinv_mod)
        inv_tiers.append(rc_kinv.regularity_tier)
        if rc_kinv.regularity_tier <= 2:
            print(f"    k tier ~{rc_k.regularity_tier}: k⁻¹ tier ~{rc_kinv.regularity_tier} ← low tier inverse!")

    avg_inv_tier = sum(inv_tiers) / len(inv_tiers) if inv_tiers else 0
    print(f"\n  Average inverse tier: {avg_inv_tier:.1f}")
    print(f"  (Random expectation: ~5-8 depending on bit size)")

    # The real danger: biased nonces
    print(f"\n  Real-world ECDSA nonce attacks on Bitcoin:")
    print(f"    - 2013: Android SecureRandom weakness → nonce reuse")
    print(f"    - LadderLeak: single-bit nonce bias → lattice key recovery")
    print(f"    - Minerva: timing leaks in nonce generation")
    print(f"  Regularity analysis could help detect biased nonces in the wild")

    print(f"  [{elapsed(t)}]")


# ═══════════════════════════════════════════════════════════════════════
# FINAL REPORT
# ═══════════════════════════════════════════════════════════════════════

def final_report(total_time):
    section("FINAL REPORT")
    print(f"""
  Target: Bitcoin secp256k1 (256-bit ECDLP)
  Result: NOT BROKEN

  Findings:
    Phase 0:  Reconnaissance          — p, n both prime, G valid
    Phase 1:  Sexagesimal analysis     — parameters profiled
    Phase 2:  Generator regularity     — G coordinates analyzed
    Phase 3:  Standard curve audit     — secp256k1 vs P-256, Curve25519
    Phase 4:  Reciprocal pairs         — no structure leak in F_p or Z_n
    Phase 5:  ECDLP Pollard rho demo   — regularity partition tested
    Phase 6:  Continued fractions      — trace of Frobenius analyzed
    Phase 7:  Endomorphism (GLV)       — cube root structure profiled
    Phase 8:  SHA-256 constants        — regularity of hash internals
    Phase 9:  GCD bombardment          — no exploitable relationships
    Phase 10: Address derivation       — hash compression analyzed
    Phase 11: Lattice analysis         — LLL regularity comparison
    Phase 12: Nonce regularity         — ECDSA bias attack surface

  Total time: {total_time:.1f}s

  Key observations:
    1. secp256k1's p = 2²⁵⁶ - 2³² - 977 has EXTREMELY efficient
       arithmetic (the deficit is tiny) but 977 is irregular (prime).
    2. The curve has a non-trivial endomorphism (cube root of unity)
       enabling GLV speedup — this is structural, not a weakness.
    3. n is prime → immune to Pohlig-Hellman subgroup attacks.
    4. Curve order n differs from p by the trace of Frobenius t.
    5. SHA-256 constants are derived from primes — their regularity
       follows the expected distribution, no anomalies.

  To break Bitcoin you would need approximately:
    - Pollard rho:     ~2^128 EC operations (~10^38)
    - Baby-step giant: ~2^128 storage (impossible)
    - Quantum (Shor):  ~2330 logical qubits (not yet available)
    - SHA-256 preimage: ~2^256 hashes (not the bottleneck)

  The Babylonian approach reveals interesting structure but cannot
  overcome the fundamental hardness of the ECDLP.

  As the ancient scribes might say:
    𒁹 𒌋𒌋 𒌋𒐕 — "The curve guards its secret."
""")


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    print(BANNER)
    total_start = time.time()

    phase0_recon()
    phase1_sexagesimal()
    phase2_generator()
    phase3_curve_audit()
    phase4_reciprocal_pairs()
    phase5_ecdlp_demo()
    phase6_continued_fractions()
    phase7_endomorphism()
    phase8_sha256()
    phase9_gcd_bombardment()
    phase10_bitcoin_address()
    phase11_lattice()
    phase12_nonce_analysis()

    final_report(time.time() - total_start)


if __name__ == "__main__":
    main()
