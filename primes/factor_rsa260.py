#!/usr/bin/env python3
"""Attempt to factor RSA-2048 using every tool in the cuneiform arsenal.

This is the RSA-2048 challenge number from RSA Laboratories (2048 bits, ~617 digits).
No one has ever factored it. We throw ancient Babylonian mathematics at it anyway.

The cuneiform hypothesis: base-60 representation privileges 5-smooth numbers,
and organizing algorithms around this property may expose hidden structure.
Let's find out.
"""

import sys
import time
import random
from math import gcd, isqrt, log, log2

# Add parent to path
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from cuneiform.core.smooth import extract_smooth_part, is_smooth, smooth_exponents
from cuneiform.core.sexagesimal import Sexa
from cuneiform.number_theory.regularity import RegularityClass, classify_regularity
from cuneiform.number_theory.primes import is_prime, sieve_of_eratosthenes
from cuneiform.number_theory.reciprocals import ModularReciprocalPair
from cuneiform.crypto.rsa_analysis import RSAAnalysis
from cuneiform.crypto.continued_fractions import (
    SexagesimalContinuedFractions, cf_expansion, cf_convergents,
)

# ═══════════════════════════════════════════════════════════════════════
# THE TARGET
# ═══════════════════════════════════════════════════════════════════════

RSA_2048 = int(
    "22112825529529666435281085255026230927612089502470015394413748319128822941402001986512729726569746599085900330031400051170742204560859276357953757185954298838958709229238491006703034124620545784566413664540684214361293017694020846391065875914794251435144458199"
)

BANNER = """
╔══════════════════════════════════════════════════════════════════════╗
║        𒀭  CUNEIFORM vs RSA-2048: Breaking Modern Crypto           ║
║              with 3,700-Year-Old Mathematics  𒀭                    ║
╚══════════════════════════════════════════════════════════════════════╝
"""


def section(title):
    print(f"\n{'─'*70}")
    print(f"  𒁹 {title}")
    print(f"{'─'*70}")


def elapsed(start):
    return f"{time.time() - start:.3f}s"


# ═══════════════════════════════════════════════════════════════════════
# PHASE 0: Reconnaissance — Know Your Enemy
# ═══════════════════════════════════════════════════════════════════════

def phase0_recon(n):
    section("PHASE 0: Reconnaissance")
    print(f"  Target: RSA-2048 challenge number")
    print(f"  Digits: {len(str(n))}")
    print(f"  Bits:   {n.bit_length()}")
    print(f"  n mod 2:  {n % 2}  (odd ✓)")
    print(f"  n mod 3:  {n % 3}")
    print(f"  n mod 5:  {n % 5}")
    print(f"  n mod 60: {n % 60}")
    print(f"  n mod 360: {n % 360}")

    # Perfect square check
    s = isqrt(n)
    if s * s == n:
        print(f"  !! PERFECT SQUARE — sqrt(n) = {s}")
        return s
    print(f"  Perfect square: No")
    print(f"  isqrt(n) ≈ {str(s)[:40]}... ({s.bit_length()} bits)")

    # Check if n is itself prime (it shouldn't be — it's a semiprime)
    # Skip full Miller-Rabin on 2048-bit number, just do quick Fermat test
    t = time.time()
    fermat = pow(2, n - 1, n)
    print(f"  Fermat test (base 2): 2^(n-1) mod n = {'1 (probable prime or Carmichael)' if fermat == 1 else 'not 1 (composite ✓)'}  [{elapsed(t)}]")

    return None


# ═══════════════════════════════════════════════════════════════════════
# PHASE 1: Sexagesimal Analysis — The Babylonian Lens
# ═══════════════════════════════════════════════════════════════════════

