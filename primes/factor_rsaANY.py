#!/usr/bin/env python3
"""Factor any RSA modulus using the cuneiform arsenal.

Prompts the user to paste an RSA number of any size, auto-detects its bit
length, and tunes every algorithm's parameters accordingly.

Usage:
    python factor_rsaANY.py                  # default 5-minute time budget
    python factor_rsaANY.py --time 30m       # 30 minutes
    python factor_rsaANY.py --time 3600      # 1 hour (seconds)
    python factor_rsaANY.py --time=10m       # 10 minutes

The cuneiform hypothesis: base-60 representation privileges 5-smooth numbers,
and organizing algorithms around this property may expose hidden structure.
"""

import sys
import time
import random
from math import log, log2, exp, sqrt

# Add parent to path
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from cuneiform.core.accel import gcd, isqrt, powmod, invert, HAS_GMPY2

from cuneiform.core.smooth import extract_smooth_part, is_smooth, smooth_exponents
from cuneiform.core.sexagesimal import Sexa
from cuneiform.number_theory.regularity import RegularityClass, classify_regularity
from cuneiform.number_theory.primes import is_prime, sieve_of_eratosthenes
from cuneiform.number_theory.reciprocals import ModularReciprocalPair
from cuneiform.crypto.rsa_analysis import RSAAnalysis
from cuneiform.crypto.continued_fractions import (
    SexagesimalContinuedFractions, cf_expansion, cf_convergents,
)

BANNER = """
╔══════════════════════════════════════════════════════════════════════╗
║        𒀭  CUNEIFORM RSA Factorizer — Any Size                     ║
║              3,700-Year-Old Mathematics vs Modern Crypto  𒀭        ║
╚══════════════════════════════════════════════════════════════════════╝
"""


def section(title):
    print(f"\n{'─'*70}")
    print(f"  𒁹 {title}")
    print(f"{'─'*70}")


def elapsed(start):
    return f"{time.time() - start:.3f}s"


# ═══════════════════════════════════════════════════════════════════════
# PARAMETER TUNING — scale everything to the input size
# ═══════════════════════════════════════════════════════════════════════

