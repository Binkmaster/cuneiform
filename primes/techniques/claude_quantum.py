"""Classical Period Detection via Modular Oscillation Analysis.

A novel factoring technique inspired by Shor's quantum algorithm, adapted
for classical computation.

Mathematical foundation:
    Shor's algorithm finds the order r of g in (Z/NZ)* using the Quantum
    Fourier Transform. Classically, we cannot find r in polynomial time,
    but we CAN detect SMALL DIVISORS of r via spectral analysis.

    The sequence s_k = g^k mod N is periodic with period r = ord(g).
    By CRT, it has "sub-periods" r_p = ord_p(g) | (p-1) and r_q | (q-1).
    When these sub-periods (or their factors) are small enough, they
    appear as peaks in the FFT power spectrum of the normalized sequence.

Novel contributions:
    1. FFT-guided period search: instead of scanning all tau values,
       the power spectrum identifies promising candidate periods in
       O(M log M) time.
    2. Autocorrelation verification: candidate periods are verified
       via batched product GCD on (s_k - s_{k+tau}) terms, which
       concentrates factor information.
    3. Multi-base consensus: periods from multiple bases g are
       cross-referenced via GCD to find common divisors that
       relate to the factorization.
    4. Shor-style extraction: for each candidate period r, test
       both gcd(g^(r/2) - 1, N) and gcd(g^(r/2) + 1, N).

    This bridges quantum and classical factoring: it applies Shor's
    mathematical framework (period -> factor) with classical spectral
    analysis replacing the QFT. It is most effective when p-1 or q-1
    has small smooth factors that create detectable spectral peaks.

Complexity: O(M log M) per base, where M is the sequence length.
    Detects factors where ord_p(g) <= M for some base g.
"""

import sys
import cmath

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent))

from cuneiform.core.accel import gcd, isqrt, powmod, is_probable_prime


# ---------------------------------------------------------------------------
# FFT — iterative radix-2 Cooley-Tukey (no numpy)
# ---------------------------------------------------------------------------

def _fft_iterative(x):
    """Iterative radix-2 FFT (Cooley-Tukey, decimation in time).

    Input length must be a power of 2.  Returns a list of complex values.
    """
    N = len(x)
    # Bit-reversal permutation
    result = list(x)
    j = 0
    for i in range(1, N):
        bit = N >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j ^= bit
        if i < j:
            result[i], result[j] = result[j], result[i]

    # Butterfly operations
    length = 2
    while length <= N:
        angle = -2.0 * cmath.pi / length
        w_base = cmath.exp(complex(0, angle))
        for start in range(0, N, length):
            w = 1
            half = length // 2
            for k in range(half):
                t = w * result[start + k + half]
                u = result[start + k]
                result[start + k] = u + t
                result[start + k + half] = u - t
                w *= w_base
        length *= 2
    return result


def _compute_power_spectrum(float_seq, M):
    """Compute |FFT|^2 of the sequence."""
    complex_seq = [complex(x) for x in float_seq]
    fft_result = _fft_iterative(complex_seq)
    return [abs(f) ** 2 for f in fft_result]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BASE_PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]


def _choose_base(n, index):
    """Choose a base for the power sequence. Use small primes.

    Returns None if the base shares a factor with n (which itself
    would reveal a factor — the caller handles that).
    """
    g = _BASE_PRIMES[index % len(_BASE_PRIMES)]
    d = gcd(g, n)
    if d != 1:
        return None
    return g


