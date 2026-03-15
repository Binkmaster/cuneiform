"""Prime counting error analysis — what RH means for prime distribution.

The Riemann Hypothesis is equivalent to the statement:

    |pi(x) - Li(x)| = O(sqrt(x) * log(x))

where pi(x) = #{primes <= x} and Li(x) = integral from 2 to x of dt/ln(t).

This module uses CUNEIFORM's exact prime sieve to compute the actual error
and compare it to the sqrt(x) bound that RH predicts.

We also compute psi(x) = sum_{n<=x} Lambda(n) and its deviation from x,
which is more natural for the explicit formula.
"""

from __future__ import annotations

import sys
import os
from math import log, sqrt, isqrt
from fractions import Fraction

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from cuneiform.number_theory.primes import sieve_of_eratosthenes, is_prime
from cuneiform.core.smooth import extract_smooth_part


def pi(x: int) -> int:
    """Prime counting function: number of primes <= x."""
    if x < 2:
        return 0
    return len(sieve_of_eratosthenes(x))


def li(x: float) -> float:
    """Logarithmic integral Li(x) = integral from 2 to x of dt/ln(t).

    Computed by numerical integration (Simpson's rule).
    """
    if x <= 2.0:
        return 0.0
    n_steps = max(1000, int(x))
    n_steps = min(n_steps, 100000)  # cap for performance
    h = (x - 2.0) / n_steps
    total = 0.0
    for i in range(n_steps):
        t0 = 2.0 + i * h
        t1 = t0 + h
        tm = (t0 + t1) / 2.0
        # Simpson's rule on each subinterval
        f0 = 1.0 / log(t0) if t0 > 1.0 else 0.0
        fm = 1.0 / log(tm) if tm > 1.0 else 0.0
        f1 = 1.0 / log(t1) if t1 > 1.0 else 0.0
        total += (h / 6.0) * (f0 + 4 * fm + f1)
    return total


def von_mangoldt(n: int) -> float:
    """Von Mangoldt function Lambda(n).

    Lambda(n) = log(p) if n = p^k for some prime p and k >= 1, else 0.
    """
    if n <= 1:
        return 0.0
    # Check if n is a prime power
    # First check if n itself is prime
    if is_prime(n):
        return log(n)
    # Check if n = p^k for small primes
    for p in range(2, isqrt(n) + 1):
        if n % p == 0:
            # Check if n is a power of p
            m = n
            while m % p == 0:
                m //= p
            if m == 1:
                return log(p)
            return 0.0  # n has multiple distinct prime factors
    return 0.0


def psi(x: int) -> float:
    """Chebyshev psi function: psi(x) = sum_{n<=x} Lambda(n).

    This is the "natural" prime counting function for the explicit formula.
    RH is equivalent to: psi(x) = x + O(sqrt(x) * log^2(x))
    """
    return sum(von_mangoldt(n) for n in range(1, x + 1))


def prime_error_analysis(limit: int = 10000, checkpoints: list[int] | None = None):
    """Analyze prime counting error at various scales.

    Shows |pi(x) - Li(x)| / sqrt(x) at each checkpoint.
    If RH is true, this ratio should stay bounded (grow at most like log(x)).
    """
    if checkpoints is None:
        checkpoints = [100, 500, 1000, 2000, 5000, 10000, 50000, 100000]
        checkpoints = [c for c in checkpoints if c <= limit]

    primes = sieve_of_eratosthenes(limit)
    prime_set = set(primes)

    print("=" * 72)
    print("PRIME COUNTING ERROR ANALYSIS")
    print("If RH is true: |pi(x) - Li(x)| / sqrt(x) should be O(log(x))")
    print("=" * 72)
    print()
    print(f"{'x':>10} {'pi(x)':>10} {'Li(x)':>12} {'error':>10} "
          f"{'|err|/sqrt(x)':>14} {'log(x)':>8}")
    print("-" * 72)

    pi_count = 0
    prime_idx = 0

    for x in checkpoints:
        # Count primes up to x
        while prime_idx < len(primes) and primes[prime_idx] <= x:
            prime_idx += 1
        pi_count = prime_idx

        li_x = li(x)
        error = pi_count - li_x
        normalized = abs(error) / sqrt(x) if x > 0 else 0
        log_x = log(x) if x > 1 else 0

        print(f"{x:>10} {pi_count:>10} {li_x:>12.2f} {error:>10.2f} "
              f"{normalized:>14.4f} {log_x:>8.2f}")

    print()
    print("Note: The normalized error |pi(x) - Li(x)| / sqrt(x) staying")
    print("  bounded by C * log(x) for some constant C is EQUIVALENT to RH.")
    print()

    return primes