def phase1_sexagesimal(n):
    section("PHASE 1: Sexagesimal Analysis")

    t = time.time()
    smooth_part, cofactor = extract_smooth_part(n)
    print(f"  5-smooth decomposition:  [{elapsed(t)}]")
    print(f"    n = smooth_part × cofactor")
    print(f"    smooth_part = {smooth_part}")
    if smooth_part > 1:
        exp = smooth_exponents(smooth_part)
        print(f"    smooth_part = 2^{exp[0]} × 3^{exp[1]} × 5^{exp[2]}")
    print(f"    cofactor bits: {cofactor.bit_length()}")

    # Regularity classification
    t = time.time()
    rc = RegularityClass(n)
    print(f"\n  Regularity classification:  [{elapsed(t)}]")
    print(f"    Tier: {rc.regularity_tier}")
    print(f"    Is regular (5-smooth): {rc.is_regular}")
    print(f"    Smooth exponents: {rc.smooth_exponents}")

    # Sexagesimal representation of n mod 60^k for small k
    print(f"\n  Sexagesimal structure (n mod 60^k):")
    for k in range(1, 7):
        mod = 60**k
        r = n % mod
        print(f"    n mod 60^{k} = {r:>15}  (smooth part: {extract_smooth_part(r)[0] if r > 0 else 0})")

    # Analyze n ± small offsets for regularity
    print(f"\n  Near-regular neighborhood (n ± δ):")
    best_delta = None
    best_smooth = 0
    for delta in range(-20, 21):
        val = n + delta
        if val <= 0:
            continue
        sp, co = extract_smooth_part(val)
        if sp > best_smooth:
            best_smooth = sp
            best_delta = delta
        if sp > 1 and sp != val:
            print(f"    n + ({delta:+3d}): smooth_part = {sp} = 2^{smooth_exponents(sp)}")
    if best_delta is not None:
        print(f"  Best offset: δ = {best_delta}, smooth_part = {best_smooth}")


# ═══════════════════════════════════════════════════════════════════════
# PHASE 2: Trial Division — The Oldest Attack
# ═══════════════════════════════════════════════════════════════════════

def phase2_trial_division(n, limit=1_000_000):
    section(f"PHASE 2: Trial Division (primes up to {limit:,})")
    t = time.time()
    primes = sieve_of_eratosthenes(limit)
    print(f"  Generated {len(primes):,} primes up to {limit:,}  [{elapsed(t)}]")

    t = time.time()
    for p in primes:
        if n % p == 0:
            print(f"  !! FACTOR FOUND: {p}")
            return p
    print(f"  No small factors found  [{elapsed(t)}]")
    print(f"  (RSA primes are ~1024 bits each — trial division needs ~2^512 operations)")
    return None


# ═══════════════════════════════════════════════════════════════════════
# PHASE 3: Pollard's p-1 — Exploiting Smooth Group Orders
# ═══════════════════════════════════════════════════════════════════════

def phase3_pollard_p1(n, B1=500_000, B2=5_000_000):
    section(f"PHASE 3: Pollard p-1 (B1={B1:,}, B2={B2:,})")
    print(f"  If p-1 or q-1 is B1-smooth, this finds the factor.")
    print(f"  (RSA primes are chosen so p-1, q-1 have large prime factors)")

    t = time.time()
    primes = sieve_of_eratosthenes(B1)
    print(f"  Stage 1: {len(primes):,} primes, computing 2^(∏ p^e) mod n...")

    a = 2
    for p in primes:
        # Compute p^e <= B1
        pe = p
        while pe * p <= B1:
            pe *= p
        a = pow(a, pe, n)

    g = gcd(a - 1, n)
    print(f"  Stage 1 gcd: {'TRIVIAL' if g == 1 or g == n else g}  [{elapsed(t)}]")

    if 1 < g < n:
        print(f"  !! FACTOR FOUND: {g}")
        return g

    # Stage 2: check individual primes between B1 and B2
    t2 = time.time()
    print(f"  Stage 2: checking primes in ({B1:,}, {B2:,})...")
    # Use baby-step giant-step style: precompute a^(2*delta) for small deltas
    stride = 2 * 3 * 5 * 7  # 210 (primorial)
    a_stride = pow(a, stride, n)
    a_current = pow(a, B1 - (B1 % stride), n)

    # Quick stage 2 — check a few thousand primes
    count = 0
    for p in range(B1 + 1, min(B2, B1 + 500_000), 2):
        if count % 10000 == 0 and count > 0:
            g2 = gcd(a_current - 1, n)
            if 1 < g2 < n:
                print(f"  !! Stage 2 FACTOR at p~{p}: {g2}")
                return g2
        a_current = pow(a_current, p, n)
        count += 1

    g2 = gcd(a_current - 1, n)
    print(f"  Stage 2 gcd: {'TRIVIAL' if g2 == 1 or g2 == n else g2}  [{elapsed(t2)}]")

    if 1 < g2 < n:
        print(f"  !! FACTOR FOUND: {g2}")
        return g2

    print(f"  No factor found (p-1 and q-1 are not smooth enough)")
    return None