def _find_peaks(spectrum, M, num_peaks):
    """Find the strongest peaks in the power spectrum (excluding DC).

    Only examines the first half (up to Nyquist frequency).
    Returns list of (index, strength) sorted by strength descending.
    """
    indexed = [(i, spectrum[i]) for i in range(1, M // 2)]
    indexed.sort(key=lambda x: x[1], reverse=True)
    return indexed[:num_peaks]


def _small_divisors(n):
    """Return small divisors of n (up to sqrt(n), capped at 10000 trial)."""
    divs = []
    d = 2
    while d * d <= n and d < 10000:
        if n % d == 0:
            divs.append(d)
            divs.append(n // d)
        d += 1
    return sorted(set(divs))


# ---------------------------------------------------------------------------
# Main factoring function
# ---------------------------------------------------------------------------

def factor(n, *, num_bases=5, sequence_length=None, num_candidates=20):
    """Classical period detection via modular oscillation analysis.

    Parameters
    ----------
    n : int
        The integer to factor (should be an odd composite).
    num_bases : int
        Number of different bases g to try (default 5).
    sequence_length : int | None
        Length of the modular power sequence.  If None, chosen adaptively
        based on the bit-length of n, capped at 2**18.
    num_candidates : int
        Number of top FFT peaks to investigate per base (default 20).

    Returns
    -------
    tuple[int, int] | None
        A non-trivial factorisation (p, q) with p <= q, or None.
    """
    # --- Edge cases ---
    if n < 2:
        return None
    if n % 2 == 0:
        return (2, n // 2)
    # Perfect square check
    s = isqrt(n)
    if s * s == n:
        return (s, s)
    # Primality check
    if is_probable_prime(n):
        return None

    # --- Sequence length (round up to power of 2 for FFT) ---
    if sequence_length is None:
        sequence_length = min(2 ** 18, max(2 ** 12, n.bit_length() * 256))
    M = 1
    while M < sequence_length:
        M *= 2

    all_candidate_periods = []

    for base_idx in range(num_bases):
        g = _choose_base(n, base_idx)
        if g is None:
            # gcd(base, n) > 1 means we found a factor already
            d = gcd(_BASE_PRIMES[base_idx % len(_BASE_PRIMES)], n)
            if 1 < d < n:
                p, q = min(d, n // d), max(d, n // d)
                return (p, q)
            continue

        # Step 1: Generate modular power sequence  s_k = g^k mod n
        sequence = [0] * M
        val = 1
        for k in range(M):
            sequence[k] = val
            val = (val * g) % n

        # Step 2: Normalise to [0, 1) and compute power spectrum via FFT
        float_seq = [s / n for s in sequence]
        spectrum = _compute_power_spectrum(float_seq, M)

        # Step 3: Find peaks in power spectrum
        peaks = _find_peaks(spectrum, M, num_candidates)

        # Step 4: For each peak, derive candidate period and test
        for peak_idx, _strength in peaks:
            if peak_idx == 0:
                continue
            candidate_period = M // peak_idx
            if candidate_period <= 0:
                continue

            # Direct test: gcd(g^period - 1, n)
            g_period = powmod(g, candidate_period, n)
            g_test = gcd(g_period - 1, n)
            if 1 < g_test < n:
                p, q = min(g_test, n // g_test), max(g_test, n // g_test)
                return (p, q)

            # Test divisors of the candidate period (and Shor +/-1 trick)
            for d in _small_divisors(candidate_period):
                g_d = powmod(g, d, n)
                g_test = gcd(g_d - 1, n)
                if 1 < g_test < n:
                    p, q = min(g_test, n // g_test), max(g_test, n // g_test)
                    return (p, q)
                g_test = gcd(g_d + 1, n)
                if 1 < g_test < n:
                    p, q = min(g_test, n // g_test), max(g_test, n // g_test)
                    return (p, q)

            all_candidate_periods.append(candidate_period)

        # Step 5: Autocorrelation-based verification
        for candidate in sorted(set(all_candidate_periods))[:num_candidates]:
            if candidate <= 0 or candidate >= M:
                continue
            product = 1
            for k in range(min(100, M - candidate)):
                diff = (sequence[k] - sequence[k + candidate]) % n
                if diff != 0:
                    product = (product * diff) % n
            g_check = gcd(product, n)
            if 1 < g_check < n:
                p, q = min(g_check, n // g_check), max(g_check, n // g_check)
                return (p, q)

    # Step 6: Multi-base consensus
    if len(all_candidate_periods) >= 2:
        for i in range(len(all_candidate_periods)):
            for j in range(i + 1, len(all_candidate_periods)):
                d = gcd(all_candidate_periods[i], all_candidate_periods[j])
                if d > 1:
                    for base_g in range(2, 2 + num_bases):
                        if gcd(base_g, n) != 1:
                            continue
                        for delta in [d] + _small_divisors(d):
                            g_delta = powmod(base_g, delta, n)
                            test = gcd(g_delta - 1, n)
                            if 1 < test < n:
                                p, q = min(test, n // test), max(test, n // test)
                                return (p, q)
                            test = gcd(g_delta + 1, n)
                            if 1 < test < n:
                                p, q = min(test, n // test), max(test, n // test)
                                return (p, q)

    return None


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    passed = 0
    failed = 0

    def _test(label, n, expect_factors=True):
        global passed, failed
        print(f"Test: {label}")
        result = factor(n)
        if expect_factors:
            if result is not None:
                a, b = result
                assert a * b == n, f"  WRONG: {a} * {b} != {n}"
                print(f"  OK: {n} = {a} * {b}")
                passed += 1
            else:
                print(f"  FAIL: could not factor {n}")
                failed += 1
        else:
            if result is None:
                print(f"  OK: correctly returned None")
                passed += 1
            else:
                print(f"  FAIL: expected None, got {result}")
                failed += 1

    # Edge cases
    _test("n < 2", 1, expect_factors=False)
    _test("n = 0", 0, expect_factors=False)
    _test("n even", 100, expect_factors=True)
    _test("perfect square", 49, expect_factors=True)
    _test("prime", 104729, expect_factors=False)

    # Semiprime with very smooth p-1:
    # p = 257 (prime, p-1 = 256 = 2^8)
    # q = 521 (prime, q-1 = 520 = 2^3 * 5 * 13)
    _test("257 * 521 (p-1 = 2^8, very smooth)", 257 * 521)

    # Semiprime with smooth p-1:
    # p = 769 (prime, p-1 = 768 = 2^8 * 3)
    # q = 7919 (prime, q-1 = 7918 = 2 * 37 * 107)
    _test("769 * 7919 (p-1 = 2^8*3, smooth)", 769 * 7919)

    # Larger semiprime with power-of-2 p-1 (Fermat prime):
    # p = 65537 (prime, p-1 = 2^16, perfectly smooth)
    # q = 104729 (prime)
    _test("65537 * 104729 (p-1 = 2^16, Fermat prime)", 65537 * 104729)

    print(f"\n{passed} passed, {failed} failed")
