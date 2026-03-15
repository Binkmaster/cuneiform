"""The von Mangoldt explicit formula — zeros of zeta control primes.

The explicit formula for the Chebyshev psi function is:

    psi(x) = x - sum_rho x^rho / rho - log(2*pi) - (1/2)*log(1 - x^(-2))

where the sum runs over ALL nontrivial zeros rho of zeta(s).

This is THE formula that connects RH to primes:
- Each zero rho = beta + i*gamma contributes a term of size ~x^beta
- If RH is true, beta = 1/2 for all rho, so each term is ~sqrt(x)
- If any beta > 1/2, that zero creates a larger oscillation

We use the first few KNOWN zeros (all on the critical line, verified
to enormous height) to partially reconstruct psi(x) and compare.

The known imaginary parts of the first zeros (rho = 1/2 + i*gamma):
"""

from __future__ import annotations

import sys
import os
from math import log, sqrt, pi as PI, atan2, cos, sin

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from cuneiform.number_theory.primes import sieve_of_eratosthenes

# First 30 known imaginary parts of nontrivial zeros of zeta(s)
# All have real part 1/2 (verified computationally to height > 10^13)
KNOWN_ZERO_GAMMAS = [
    14.134725141734693,
    21.022039638771555,
    25.010857580145688,
    30.424876125859513,
    32.935061587739189,
    37.586178158825671,
    40.918719012147495,
    43.327073280914999,
    48.005150881167159,
    49.773832477672302,
    52.970321477714460,
    56.446247697063394,
    59.347044002602353,
    60.831778524609809,
    65.112544048081606,
    67.079810529494173,
    69.546401711173979,
    72.067157674481907,
    75.704690699083933,
    77.144840068874805,
    79.337375020249367,
    82.910380854086030,
    84.735492980517050,
    87.425274613125229,
    88.809111207634465,
    92.491899270558484,
    94.651344040519838,
    95.870634228245309,
    98.831194218193692,
    101.317851005731220,
]


def explicit_formula_psi(x: float, num_zeros: int = 30) -> float:
    """Compute psi(x) using the explicit formula with known zeros.

    psi(x) = x - sum_{rho} x^rho / rho - log(2*pi) - (1/2)*log(1 - 1/x^2)

    Each zero rho = 1/2 + i*gamma contributes:
        x^rho / rho + x^(rho_bar) / rho_bar
        = 2 * Re(x^rho / rho)

    where x^rho = x^(1/2) * exp(i * gamma * log(x))
    so x^rho / rho = x^(1/2) * exp(i*gamma*log(x)) / (1/2 + i*gamma)
    """
    if x <= 1:
        return 0.0

    result = x  # main term
    result -= log(2 * PI)  # constant

    # Correction for trivial zeros (small for large x)
    if x > 1.01:
        result -= 0.5 * log(1.0 - 1.0 / (x * x))

    # Sum over nontrivial zeros (using known gammas, all with Re = 1/2)
    log_x = log(x)
    sqrt_x = sqrt(x)
    n_zeros = min(num_zeros, len(KNOWN_ZERO_GAMMAS))

    for gamma in KNOWN_ZERO_GAMMAS[:n_zeros]:
        # x^rho = x^(1/2 + i*gamma) = sqrt(x) * e^(i*gamma*log(x))
        theta = gamma * log_x
        # x^rho / rho where rho = 1/2 + i*gamma
        # = sqrt(x) * (cos(theta) + i*sin(theta)) / (1/2 + i*gamma)
        # Real part of this:
        denom = 0.25 + gamma * gamma  # |rho|^2
        re_term = sqrt_x * (0.5 * cos(theta) + gamma * sin(theta)) / denom
        # Factor of 2 because rho and conj(rho) both contribute
        result -= 2 * re_term

    return result


def compare_explicit_to_actual(limit: int = 1000):
    """Compare the explicit formula reconstruction to actual psi(x).

    This demonstrates how zeros of zeta literally generate the
    prime-counting oscillations.
    """
    from primes.reimann.prime_error import von_mangoldt

    print("=" * 78)
    print("EXPLICIT FORMULA: RECONSTRUCTING PRIMES FROM ZETA ZEROS")
    print("=" * 78)
    print()
    print("psi(x) = x - sum_rho x^rho/rho - log(2pi) - ...")
    print(f"Using first {len(KNOWN_ZERO_GAMMAS)} known zeros (all with Re=1/2)")
    print()

    checkpoints = [c for c in [10, 20, 50, 100, 200, 500, 1000, 2000, 5000]
                   if c <= limit]

    # Compute actual psi
    psi_actual = [0.0]
    for n in range(1, limit + 1):
        psi_actual.append(psi_actual[-1] + von_mangoldt(n))

    print(f"{'x':>8} {'psi_actual':>12} {'psi_explicit':>14} "
          f"{'psi_5zeros':>12} {'psi_15zeros':>13} {'error_30':>10}")
    print("-" * 78)

    for x in checkpoints:
        actual = psi_actual[x]
        approx_5 = explicit_formula_psi(x, num_zeros=5)
        approx_15 = explicit_formula_psi(x, num_zeros=15)
        approx_30 = explicit_formula_psi(x, num_zeros=30)
        error = actual - approx_30

        print(f"{x:>8} {actual:>12.2f} {approx_30:>14.2f} "
              f"{approx_5:>12.2f} {approx_15:>13.2f} {error:>10.2f}")

    print()
    print("As more zeros are included, the explicit formula converges to")
    print("the actual psi(x). The 'error' column shows the residual from")
    print("truncating the infinite sum over zeros.")
    print()