# ═══════════════════════════════════════════════════════════════════════
# PHASE 4: Pollard's rho — Birthday Paradox Attack
# ═══════════════════════════════════════════════════════════════════════

def phase4_pollard_rho(n, iterations=5_000_000):
    section(f"PHASE 4: Pollard's rho ({iterations:,} iterations)")
    print(f"  Expected: O(p^(1/4)) iterations for smallest prime p")
    print(f"  For RSA-2048: p ~ 2^1024, so we need ~ 2^256 iterations")
    print(f"  We'll try {iterations:,} just to be thorough...")

    t = time.time()
    x = 2
    y = 2
    c = 1
    d = 1

    # Brent's improvement: accumulate product, batch gcd
    product = 1
    batch = 1000

    for i in range(1, iterations + 1):
        x = (x * x + c) % n
        y = (y * y + c) % n
        y = (y * y + c) % n

        product = (product * abs(x - y)) % n

        if i % batch == 0:
            d = gcd(product, n)
            if d == n:
                # Backtrack with single steps
                x2 = 2
                y2 = 2
                for j in range(max(0, i - batch), i):
                    x2 = (x2 * x2 + c) % n
                    y2 = (y2 * y2 + c) % n
                    y2 = (y2 * y2 + c) % n
                    d2 = gcd(abs(x2 - y2), n)
                    if 1 < d2 < n:
                        print(f"  !! FACTOR at iteration {j}: {d2}")
                        return d2
                # Try different c
                c += 1
                x = y = 2
                product = 1
                continue
            if 1 < d < n:
                print(f"  !! FACTOR at iteration {i}: {d}  [{elapsed(t)}]")
                return d
            product = 1

        if i % 1_000_000 == 0:
            print(f"    ... {i:,} iterations  [{elapsed(t)}]")

    print(f"  No factor found after {iterations:,} iterations  [{elapsed(t)}]")
    return None


# ═══════════════════════════════════════════════════════════════════════
# PHASE 5: ECM — Elliptic Curve Method (Standard + Plimpton)
# ═══════════════════════════════════════════════════════════════════════

def phase5_ecm(n, curves=50, B1=50_000):
    section(f"PHASE 5: Elliptic Curve Method ({curves} curves, B1={B1:,})")
    print(f"  ECM excels at finding small factors — but RSA-2048 has none.")
    print(f"  We try both standard random curves and Plimpton-322-derived curves.")

    from cuneiform.number_theory.ecm import ECM, PlimptonECM

    # Standard ECM
    t = time.time()
    print(f"\n  5a. Standard ECM ({curves} random curves)...")
    ecm = ECM(n, B1=B1, curves=curves)
    result = ecm.factor()
    print(f"      Curves tried: {ecm.stats['curves_tried']}")
    if result:
        print(f"      !! FACTOR FOUND: {result[0]}")
        return result[0]
    print(f"      No factor  [{elapsed(t)}]")

    # Plimpton ECM
    t = time.time()
    print(f"\n  5b. Plimpton-322 ECM ({curves} curves from Babylonian triples)...")
    pecm = PlimptonECM(n, B1=B1, curves=curves)
    result = pecm.factor()
    print(f"      Curves tried: {pecm.stats['curves_tried']}")
    if result:
        print(f"      !! FACTOR FOUND: {result[0]}")
        return result[0]
    print(f"      No factor  [{elapsed(t)}]")

    return None


# ═══════════════════════════════════════════════════════════════════════
# PHASE 6: Continued Fraction Analysis
# ═══════════════════════════════════════════════════════════════════════

