"""Grover oracle gate analysis — binary vs sexagesimal smoothness oracles.

Compares the quantum circuit complexity of checking smoothness
using a binary oracle (full trial division) versus a sexagesimal oracle
(extract 5-smooth part first, then trial-divide the smaller cofactor).

Lower circuit depth = fewer error-prone quantum gates =
more feasible on near-term hardware like Google's Willow.
"""

from __future__ import annotations

import math

from cuneiform.core.smooth import extract_smooth_part


class GroverSmoothSearch:
    """Analyze quantum oracle complexity for smooth number detection.

    The oracle marks |x⟩ → -|x⟩ if Q(x) is B-smooth.
    We compare binary vs sexagesimal oracle implementations.
    """

    def oracle_binary_gates(self, num_bits: int, bound: int) -> dict:
        """Estimate quantum gates for a binary smoothness oracle.

        The oracle checks if a number (num_bits wide) is B-smooth
        by trial division by all primes up to bound.

        Gate count model:
        - Each trial division by prime p needs O(num_bits) gates
          for a modular reduction circuit
        - Number of primes up to bound ≈ bound/ln(bound)
        - Each comparison needs O(num_bits) gates
        """
        num_primes = self._prime_count(bound)
        # Modular reduction: O(num_bits^2) gates per prime (schoolbook division)
        division_gates = num_primes * num_bits * num_bits
        # Comparison circuit: O(num_bits) per check
        comparison_gates = num_primes * num_bits
        # Ancilla qubits needed for intermediate results
        ancilla = num_primes  # One flag per prime

        total = division_gates + comparison_gates

        return {
            "method": "binary_trial_division",
            "num_bits": num_bits,
            "smoothness_bound": bound,
            "num_primes_checked": num_primes,
            "division_gates": division_gates,
            "comparison_gates": comparison_gates,
            "total_gates": total,
            "ancilla_qubits": ancilla,
            "circuit_depth": division_gates,  # Sequential divisions dominate
        }

    def oracle_sexagesimal_gates(self, num_bits: int, bound: int) -> dict:
        """Estimate quantum gates for a sexagesimal smoothness oracle.

        Three-stage pipeline:
        Stage 1: Extract 5-smooth part by dividing out 2, 3, 5 (FIXED depth)
        Stage 2: Compare cofactor against bound
        Stage 3: Trial-divide cofactor by primes 7..bound (SHORTER)

        The 5-smooth extraction is fixed-depth because you only
        divide by 2, 3, and 5. This reduces the variable-depth part.
        """
        # Stage 1: Extract 5-smooth part
        # Divide by 2: at most num_bits iterations, each O(num_bits) gates
        # Divide by 3: at most num_bits * log_3(2) iterations
        # Divide by 5: at most num_bits * log_5(2) iterations
        div2_iters = num_bits
        div3_iters = math.ceil(num_bits * math.log(2) / math.log(3))
        div5_iters = math.ceil(num_bits * math.log(2) / math.log(5))

        # Each division step: O(num_bits) gates for shift/subtract
        stage1_gates = (div2_iters + div3_iters + div5_iters) * num_bits
        stage1_depth = stage1_gates  # Sequential

        # After smooth extraction, cofactor has at most
        # num_bits * (1 - log(30)/log(2^num_bits)) bits on average
        # In practice, cofactor is significantly smaller
        cofactor_bits = max(1, num_bits - math.ceil(math.log2(30) * (num_bits // 8)))

        # Stage 2: Compare cofactor to 1 (if cofactor == 1, it's B-smooth)
        stage2_gates = cofactor_bits  # Simple comparison

        # Stage 3: Trial divide cofactor by primes from 7 to bound
        # But cofactor is smaller, so divisions are cheaper
        num_primes_remaining = max(0, self._prime_count(bound) - 3)  # Exclude 2, 3, 5
        stage3_gates = num_primes_remaining * cofactor_bits * cofactor_bits
        stage3_depth = stage3_gates

        total = stage1_gates + stage2_gates + stage3_gates
        ancilla = 3 + num_primes_remaining  # 3 for smooth extraction + 1 per remaining prime

        return {
            "method": "sexagesimal_three_stage",
            "num_bits": num_bits,
            "smoothness_bound": bound,
            "cofactor_bits_estimate": cofactor_bits,
            "stage1_smooth_extraction_gates": stage1_gates,
            "stage2_comparison_gates": stage2_gates,
            "stage3_cofactor_division_gates": stage3_gates,
            "total_gates": total,
            "ancilla_qubits": ancilla,
            "circuit_depth": stage1_depth + stage2_gates + stage3_depth,
        }

    def compare_oracle_depths(self, bit_range: range | None = None,
                               bound: int = 100) -> list[dict]:
        """Compare gate counts across a range of problem sizes.

        Returns list of comparison dicts with savings percentage.
        """
        if bit_range is None:
            bit_range = range(8, 65, 8)

        results = []
        for num_bits in bit_range:
            binary = self.oracle_binary_gates(num_bits, bound)
            sexa = self.oracle_sexagesimal_gates(num_bits, bound)

            savings = 1.0 - (sexa["total_gates"] / binary["total_gates"]) \
                if binary["total_gates"] > 0 else 0.0

            results.append({
                "num_bits": num_bits,
                "binary_gates": binary["total_gates"],
                "sexa_gates": sexa["total_gates"],
                "binary_depth": binary["circuit_depth"],
                "sexa_depth": sexa["circuit_depth"],
                "gate_savings_pct": savings * 100,
                "depth_savings_pct": (
                    1.0 - sexa["circuit_depth"] / binary["circuit_depth"]
                ) * 100 if binary["circuit_depth"] > 0 else 0.0,
            })

        return results

    def grover_iterations(self, search_space: int,
                           smooth_density: float) -> dict:
        """Estimate Grover iterations needed to find a smooth number.

        search_space: size of the range to search
        smooth_density: fraction of range that is B-smooth

        Classical: O(1/density) expected trials
        Grover: O(1/sqrt(density)) iterations, each running the oracle
        """
        if smooth_density <= 0 or smooth_density > 1:
            raise ValueError("smooth_density must be in (0, 1]")

        num_marked = max(1, int(search_space * smooth_density))
        classical_expected = int(1.0 / smooth_density)
        grover_iters = math.ceil(
            (math.pi / 4) * math.sqrt(search_space / num_marked)
        )

        return {
            "search_space": search_space,
            "smooth_density": smooth_density,
            "num_smooth_in_range": num_marked,
            "classical_expected_trials": classical_expected,
            "grover_iterations": grover_iters,
            "quantum_speedup": classical_expected / grover_iters if grover_iters > 0 else 0,
        }

    @staticmethod
    def _prime_count(n: int) -> int:
        """Approximate number of primes up to n (prime counting function)."""
        if n < 2:
            return 0
        if n < 10:
            return sum(1 for p in [2, 3, 5, 7] if p <= n)
        return int(n / math.log(n))

    @staticmethod
    def empirical_smooth_density(start: int, end: int, bound: int) -> float:
        """Measure actual smooth number density in a range.

        Checks what fraction of numbers in [start, end] are B-smooth.
        """
        count = 0
        total = 0
        for n in range(max(1, start), end + 1):
            total += 1
            _, cofactor = extract_smooth_part(n)
            # Check if cofactor has all prime factors <= bound
            temp = cofactor
            for p in range(7, bound + 1, 2):
                if p * p > temp:
                    break
                while temp % p == 0:
                    temp //= p
            if temp == 1 or (temp <= bound):
                count += 1
        return count / total if total > 0 else 0.0