def zero_contribution_anatomy(x: float = 100.0):
    """Show exactly how each zero contributes to prime oscillations.

    This makes visible the 'hidden beats behind the primes' that
    the other LLM mentioned.
    """
    print("=" * 78)
    print(f"ANATOMY OF ZERO CONTRIBUTIONS AT x = {x}")
    print("Each zero rho = 1/2 + i*gamma contributes an oscillation")
    print("=" * 78)
    print()

    log_x = log(x)
    sqrt_x = sqrt(x)

    print(f"{'#':>3} {'gamma':>12} {'period':>10} {'amplitude':>12} "
          f"{'contribution':>14}")
    print("-" * 56)

    total_contribution = 0.0
    for i, gamma in enumerate(KNOWN_ZERO_GAMMAS[:20]):
        theta = gamma * log_x
        denom = 0.25 + gamma * gamma
        # Amplitude of this zero's contribution
        amplitude = sqrt_x / sqrt(denom)
        # The "period" in terms of x: the oscillation completes when
        # gamma * log(x) increases by 2*pi, so x changes by factor e^(2pi/gamma)
        period = 2 * PI / gamma  # in log(x) space
        # Actual contribution (real part)
        re_term = sqrt_x * (0.5 * cos(theta) + gamma * sin(theta)) / denom
        contribution = -2 * re_term
        total_contribution += contribution

        print(f"{i+1:>3} {gamma:>12.4f} {period:>10.4f} "
              f"{amplitude:>12.4f} {contribution:>14.4f}")

    print(f"\n{'Total zero contribution:':>40} {total_contribution:>14.4f}")
    print(f"{'Main term (x):':>40} {x:>14.4f}")
    print(f"{'Constant (-log 2pi):':>40} {-log(2*PI):>14.4f}")
    print(f"{'Predicted psi(x):':>40} "
          f"{x + total_contribution - log(2*PI):>14.4f}")
    print()
    print("The 'period' is in log(x) space: how fast this zero oscillates")
    print("as x grows. Higher zeros oscillate faster but with decreasing")
    print("amplitude (~1/gamma), creating a fractal-like staircase.")
    print()


def what_if_zero_off_line():
    """Thought experiment: what would happen if a zero were off the line?

    If rho = sigma + i*gamma with sigma > 1/2, the term x^rho / rho
    would have magnitude ~x^sigma, which grows FASTER than sqrt(x).

    This would create anomalously large oscillations in prime counting.
    """
    print("=" * 78)
    print("THOUGHT EXPERIMENT: WHAT IF A ZERO WERE OFF THE CRITICAL LINE?")
    print("=" * 78)
    print()
    print("If a zero existed at rho = sigma + i*gamma with sigma > 1/2,")
    print("it would contribute a term of size ~x^sigma to psi(x).")
    print()
    print("Example: hypothetical zero at rho = 0.75 + 14.13i")
    print("(same imaginary part as first zero, but real part 3/4 instead of 1/2)")
    print()

    print(f"{'x':>10} {'sqrt(x) term':>14} {'x^0.75 term':>14} {'ratio':>8}")
    print("-" * 50)

    for x in [100, 1000, 10000, 100000, 1000000]:
        sqrt_term = sqrt(x)
        off_term = x ** 0.75
        ratio = off_term / sqrt_term
        print(f"{x:>10} {sqrt_term:>14.2f} {off_term:>14.2f} {ratio:>8.1f}")

    print()
    print("The x^0.75 term grows as x^(1/4) relative to the sqrt(x) terms.")
    print("At x = 10^6, it's already 31.6x larger. At x = 10^12, it would")
    print("be 1000x larger. This would create visible distortions in prime")
    print("distribution that we do NOT observe.")
    print()
    print("This is the empirical evidence (not proof!) that RH is true:")
    print("the primes distribute themselves as if all zeros are on the line.")


if __name__ == "__main__":
    print()
    print("RIEMANN HYPOTHESIS: EXPLICIT FORMULA EXPLORATION")
    print("Using CUNEIFORM exact prime arithmetic + known zeta zeros")
    print()

    compare_explicit_to_actual(limit=2000)
    print()
    zero_contribution_anatomy(x=100.0)
    print()
    zero_contribution_anatomy(x=1000.0)
    print()
    what_if_zero_off_line()