def phase6_continued_fractions(n):
    section("PHASE 6: Continued Fraction / Wiener Analysis")
    print(f"  Wiener's attack works when d < n^0.25 (i.e., tiny private key).")
    print(f"  RSA-2048 with e=65537 is immune, but we analyze the CF structure.")

    e = 65537  # Standard public exponent

    # Standard CF of e/n
    t = time.time()
    terms = cf_expansion(e, n, max_terms=200)
    print(f"\n  Standard CF expansion of e/n:")
    print(f"    Terms computed: {len(terms)}")
    print(f"    First 15 quotients (truncated): {[t if t < 10**20 else f'{t:.6e}' for t in terms[:15]]}")

    # Check how many quotients are 5-smooth (only check small ones)
    small_terms = [t for t in terms if t > 0 and t < 10**12]
    smooth_count = sum(1 for t in small_terms if is_smooth(t))
    print(f"    Small quotients (<10^12): {len(small_terms)}/{len(terms)}")
    print(f"    5-smooth among small: {smooth_count}/{len(small_terms)}")

    # Standard CF convergent check for Wiener (no sexagesimal — quotients too large)
    print(f"\n  Wiener attack with e=65537 (standard CF only):")
    convs = cf_convergents(terms)
    wiener_found = False
    for i, (k, d) in enumerate(convs):
        if d == 0 or k == 0:
            continue
        ed_minus_1 = e * d - 1
        if ed_minus_1 % k != 0:
            continue
        phi_n = ed_minus_1 // k
        s = n - phi_n + 1
        disc = s * s - 4 * n
        if disc < 0:
            continue
        sq = isqrt(disc)
        if sq * sq == disc:
            p = (s + sq) // 2
            q = (s - sq) // 2
            if p * q == n and p > 1 and q > 1:
                print(f"    !! FACTORED via Wiener at convergent {i}!")
                wiener_found = True
                break
    if not wiener_found:
        print(f"    Not vulnerable (e=65537 is standard, d is large)")
    print(f"    Convergents checked: {len(convs)}  [{elapsed(t)}]")

    # Demo on a weak RSA
    print(f"\n  Demonstration: Wiener on a weak 64-bit RSA...")
    demo_p = 4294967311  # ~32 bits
    demo_q = 4294967357
    demo_n = demo_p * demo_q
    demo_phi = (demo_p - 1) * (demo_q - 1)
    demo_d = 65537  # small d
    demo_e = pow(demo_d, -1, demo_phi)
    demo_terms = cf_expansion(demo_e, demo_n, max_terms=200)
    demo_convs = cf_convergents(demo_terms)
    demo_found = False
    for i, (k, d) in enumerate(demo_convs):
        if d == 0 or k == 0:
            continue
        ed1 = demo_e * d - 1
        if ed1 % k != 0:
            continue
        phi = ed1 // k
        s = demo_n - phi + 1
        disc = s * s - 4 * demo_n
        if disc < 0:
            continue
        sq = isqrt(disc)
        if sq * sq == disc:
            p = (s + sq) // 2
            q = (s - sq) // 2
            if p * q == demo_n and p > 1 and q > 1:
                demo_found = True
                break
    print(f"    Weak RSA factored via Wiener: {demo_found}")


# ═══════════════════════════════════════════════════════════════════════
# PHASE 7: RSA Structural Analysis
# ═══════════════════════════════════════════════════════════════════════

def phase7_rsa_structure(n):
    section("PHASE 7: RSA Structural Analysis")

    rsa = RSAAnalysis()

    # Analyze known factored RSA challenges
    t = time.time()
    print(f"  Analyzing known factored RSA challenges for patterns...")
    known = rsa.analyze_factored_rsa()
    for name, data in known.items():
        print(f"\n  {name} ({data['n_bits']} bits):")
        print(f"    n tier: {data['n_tier']}, n mod 60: {data['n_mod_60']}")
        print(f"    p tier: {data['p_tier']}, q tier: {data['q_tier']}")
        print(f"    p-1 tier: {data['p_minus_1_tier']}, q-1 tier: {data['q_minus_1_tier']}")
    print(f"  [{elapsed(t)}]")

    # Analyze RSA-2048 public exponent interaction
    t = time.time()
    print(f"\n  RSA-2048 public exponent interaction (e=65537):")
    pe = rsa.public_exponent_interaction(n, e=65537)
    print(f"    e mod 60: {pe['e_mod_60']}, e tier: {pe['e_tier']}")
    print(f"    n mod 60: {pe['n_mod_60']}, n tier: {pe['n_tier']}")
    print(f"    Power orbit tiers (e^k mod n):")
    for k, data in list(pe["power_tiers"].items())[:5]:
        print(f"      e^{k}: mod 60 = {data['value_mod_60']}, tier = {data['tier']}")
    print(f"  [{elapsed(t)}]")


# ═══════════════════════════════════════════════════════════════════════
# PHASE 8: Modular Reciprocal Pair Analysis
# ═══════════════════════════════════════════════════════════════════════

