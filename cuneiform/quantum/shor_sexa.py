"""Shor's algorithm with sexagesimal QFT — classical simulation.

Compares standard binary QFT period detection against a hypothetical
base-60 QFT. The sexagesimal QFT uses frequencies organized around
base 60, naturally decomposing into 5-smooth components.

All simulation is classical — no quantum hardware needed. The point
is to analyze the number-theoretic structure of period finding through
the sexagesimal lens.
"""

from __future__ import annotations

import cmath
import math
from fractions import Fraction

from cuneiform.core.smooth import extract_smooth_part, is_smooth
from cuneiform.number_theory.regularity import RegularityClass


class SexagesimalShor:
    """Classical simulation of Shor-style period finding.

    Compares binary QFT vs sexagesimal QFT for detecting the period
    of a^r ≡ 1 (mod n).
    """

    def __init__(self, a: int, n: int):
        if math.gcd(a, n) != 1:
            raise ValueError(f"a={a} and n={n} must be coprime")
        if n < 2:
            raise ValueError(f"n must be >= 2, got {n}")
        self.a = a
        self.n = n

    def classical_period(self) -> int:
        """Find the period r such that a^r ≡ 1 (mod n). Brute force."""
        x = self.a % self.n
        for r in range(1, self.n + 1):
            if pow(self.a, r, self.n) == 1:
                return r
        raise RuntimeError(f"No period found for a={self.a}, n={self.n}")

    def simulate_binary_qft(self, num_qubits: int) -> dict[int, float]:
        """Simulate standard QFT on 2^num_qubits states.

        Returns {frequency: probability} for frequencies that would
        be measured. In real Shor, peaks appear at multiples of N/r.
        """
        N = 2 ** num_qubits
        r = self.classical_period()

        # Build the state vector |f(x)⟩ for x = 0..N-1
        # After QFT, probability of measuring frequency k is:
        # |sum_{j: a^j mod n = s} exp(2πi jk/N)|^2 / N
        # For simplicity, compute for s = 1 (the residue of a^0)
        probs = {}
        hits = [j for j in range(N) if pow(self.a, j, self.n) == 1]

        if not hits:
            hits = [0]  # At least j=0

        for k in range(N):
            amplitude = sum(
                cmath.exp(2j * cmath.pi * j * k / N)
                for j in hits
            )
            prob = abs(amplitude) ** 2 / (N * N)
            if prob > 1e-10:
                probs[k] = prob

        return probs

    def simulate_sexagesimal_qft(self, num_qudits: int) -> dict[int, float]:
        """Simulate a base-60 QFT on num_qudits (each qudit has 60 levels).

        A single qudit holds log2(60) ≈ 5.9 bits of information.
        The Fourier basis uses frequencies that are multiples of 60^k.
        """
        N = 60 ** num_qudits
        r = self.classical_period()

        hits = [j for j in range(min(N, self.n * 2)) if pow(self.a, j, self.n) == 1]
        if not hits:
            hits = [0]

        probs = {}
        # Only check frequencies near expected peaks (multiples of N/r)
        # to avoid O(N^2) explosion
        expected_spacing = N / r if r > 0 else N
        check_freqs = set()
        for m in range(r + 1):
            center = round(m * expected_spacing)
            for delta in range(-3, 4):
                f = center + delta
                if 0 <= f < N:
                    check_freqs.add(f)

        for k in check_freqs:
            amplitude = sum(
                cmath.exp(2j * cmath.pi * j * k / N)
                for j in hits
            )
            prob = abs(amplitude) ** 2 / (N * N)
            if prob > 1e-10:
                probs[k] = prob

        return probs

    def period_regularity_analysis(self) -> dict:
        """Analyze the regularity of the period and related quantities."""
        r = self.classical_period()
        rc_r = RegularityClass(r) if r > 0 else None
        rc_a = RegularityClass(self.a) if self.a > 0 else None
        rc_n = RegularityClass(self.n)

        smooth_part_r, cofactor_r = extract_smooth_part(r) if r > 0 else (0, 0)

        return {
            "a": self.a,
            "n": self.n,
            "period": r,
            "period_regularity_tier": rc_r.regularity_tier if rc_r else None,
            "period_is_regular": is_smooth(r) if r > 0 else False,
            "period_smooth_part": smooth_part_r,
            "period_cofactor": cofactor_r,
            "a_regularity_tier": rc_a.regularity_tier if rc_a else None,
            "n_regularity_tier": rc_n.regularity_tier,
            "smooth_fraction_of_period": Fraction(smooth_part_r, r) if r > 0 else Fraction(0),
        }

    def compare_qft_efficiency(self, bits: int = 8) -> dict:
        """Compare binary vs sexagesimal QFT peak detection.

        bits: information capacity (binary QFT uses 'bits' qubits,
        sexagesimal QFT uses ceil(bits/5.9) qudits).
        """
        num_qubits = bits
        num_qudits = max(1, math.ceil(bits / math.log2(60)))

        binary_probs = self.simulate_binary_qft(num_qubits)
        sexa_probs = self.simulate_sexagesimal_qft(num_qudits)

        r = self.classical_period()
        N_bin = 2 ** num_qubits
        N_sexa = 60 ** num_qudits

        # Find peak probabilities near expected period multiples
        def peak_prob(probs, N):
            if r == 0:
                return 0.0
            total = 0.0
            for m in range(1, r + 1):
                expected = round(m * N / r)
                # Check nearby frequencies
                for delta in range(-1, 2):
                    f = expected + delta
                    if f in probs:
                        total += probs[f]
            return total

        binary_peak = peak_prob(binary_probs, N_bin)
        sexa_peak = peak_prob(sexa_probs, N_sexa)

        return {
            "num_qubits": num_qubits,
            "num_qudits": num_qudits,
            "binary_dimension": N_bin,
            "sexa_dimension": N_sexa,
            "period": r,
            "binary_peak_probability": binary_peak,
            "sexa_peak_probability": sexa_peak,
            "binary_num_peaks": len(binary_probs),
            "sexa_num_peaks": len(sexa_probs),
        }


def batch_period_regularity(n: int, max_a: int = 0) -> list[dict]:
    """Analyze period regularity for all valid a < n coprime to n."""
    if max_a <= 0:
        max_a = n
    results = []
    for a in range(2, min(max_a, n)):
        if math.gcd(a, n) != 1:
            continue
        shor = SexagesimalShor(a, n)
        results.append(shor.period_regularity_analysis())
    return results