def tune_parameters(n):
    """Return a dict of algorithm parameters tuned to the size of n."""
    bits = n.bit_length()
    digits = len(str(n))
    # Assume semiprime: each factor is roughly half the bits
    factor_bits = bits // 2
    factor_digits = digits // 2

    params = {
        "bits": bits,
        "digits": digits,
        "factor_bits": factor_bits,
        "factor_digits": factor_digits,
    }

    # Trial division — always cheap, cap the sieve
    params["trial_limit"] = 1_000_000

    # Pollard p-1
    # Effective when p-1 is B1-smooth. Scale B1 with factor size.
    if factor_digits <= 15:
        params["pm1_B1"] = 100_000
        params["pm1_B2"] = 1_000_000
    elif factor_digits <= 25:
        params["pm1_B1"] = 500_000
        params["pm1_B2"] = 5_000_000
    elif factor_digits <= 40:
        params["pm1_B1"] = 1_000_000
        params["pm1_B2"] = 10_000_000
    else:
        params["pm1_B1"] = 2_000_000
        params["pm1_B2"] = 20_000_000

    # Pollard rho — O(p^(1/2)) steps. Only realistic for small factors.
    if factor_bits <= 40:
        params["rho_iterations"] = 5_000_000
    elif factor_bits <= 50:
        params["rho_iterations"] = 10_000_000
    elif factor_bits <= 60:
        params["rho_iterations"] = 20_000_000
    else:
        # Won't succeed, but run a token amount
        params["rho_iterations"] = min(2_000_000, 2 ** min(factor_bits // 3, 24))

    # ECM — the workhorse for medium factors
    # GMP-ECM recommended B1 values by factor size (digits):
    #   20d → B1=11e3    25d → B1=5e4     30d → B1=25e4
    #   35d → B1=1e6     40d → B1=3e6     45d → B1=11e6
    #   50d → B1=43e6    55d → B1=11e7    60d → B1=26e7
    # Pure Python is ~100-1000x slower, so we use smaller bounds
    # but more curves to compensate.
    if factor_digits <= 15:
        params["ecm_B1"] = 5_000
        params["ecm_curves"] = 50
    elif factor_digits <= 20:
        params["ecm_B1"] = 10_000
        params["ecm_curves"] = 100
    elif factor_digits <= 25:
        params["ecm_B1"] = 50_000
        params["ecm_curves"] = 150
    elif factor_digits <= 30:
        params["ecm_B1"] = 250_000
        params["ecm_curves"] = 200
    elif factor_digits <= 35:
        params["ecm_B1"] = 500_000
        params["ecm_curves"] = 300
    elif factor_digits <= 40:
        params["ecm_B1"] = 1_000_000
        params["ecm_curves"] = 400
    elif factor_digits <= 50:
        params["ecm_B1"] = 2_000_000
        params["ecm_curves"] = 500
    else:
        # Very large factors — ECM unlikely in pure Python
        params["ecm_B1"] = 5_000_000
        params["ecm_curves"] = 200

    # Fermat — works when p, q are close
    if bits <= 128:
        params["fermat_iterations"] = 2_000_000
    elif bits <= 256:
        params["fermat_iterations"] = 1_000_000
    elif bits <= 512:
        params["fermat_iterations"] = 500_000
    else:
        params["fermat_iterations"] = 200_000

    # Williams p+1
    params["pp1_B"] = params["pm1_B1"]

    # Quadratic sieve — only practical in pure Python for small n
    if bits <= 80:
        params["qs_bound"] = 1_000
        params["qs_sieve_range"] = 50_000
        params["qs_skip"] = False
    elif bits <= 128:
        params["qs_bound"] = 10_000
        params["qs_sieve_range"] = 200_000
        params["qs_skip"] = False
    elif bits <= 200:
        params["qs_bound"] = 50_000
        params["qs_sieve_range"] = 500_000
        params["qs_skip"] = False
    elif bits <= 330:
        params["qs_bound"] = 500_000
        params["qs_sieve_range"] = 2_000_000
        params["qs_skip"] = False
    else:
        # Too large for pure Python QS
        params["qs_bound"] = 500_000
        params["qs_sieve_range"] = 1_000_000
        params["qs_skip"] = True

    # Random congruences
    params["random_attempts"] = 50_000

    return params


def print_parameters(params):
    """Display the auto-tuned parameters."""
    section("AUTO-TUNED PARAMETERS")
    print(f"  Input size: {params['bits']} bits, {params['digits']} digits")
    print(f"  Expected factor size: ~{params['factor_bits']} bits, ~{params['factor_digits']} digits")
    print(f"")
    print(f"  Trial division:     limit = {params['trial_limit']:,}")
    print(f"  Pollard p-1:        B1 = {params['pm1_B1']:,}, B2 = {params['pm1_B2']:,}")
    print(f"  Pollard rho:        iterations = {params['rho_iterations']:,}")
    print(f"  ECM:                B1 = {params['ecm_B1']:,}, curves = {params['ecm_curves']}")
    print(f"  Fermat:             iterations = {params['fermat_iterations']:,}")
    print(f"  Williams p+1:       B = {params['pp1_B']:,}")
    if params["qs_skip"]:
        print(f"  Quadratic sieve:    SKIPPED (too large for pure Python)")
    else:
        print(f"  Quadratic sieve:    bound = {params['qs_bound']:,}, sieve = {params['qs_sieve_range']:,}")
    print(f"  Random congruences: attempts = {params['random_attempts']:,}")


# ═══════════════════════════════════════════════════════════════════════
# PHASE 0: Reconnaissance — Know Your Enemy
# ═══════════════════════════════════════════════════════════════════════

def phase0_recon(n):
    section("PHASE 0: Reconnaissance")
    bits = n.bit_length()
    digits = len(str(n))
    print(f"  Target: {digits}-digit RSA modulus ({bits} bits)")
    print(f"  n mod 2:  {n % 2}  ({'odd ✓' if n % 2 == 1 else 'EVEN — not RSA!'})")
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

    # Primality check
    t = time.time()
    fermat = powmod(2, n - 1, n)
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

    # Sexagesimal structure
    print(f"\n  Sexagesimal structure (n mod 60^k):")
    for k in range(1, 7):
        mod = 60**k
        r = n % mod
        print(f"    n mod 60^{k} = {r:>15}  (smooth part: {extract_smooth_part(r)[0] if r > 0 else 0})")

    # Near-regular neighborhood
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
    factor_bits = n.bit_length() // 2
    print(f"  No small factors found  [{elapsed(t)}]")
    print(f"  (Factors are ~{factor_bits} bits — trial division needs ~2^{factor_bits} operations)")
    return None


# ═══════════════════════════════════════════════════════════════════════
# PHASE 3: Pollard's p-1 — Exploiting Smooth Group Orders
# ═══════════════════════════════════════════════════════════════════════

def phase3_pollard_p1(n, B1=500_000, B2=5_000_000):
    section(f"PHASE 3: Pollard p-1 (B1={B1:,}, B2={B2:,})")
    print(f"  If p-1 or q-1 is B1-smooth, this finds the factor.")

    t = time.time()
    primes = sieve_of_eratosthenes(B1)
    print(f"  Stage 1: {len(primes):,} primes, computing 2^(∏ p^e) mod n...")

    a = 2
    for p in primes:
        pe = p
        while pe * p <= B1:
            pe *= p
        a = powmod(a, pe, n)

    g = gcd(a - 1, n)
    print(f"  Stage 1 gcd: {'TRIVIAL' if g == 1 or g == n else g}  [{elapsed(t)}]")

    if 1 < g < n:
        print(f"  !! FACTOR FOUND: {g}")
        return g

    # Stage 2: check individual primes between B1 and B2
    t2 = time.time()
    print(f"  Stage 2: checking primes in ({B1:,}, {B2:,})...")
    stage2_primes = sieve_of_eratosthenes(min(B2, B1 + 2_000_000))

    product = 1
    batch_size = 500
    count = 0
    for p in stage2_primes:
        if p <= B1:
            continue
        ap = powmod(a, p, n)
        product = (product * (ap - 1)) % n
        count += 1
        if count % batch_size == 0:
            g2 = gcd(product, n)
            if 1 < g2 < n:
                print(f"  !! Stage 2 FACTOR at prime ~{p}: {g2}")
                return g2
            if g2 == n:
                for p2 in stage2_primes:
                    if p2 <= p - batch_size or p2 > p:
                        continue
                    if p2 <= B1:
                        continue
                    g3 = gcd(powmod(a, p2, n) - 1, n)
                    if 1 < g3 < n:
                        print(f"  !! Stage 2 FACTOR at prime {p2}: {g3}")
                        return g3
            product = 1

    g2 = gcd(product, n)
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
    factor_bits = n.bit_length() // 2
    print(f"  Expected: O(p^(1/2)) iterations for smallest prime p")
    print(f"  Estimated factor: ~{factor_bits} bits → need ~2^{factor_bits // 2} iterations")

    t = time.time()
    x = 2
    y = 2
    c = 1
    d = 1

    product = 1
    batch = 1000
    x_save, y_save = x, y

    expected_iters = 2 ** (factor_bits // 2)
    report_interval = max(500_000, iterations // 20)  # ~20 progress reports

    for i in range(1, iterations + 1):
        if i % batch == 1:
            x_save, y_save = x, y

        x = (x * x + c) % n
        y = (y * y + c) % n
        y = (y * y + c) % n

        diff = x - y if x > y else y - x
        if diff == 0:
            c += 1
            x = y = 2
            x_save = y_save = 2
            product = 1
            continue

        product = (product * diff) % n

        if i % batch == 0:
            d = gcd(product, n)
            if d == n:
                x2, y2 = x_save, y_save
                for j in range(batch):
                    x2 = (x2 * x2 + c) % n
                    y2 = (y2 * y2 + c) % n
                    y2 = (y2 * y2 + c) % n
                    d2 = gcd(abs(x2 - y2), n)
                    if 1 < d2 < n:
                        print(f"  !! FACTOR at iteration {i - batch + j + 1}: {d2}")
                        return d2
                c += 1
                x = y = 2
                x_save = y_save = 2
                product = 1
                continue
            if 1 < d < n:
                print(f"  !! FACTOR at iteration {i}: {d}  [{elapsed(t)}]")
                return d
            product = 1

        if i % report_interval == 0:
            pct = min(i / expected_iters * 100, 100) if expected_iters > 0 else 0
            print(f"    ... {i:,} iterations ({pct:.0f}% of expected)  [{elapsed(t)}]")

    print(f"  No factor found after {iterations:,} iterations  [{elapsed(t)}]")
    return None


# ═══════════════════════════════════════════════════════════════════════
# PHASE 5: ECM — Elliptic Curve Method (Standard + Plimpton)
# ═══════════════════════════════════════════════════════════════════════

def phase5_ecm(n, curves=50, B1=50_000):
    section(f"PHASE 5: Elliptic Curve Method ({curves} curves, B1={B1:,})")
    factor_digits = len(str(n)) // 2
    print(f"  ECM targets factors up to ~{factor_digits} digits with these bounds.")
    print(f"  Trying standard random curves and Plimpton-322-derived curves.")

    from cuneiform.number_theory.ecm import ECM, PlimptonECM

    # Standard ECM — run in small batches for progress reporting
    t = time.time()
    half_curves = max(curves // 2, 1)
    print(f"\n  5a. Standard ECM ({half_curves} random curves)...")
    report_every = max(1, half_curves // 10)  # ~10 progress reports
    curves_done = 0
    for batch_start in range(0, half_curves, report_every):
        batch_size = min(report_every, half_curves - batch_start)
        ecm = ECM(n, B1=B1, curves=batch_size)
        result = ecm.factor()
        curves_done += ecm.stats['curves_tried']
        if result:
            print(f"      !! FACTOR FOUND on curve {curves_done}: {result[0]}  [{elapsed(t)}]")
            return result[0]
        if half_curves > 5:
            print(f"      ... {curves_done}/{half_curves} curves  [{elapsed(t)}]")
    print(f"      No factor after {curves_done} curves  [{elapsed(t)}]")

    # Plimpton ECM
    t = time.time()
    print(f"\n  5b. Plimpton-322 ECM ({half_curves} curves from Babylonian triples)...")
    pecm = PlimptonECM(n, B1=B1, curves=half_curves)
    result = pecm.factor()
    total_curves = curves_done + pecm.stats['curves_tried']
    print(f"      Curves tried: {total_curves} total ({pecm.stats['curves_tried']} Plimpton)")
    if result:
        print(f"      !! FACTOR FOUND: {result[0]}  [{elapsed(t)}]")
        return result[0]
    print(f"      No factor  [{elapsed(t)}]")

    return None


# ═══════════════════════════════════════════════════════════════════════
# PHASE 6: Continued Fraction Analysis
# ═══════════════════════════════════════════════════════════════════════

def phase6_continued_fractions(n):
    section("PHASE 6: Continued Fraction / Wiener Analysis")
    print(f"  Wiener's attack works when d < n^0.25 (i.e., tiny private key).")

    e = 65537

    t = time.time()
    terms = cf_expansion(e, n, max_terms=200)
    print(f"\n  Standard CF expansion of e/n:")
    print(f"    Terms computed: {len(terms)}")
    display = [str(x) if x < 10**20 else f'{x:.6e}' for x in terms[:15]]
    print(f"    First 15 quotients: {display}")

    small_terms = [x for x in terms if 0 < x < 10**12]
    smooth_count = sum(1 for x in small_terms if is_smooth(x))
    print(f"    Small quotients (<10^12): {len(small_terms)}/{len(terms)}")
    print(f"    5-smooth among small: {smooth_count}/{len(small_terms)}")

    # Wiener attack
    print(f"\n  Wiener attack with e=65537:")
    convs = cf_convergents(terms)
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
                print(f"    p = {p}")
                print(f"    q = {q}")
                return p
    print(f"    Not vulnerable (e=65537 is standard, d is large)")
    print(f"    Convergents checked: {len(convs)}  [{elapsed(t)}]")
    return None


# ═══════════════════════════════════════════════════════════════════════
# PHASE 7: RSA Structural Analysis
# ═══════════════════════════════════════════════════════════════════════

def phase7_rsa_structure(n):
    section("PHASE 7: RSA Structural Analysis")

    rsa = RSAAnalysis()

    t = time.time()
    print(f"  Analyzing known factored RSA challenges for patterns...")
    known = rsa.analyze_factored_rsa()
    for name, data in known.items():
        print(f"\n  {name} ({data['n_bits']} bits):")
        print(f"    n tier: {data['n_tier']}, n mod 60: {data['n_mod_60']}")
        print(f"    p tier: {data['p_tier']}, q tier: {data['q_tier']}")
        print(f"    p-1 tier: {data['p_minus_1_tier']}, q-1 tier: {data['q_minus_1_tier']}")
    print(f"  [{elapsed(t)}]")

    t = time.time()
    print(f"\n  Public exponent interaction (e=65537):")
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
    regular_numbers = []
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

    interesting = []
    for x in regular_numbers[:200]:
        x_inv = invert(x, n)
        s = (x + x_inv) % n
        d = (x - x_inv) % n

        g_s = gcd(s, n)
        g_d = gcd(d, n)
        if 1 < g_s < n:
            print(f"  !! FACTOR from sum(x={x}): {g_s}")
            return g_s
        if 1 < g_d < n:
            print(f"  !! FACTOR from diff(x={x}): {g_d}")
            return g_d

        sp_inv, co_inv = extract_smooth_part(x_inv % (n // 2))
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
    print(f"  Works when p and q are close.")

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
        v = seed
        for p in primes:
            pe = p
            while pe * p <= B:
                pe *= p
            v_k = v
            v_k1 = (v * v - 2) % n
            for bit in bin(pe)[3:]:
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
# PHASE 11: Sexagesimal Quadratic Sieve
# ═══════════════════════════════════════════════════════════════════════

def phase11_sexa_qs(n, bound=500_000, sieve_range=2_000_000, skip=False):
    section("PHASE 11: Sexagesimal Quadratic Sieve")

    if skip:
        print(f"  SKIPPED — {n.bit_length()}-bit target too large for pure Python QS.")
        print(f"  QS/GNFS requires optimized C/C++ for numbers this size.")
        return None

    print(f"  Trying both standard and sexagesimal QS.")
    print(f"  Bound: {bound:,}, Sieve range: {sieve_range:,}")

    from cuneiform.number_theory.sieve import QuadraticSieve, SexagesimalQuadraticSieve

    # Warmup on a small semiprime to verify algorithm works
    print(f"\n  11a. Warmup: 60-bit semiprime")
    wp = 1073741827
    wq = 1073741831
    demo_n = wp * wq
    print(f"  Demo target: {demo_n} ({demo_n.bit_length()} bits)")

    t = time.time()
    sqs_demo = SexagesimalQuadraticSieve(demo_n, bound=500, sieve_range=50000)
    result_demo = sqs_demo.factor()
    print(f"  Sexagesimal QS result: {result_demo}  [{elapsed(t)}]")
    if result_demo:
        print(f"  Warmup PASSED — algorithm works correctly.")
    else:
        print(f"  Warmup FAILED — algorithm may have issues.")
        return None

    # Attack the real target
    print(f"\n  11b. Target ({n.bit_length()} bits, {len(str(n))} digits)")
    print(f"  (This may take a while in pure Python...)")

    # Standard QS
    t = time.time()
    print(f"\n  Standard QS:")
    qs = QuadraticSieve(n, bound=bound, sieve_range=sieve_range)
    result = qs.factor()
    print(f"    Relations found: {qs.stats['smooth_found']}")
    if result:
        print(f"    !! FACTORED: {result[0]} × {result[1]}")
        return result[0]
    print(f"    No factor  [{elapsed(t)}]")

    # Sexagesimal QS
    t = time.time()
    print(f"\n  Sexagesimal QS:")
    sqs = SexagesimalQuadraticSieve(n, bound=bound, sieve_range=sieve_range)
    result_s = sqs.factor()
    print(f"    Relations found: {sqs.stats['smooth_found']}")
    print(f"    Smooth by tier: {sqs.stats['smooth_by_tier']}")
    print(f"    Prefilter saves: {sqs.stats['prefilter_saves']}")
    if result_s:
        print(f"    !! FACTORED: {result_s[0]} × {result_s[1]}")
        return result_s[0]
    print(f"    No factor  [{elapsed(t)}]")

    return None


# ═══════════════════════════════════════════════════════════════════════
# PHASE 12: Lattice-Based Analysis
# ═══════════════════════════════════════════════════════════════════════

def phase12_lattice(n):
    section("PHASE 12: Lattice / LLL Analysis")
    print(f"  Building lattices from reciprocal pairs mod small multiples of 60")

    from cuneiform.crypto.lattice import SexagesimalLattice, LatticeReductionComparison

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
        val = powmod(60, k, n) - 1
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

    t = time.time()
    rng = random.Random(42)

    for i in range(attempts):
        a = rng.randint(2, n - 2)
        val = powmod(a, (n - 1) // 2, n)
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

def final_report(n, factor_found, total_time):
    section("FINAL REPORT")
    bits = n.bit_length()
    digits = len(str(n))
    factor_bits = bits // 2

    if factor_found:
        q = n // factor_found
        print(f"""
  Target: {digits}-digit RSA modulus ({bits} bits)
  Result: FACTORED!

    p = {factor_found}
    q = {q}
    p × q = n: {factor_found * q == n}

  Total time: {total_time:.1f}s

  The ancient scribes would be proud:
    𒁹 𒌋𒌋 𒌋𒐕 — "The number yields to division."
""")
    else:
        print(f"""
  Target: {digits}-digit RSA modulus ({bits} bits)
  Result: NOT FACTORED (in this run)

  Total time: {total_time:.1f}s

  Estimated factor size: ~{factor_bits} bits (~{digits // 2} digits)

  Complexity estimates for this target:
    - Trial division:  ~2^{factor_bits} operations
    - Pollard rho:     ~2^{factor_bits // 2} operations
    - ECM:             depends on factor smoothness
    - QS/GNFS:         sub-exponential, feasible with optimized C up to ~250 digits

  Suggestions:
    - Increase ECM bounds and curves (the most likely to succeed)
    - Use a compiled factoring library (GMP-ECM, msieve, CADO-NFS)
    - Pure Python is ~100-1000x slower than optimized C

  As the ancient scribes might say:
    𒁹 𒌋𒌋 𒌋𒐕 — "The number resists, but not forever."
""")


# ═══════════════════════════════════════════════════════════════════════
# INPUT
# ═══════════════════════════════════════════════════════════════════════

def get_rsa_number():
    """Prompt user to paste an RSA modulus."""
    print(BANNER)
    print("  Paste your RSA modulus below (decimal integer).")
    print("  It can span multiple lines — enter a blank line when done.")
    print()

    lines = []
    while True:
        try:
            line = input("  > " if not lines else "  . ").strip()
        except EOFError:
            break
        if not line and lines:
            break
        # Strip any non-digit characters (spaces, colons, 0x prefix, etc.)
        cleaned = ''.join(c for c in line if c.isdigit())
        if cleaned:
            lines.append(cleaned)

    if not lines:
        print("  No number entered. Exiting.")
        sys.exit(1)

    raw = ''.join(lines)
    try:
        n = int(raw)
    except ValueError:
        print(f"  Could not parse as integer. Exiting.")
        sys.exit(1)

    if n < 4:
        print(f"  Number too small (n={n}). Need n >= 4.")
        sys.exit(1)

    if n % 2 == 0:
        print(f"  n is even — factor is 2.")
        print(f"  2 × {n // 2}")
        sys.exit(0)

    return n


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def escalation_section(round_num, max_rounds, total_elapsed):
    """Print a prominent escalation header."""
    print(f"\n{'═'*70}")
    print(f"  𒀭 ESCALATION ROUND {round_num}/{max_rounds}  "
          f"(total elapsed: {total_elapsed:.1f}s)")
    print(f"  Retrying key methods with increased bounds...")
    print(f"{'═'*70}")


def parse_time_budget():
    """Parse --time argument from command line (in seconds or minutes)."""
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--time" and i < len(sys.argv):
            val = sys.argv[i + 1]
            # Support "5m" for minutes, "300s" or "300" for seconds
            if val.endswith("m"):
                return int(val[:-1]) * 60
            elif val.endswith("s"):
                return int(val[:-1])
            else:
                return int(val)
        if arg.startswith("--time="):
            val = arg.split("=", 1)[1]
            if val.endswith("m"):
                return int(val[:-1]) * 60
            elif val.endswith("s"):
                return int(val[:-1])
            else:
                return int(val)
    return 300  # default: 5 minutes


def main():
    n = get_rsa_number()
    params = tune_parameters(n)
    print(f"  Acceleration: {'gmpy2/GMP' if HAS_GMPY2 else 'stdlib (install gmpy2 for 5-50x speedup)'}")
    print_parameters(params)

    total_start = time.time()
    factor = None

    # Always run recon and sexagesimal analysis
    phase0_recon(n)
    phase1_sexagesimal(n)

    # Factoring phases — short-circuit on success
    factor = phase2_trial_division(n, limit=params["trial_limit"])

    if not factor:
        factor = phase3_pollard_p1(n, B1=params["pm1_B1"], B2=params["pm1_B2"])

    if not factor:
        factor = phase4_pollard_rho(n, iterations=params["rho_iterations"])

    if not factor:
        factor = phase5_ecm(n, curves=params["ecm_curves"], B1=params["ecm_B1"])

    if not factor:
        factor = phase6_continued_fractions(n)

    if not factor:
        phase7_rsa_structure(n)

    if not factor:
        factor = phase8_reciprocal_pairs(n)

    if not factor:
        result = phase9_fermat(n, iterations=params["fermat_iterations"])
        if result:
            factor = result[0] if isinstance(result, tuple) else result

    if not factor:
        factor = phase10_williams_pp1(n, B=params["pp1_B"])

    if not factor:
        factor = phase11_sexa_qs(
            n,
            bound=params["qs_bound"],
            sieve_range=params["qs_sieve_range"],
            skip=params["qs_skip"],
        )

    if not factor:
        phase12_lattice(n)

    if not factor:
        factor = phase13_gcd_bombardment(n)

    if not factor:
        factor = phase14_random_congruences(n, attempts=params["random_attempts"])

    # ═══════════════════════════════════════════════════════════════════
    # ESCALATION — retry the most promising methods with bigger bounds
    # ═══════════════════════════════════════════════════════════════════
    MAX_ESCALATION_ROUNDS = 5
    TIME_BUDGET = parse_time_budget()

    round_num = 0
    while not factor and round_num < MAX_ESCALATION_ROUNDS:
        elapsed_total = time.time() - total_start
        if elapsed_total > TIME_BUDGET:
            section("TIME BUDGET EXCEEDED")
            print(f"  Spent {elapsed_total:.1f}s (budget: {TIME_BUDGET}s). Stopping.")
            break

        round_num += 1
        multiplier = 2 ** round_num  # 2x, 4x, 8x, 16x, 32x
        time_remaining = TIME_BUDGET - elapsed_total

        escalation_section(round_num, MAX_ESCALATION_ROUNDS, elapsed_total)
        print(f"  Bounds multiplier: {multiplier}x")
        print(f"  Time remaining: {time_remaining:.0f}s")

        # --- Pollard rho (most likely to succeed with more iterations) ---
        if not factor:
            rho_iters = params["rho_iterations"] * multiplier
            print(f"\n  >> Pollard rho: {rho_iters:,} iterations ({multiplier}x)")
            factor = phase4_pollard_rho(n, iterations=rho_iters)

        # --- ECM (the workhorse — more curves AND larger B1) ---
        if not factor:
            ecm_B1 = params["ecm_B1"] * multiplier
            ecm_curves = params["ecm_curves"] * multiplier
            print(f"\n  >> ECM: B1={ecm_B1:,}, {ecm_curves} curves ({multiplier}x)")
            factor = phase5_ecm(n, curves=ecm_curves, B1=ecm_B1)

        # --- Pollard p-1 (larger B1/B2) ---
        if not factor:
            pm1_B1 = params["pm1_B1"] * multiplier
            pm1_B2 = params["pm1_B2"] * multiplier
            print(f"\n  >> Pollard p-1: B1={pm1_B1:,}, B2={pm1_B2:,} ({multiplier}x)")
            factor = phase3_pollard_p1(n, B1=pm1_B1, B2=pm1_B2)

        # --- Williams p+1 (larger B) ---
        if not factor:
            pp1_B = params["pp1_B"] * multiplier
            print(f"\n  >> Williams p+1: B={pp1_B:,} ({multiplier}x)")
            factor = phase10_williams_pp1(n, B=pp1_B)

        if not factor:
            elapsed_total = time.time() - total_start
            print(f"\n  Round {round_num} complete. "
                  f"No factor yet. Elapsed: {elapsed_total:.1f}s")

    final_report(n, factor, time.time() - total_start)


if __name__ == "__main__":
    main()