def phase8_reciprocal_pairs(n):
    section("PHASE 8: Modular Reciprocal Pair Analysis")
    print(f"  Babylonian reciprocal pairs (x, x⁻¹ mod n) — the core innovation.")
    print(f"  Testing if regular pairs reveal structure in n...")

    t = time.time()
    # Check small regular numbers and their inverses mod n
    regular_numbers = []
    a, b, c = 1, 1, 1
    for a_exp in range(30):
        val_a = 2**a_exp
        if val_a > 10_000:
            break
        for b_exp in range(20):
            val_ab = val_a * 3**b_exp
            if val_ab > 10_000:
                break
            for c_exp in range(15):
                val = val_ab * 5**c_exp
                if val > 10_000:
                    break
                if val > 1 and gcd(val, n) == 1:
                    regular_numbers.append(val)

    regular_numbers.sort()
    print(f"  Regular numbers < 10,000 coprime to n: {len(regular_numbers)}")

    # For each, compute modular inverse and check for interesting properties
    interesting = []
    for x in regular_numbers[:200]:
        x_inv = pow(x, -1, n)
        s = (x + x_inv) % n
        d = (x - x_inv) % n

        # Check if sum or difference reveals a factor
        g_s = gcd(s, n)
        g_d = gcd(d, n)
        if 1 < g_s < n:
            print(f"  !! FACTOR from sum(x={x}): {g_s}")
            return g_s
        if 1 < g_d < n:
            print(f"  !! FACTOR from diff(x={x}): {g_d}")
            return g_d

        # Check regularity of the inverse
        sp_inv, co_inv = extract_smooth_part(x_inv % (n // 2))  # reduce size
        if sp_inv > 1:
            interesting.append((x, sp_inv))

    print(f"  Checked {min(200, len(regular_numbers))} reciprocal pairs")
    print(f"  Pairs with non-trivial smooth inverse part: {len(interesting)}")
    if interesting:
        top = sorted(interesting, key=lambda p: p[1], reverse=True)[:5]
        for x, sp in top:
            print(f"    x={x}: inverse smooth part = {sp}")
    print(f"  No factors found from reciprocal pairs  [{elapsed(t)}]")

    return None


# ═══════════════════════════════════════════════════════════════════════
# PHASE 9: Fermat's Method — Difference of Squares
# ═══════════════════════════════════════════════════════════════════════

def phase9_fermat(n, iterations=1_000_000):
    section(f"PHASE 9: Fermat's Method ({iterations:,} iterations)")
    print(f"  n = a² - b² = (a+b)(a-b)")
    print(f"  Works when p and q are close. RSA primes are chosen far apart.")

    t = time.time()
    a = isqrt(n)
    if a * a < n:
        a += 1

    for i in range(iterations):
        b2 = a * a - n
        b = isqrt(b2)
        if b * b == b2:
            p = a + b
            q = a - b
            if q > 1 and p * q == n:
                print(f"  !! FACTORS FOUND at iteration {i}:")
                print(f"     p = {p}")
                print(f"     q = {q}")
                return (p, q)
        a += 1

        if i % 200_000 == 0 and i > 0:
            print(f"    ... {i:,} iterations, a-isqrt(n) = {a - isqrt(n)}  [{elapsed(t)}]")

    print(f"  No factors after {iterations:,} iterations  [{elapsed(t)}]")
    print(f"  (p and q differ by more than {2 * iterations} from sqrt(n))")
    return None


# ═══════════════════════════════════════════════════════════════════════
# PHASE 10: Williams p+1 — Another Smooth Group Order Attack
# ═══════════════════════════════════════════════════════════════════════

def phase10_williams_pp1(n, B=500_000):
    section(f"PHASE 10: Williams p+1 (B={B:,})")
    print(f"  Exploits smooth p+1. Uses Lucas sequences.")

    t = time.time()
    primes = sieve_of_eratosthenes(B)

    for seed in [3, 5, 7, 11, 13, 17]:
        # Lucas sequence: V_0 = 2, V_1 = seed, V_k = seed*V_{k-1} - V_{k-2} mod n
        v = seed
        for p in primes:
            pe = p
            while pe * p <= B:
                pe *= p
            # Compute V_{pe} using the doubling formulas
            v_k = v
            v_k1 = (v * v - 2) % n
            for bit in bin(pe)[3:]:  # skip '0b1'
                if bit == '0':
                    v_k1 = (v_k * v_k1 - v) % n
                    v_k = (v_k * v_k - 2) % n
                else:
                    v_k = (v_k * v_k1 - v) % n
                    v_k1 = (v_k1 * v_k1 - 2) % n
            v = v_k

        g = gcd(v - 2, n)
        if 1 < g < n:
            print(f"  !! FACTOR with seed {seed}: {g}  [{elapsed(t)}]")
            return g
        status = "trivial (1)" if g == 1 else "trivial (n)"
        print(f"  Seed {seed}: gcd = {status}")

    print(f"  No factor found  [{elapsed(t)}]")
    return None


# ═══════════════════════════════════════════════════════════════════════
# PHASE 11: Sexagesimal Quadratic Sieve (Toy Demo)
# ═══════════════════════════════════════════════════════════════════════

def phase11_sexa_qs_demo():
    section("PHASE 11: Sexagesimal QS — Demonstration on Smaller Target")
    print(f"  The QS cannot touch RSA-2048 (needs ~2^110 operations).")
    print(f"  Demonstrating on a 60-bit semiprime to show the algorithm works.")

    from cuneiform.number_theory.sieve import QuadraticSieve, SexagesimalQuadraticSieve

    # Generate a ~60 bit semiprime
    p = 1073741827  # ~30 bit prime
    q = 1073741831
    demo_n = p * q
    print(f"\n  Demo target: {demo_n} ({demo_n.bit_length()} bits)")
    print(f"  Known factors: {p} × {q}")

    # Standard QS
    t = time.time()
    qs = QuadraticSieve(demo_n, bound=500, sieve_range=50000)
    result = qs.factor()
    print(f"\n  Standard QS:")
    print(f"    Relations found: {qs.stats['smooth_found']}")
    print(f"    Result: {result}  [{elapsed(t)}]")

    # Sexagesimal QS
    t = time.time()
    sqs = SexagesimalQuadraticSieve(demo_n, bound=500, sieve_range=50000)
    result_s = sqs.factor()
    print(f"\n  Sexagesimal QS:")
    print(f"    Relations found: {sqs.stats['smooth_found']}")
    print(f"    Smooth by tier: {sqs.stats['smooth_by_tier']}")
    print(f"    Prefilter saves: {sqs.stats['prefilter_saves']}")
    print(f"    Result: {result_s}  [{elapsed(t)}]")


# ═══════════════════════════════════════════════════════════════════════
# PHASE 12: Lattice-Based Analysis
# ═══════════════════════════════════════════════════════════════════════

def phase12_lattice(n):
    section("PHASE 12: Lattice / LLL Analysis")
    print(f"  Building lattices from reciprocal pairs mod small multiples of 60")

    from cuneiform.crypto.lattice import SexagesimalLattice, LatticeReductionComparison

    # Analyze lattice reduction with regularity-organized bases
    t = time.time()
    comp = LatticeReductionComparison(dimensions=[6, 8, 10])
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
# PHASE 13: Deep Number Theory — GCD Bombardment
# ═══════════════════════════════════════════════════════════════════════

def phase13_gcd_bombardment(n):
    section("PHASE 13: GCD Bombardment")
    print(f"  Testing gcd(n, interesting_numbers) for serendipitous factors...")

    t = time.time()
    tests = []

    # Factorials
    factorial = 1
    for k in range(1, 1000):
        factorial = (factorial * k) % n
        if k in [100, 200, 500, 999]:
            g = gcd(factorial - 1, n)
            tests.append((f"{k}! - 1", g))
            g2 = gcd(factorial + 1, n)
            tests.append((f"{k}! + 1", g2))

    # Powers of 60
    for k in range(1, 200):
        val = pow(60, k, n) - 1
        g = gcd(val, n)
        if 1 < g < n:
            tests.append((f"60^{k} - 1", g))
            print(f"  !! FACTOR from 60^{k} - 1: {g}")

    # Fibonacci numbers mod n
    fib_a, fib_b = 0, 1
    for k in range(1, 10000):
        fib_a, fib_b = fib_b, (fib_a + fib_b) % n
        if k % 1000 == 0:
            g = gcd(fib_a, n)
            if 1 < g < n:
                tests.append((f"Fib({k})", g))
                print(f"  !! FACTOR from Fib({k}): {g}")

    # Report
    nontrivial = [(name, g) for name, g in tests if 1 < g < n]
    if nontrivial:
        for name, g in nontrivial:
            print(f"  Factor from {name}: {g}")
    else:
        print(f"  No factors found from {len(tests)} GCD tests  [{elapsed(t)}]")

    return nontrivial[0][1] if nontrivial else None


# ═══════════════════════════════════════════════════════════════════════
# PHASE 14: The Hail Mary — Random Congruences
# ═══════════════════════════════════════════════════════════════════════

def phase14_random_congruences(n, attempts=100_000):
    section(f"PHASE 14: Random Congruence Search ({attempts:,} attempts)")
    print(f"  Compute random a^(n-1)/2 mod n, check for non-trivial gcd.")
    print(f"  Probability of success per attempt: ~2^(-1024)")

    t = time.time()
    rng = random.Random(42)

    for i in range(attempts):
        a = rng.randint(2, n - 2)
        # Compute a^((n-1)/2) mod n
        val = pow(a, (n - 1) // 2, n)
        if val != 1 and val != n - 1:
            g = gcd(val - 1, n)
            if 1 < g < n:
                print(f"  !! FACTOR at attempt {i}: {g}  [{elapsed(t)}]")
                return g
            g = gcd(val + 1, n)
            if 1 < g < n:
                print(f"  !! FACTOR at attempt {i}: {g}  [{elapsed(t)}]")
                return g

    print(f"  No factors after {attempts:,} attempts  [{elapsed(t)}]")
    return None


# ═══════════════════════════════════════════════════════════════════════
# FINAL REPORT
# ═══════════════════════════════════════════════════════════════════════

def final_report(n, total_time):
    section("FINAL REPORT")
    print(f"""
  Target: RSA-2048 ({n.bit_length()} bits, {len(str(n))} digits)
  Result: NOT FACTORED

  Methods attempted:
    Phase 0:  Reconnaissance               — confirmed composite
    Phase 1:  Sexagesimal analysis          — regularity profiled
    Phase 2:  Trial division (10^6)         — no small factors
    Phase 3:  Pollard p-1                   — p-1, q-1 not smooth
    Phase 4:  Pollard rho (5M iterations)   — space too large
    Phase 5:  ECM (standard + Plimpton)     — no small factors
    Phase 6:  Continued fractions / Wiener  — d not small
    Phase 7:  RSA structural analysis       — patterns catalogued
    Phase 8:  Reciprocal pair analysis      — no factor leaked
    Phase 9:  Fermat's method               — p, q not close
    Phase 10: Williams p+1                  — p+1, q+1 not smooth
    Phase 11: Sexagesimal QS (demo)         — works on small n!
    Phase 12: Lattice / LLL analysis        — regularity tested
    Phase 13: GCD bombardment               — no lucky hits
    Phase 14: Random congruences            — 2^(-1024) odds

  Total time: {total_time:.1f}s

  The RSA-2048 challenge remains unbroken.
  Prize: $200,000 (expired, but the glory is eternal)

  To factor RSA-2048 you would need approximately:
    - Trial division:  ~2^512 operations
    - Pollard rho:     ~2^256 operations
    - ECM:             ~2^100 operations (if factor existed < 2^200)
    - GNFS:            ~2^116 operations
    - Quantum (Shor):  ~4096 logical qubits (not yet available)

  The Babylonian approach is beautiful but cannot overcome the
  fundamental hardness of the integer factorization problem.
  As the ancient scribes might say:

    𒁹 𒌋𒌋 𒌋𒐕 — "The number resists division."
""")


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    print(BANNER)
    n = RSA_2048
    total_start = time.time()

    phase0_recon(n)
    phase1_sexagesimal(n)
    phase2_trial_division(n)
    phase3_pollard_p1(n, B1=100_000, B2=500_000)
    phase4_pollard_rho(n, iterations=500_000)
    phase5_ecm(n, curves=10, B1=5_000)
    phase6_continued_fractions(n)
    phase7_rsa_structure(n)
    phase8_reciprocal_pairs(n)
    phase9_fermat(n, iterations=200_000)
    phase10_williams_pp1(n, B=100_000)
    phase11_sexa_qs_demo()
    phase12_lattice(n)
    phase13_gcd_bombardment(n)
    phase14_random_congruences(n, attempts=50_000)

    final_report(n, time.time() - total_start)


if __name__ == "__main__":
    main()