def regularity_of_prime_gaps(primes: list[int]):
    """Analyze prime gaps through CUNEIFORM's regularity lens.

    Prime gaps g = p_{n+1} - p_n. CUNEIFORM decomposes each gap as
    g = smooth_part * cofactor. If gaps have high smooth parts, the
    primes are "aligned" with the sexagesimal grid.
    """
    print("=" * 72)
    print("PRIME GAP REGULARITY ANALYSIS (CUNEIFORM)")
    print("Decompose each prime gap as: gap = smooth_part * cofactor")
    print("=" * 72)
    print()

    gap_stats = {0: 0, 1: 0, 2: 0}  # cofactor size buckets
    total_gaps = 0
    total_smooth_ratio = Fraction(0)

    for i in range(len(primes) - 1):
        gap = primes[i + 1] - primes[i]
        if gap <= 0:
            continue
        smooth_part, cofactor = extract_smooth_part(gap)
        total_gaps += 1
        ratio = Fraction(smooth_part, gap)
        total_smooth_ratio += ratio

        if cofactor == 1:
            gap_stats[0] += 1  # fully smooth gap
        elif cofactor < 50:
            gap_stats[1] += 1  # near-smooth gap
        else:
            gap_stats[2] += 1  # non-smooth gap

    if total_gaps == 0:
        print("Not enough primes for gap analysis.")
        return

    print(f"Total prime gaps analyzed: {total_gaps}")
    print(f"Fully smooth gaps (cofactor=1): {gap_stats[0]} "
          f"({100*gap_stats[0]/total_gaps:.1f}%)")
    print(f"Near-smooth gaps (cofactor<50):  {gap_stats[1]} "
          f"({100*gap_stats[1]/total_gaps:.1f}%)")
    print(f"Non-smooth gaps:                 {gap_stats[2]} "
          f"({100*gap_stats[2]/total_gaps:.1f}%)")
    print(f"Average smooth fraction of gap:  "
          f"{float(total_smooth_ratio / total_gaps):.4f}")
    print()
    print("Note: Prime gaps are ALWAYS even (except the gap 3->5=2 and 2->3=1),")
    print("  so they always have at least one factor of 2. Gaps divisible by 6")
    print("  (= 2*3) are 'more regular' in sexagesimal terms.")

    # Count gaps divisible by 6, 30, 60
    div6 = sum(1 for i in range(len(primes)-1)
               if (primes[i+1] - primes[i]) % 6 == 0)
    div30 = sum(1 for i in range(len(primes)-1)
                if (primes[i+1] - primes[i]) % 30 == 0)
    div60 = sum(1 for i in range(len(primes)-1)
                if (primes[i+1] - primes[i]) % 60 == 0)

    print(f"\nGaps divisible by  6: {div6} ({100*div6/total_gaps:.1f}%)")
    print(f"Gaps divisible by 30: {div30} ({100*div30/total_gaps:.1f}%)")
    print(f"Gaps divisible by 60: {div60} ({100*div60/total_gaps:.1f}%)")
    print()


def psi_error_analysis(limit: int = 5000):
    """Analyze psi(x) - x, the error in the Chebyshev function.

    This is the most direct manifestation of zeta zeros:
    psi(x) - x = -sum_rho x^rho / rho + lower order terms

    If RH holds, each x^rho term has |x^rho| = x^(1/2), giving
    psi(x) = x + O(sqrt(x) * log^2(x)).
    """
    print("=" * 72)
    print("CHEBYSHEV PSI ERROR ANALYSIS")
    print("psi(x) = x + O(sqrt(x) * log^2(x)) iff RH is true")
    print("=" * 72)
    print()

    checkpoints = [c for c in [50, 100, 200, 500, 1000, 2000, 5000]
                   if c <= limit]

    print(f"{'x':>8} {'psi(x)':>12} {'x':>8} {'psi(x)-x':>12} "
          f"{'|err|/sqrt(x)':>14}")
    print("-" * 60)

    for x in checkpoints:
        psi_x = psi(x)
        error = psi_x - x
        normalized = abs(error) / sqrt(x)
        print(f"{x:>8} {psi_x:>12.2f} {x:>8} {error:>12.2f} "
              f"{normalized:>14.4f}")

    print()
    print("The normalized error |psi(x) - x| / sqrt(x) should be")
    print("  bounded by C * log^2(x) if RH is true.")
    print()


if __name__ == "__main__":
    print()
    print("RIEMANN HYPOTHESIS: PRIME DISTRIBUTION ERROR ANALYSIS")
    print("Using CUNEIFORM exact prime arithmetic")
    print()

    # Phase 1: Prime counting error
    primes = prime_error_analysis(limit=100000)

    print()

    # Phase 2: Regularity of prime gaps
    regularity_of_prime_gaps(primes[:5000])

    # Phase 3: Chebyshev psi analysis (slower, smaller range)
    psi_error_analysis(limit=2000)
