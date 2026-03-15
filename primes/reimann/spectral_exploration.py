"""Spectral exploration — the Hilbert-Polya dream through CUNEIFORM.

The Hilbert-Polya conjecture: the nontrivial zeros of zeta are
eigenvalues of some self-adjoint operator. If such an operator exists,
its eigenvalues must be real, which (after change of variables)
would force all zeros onto the critical line — proving RH.

CUNEIFORM's exact rational matrices (RatMatrix) can explore finite-
dimensional analogues:

1. Build matrices whose eigenvalue distributions mimic zeta zeros
2. Study the GUE (Gaussian Unitary Ensemble) connection
3. Explore the Montgomery-Odlyzko law: zeros of zeta are statistically
   distributed like eigenvalues of random unitary matrices

This module also explores the regularity-tier structure as a
potential grading for operator construction.

DISCLAIMER: This is exploratory/educational. These finite-dimensional
toy models cannot prove RH.
"""

from __future__ import annotations

import sys
import os
from math import log, pi as PI, sqrt, cos, sin, exp
from fractions import Fraction

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from cuneiform.number_theory.primes import sieve_of_eratosthenes
from cuneiform.core.smooth import extract_smooth_part


def pair_correlation(gammas: list[float]) -> dict:
    """Compute the pair correlation of zero spacings.

    Montgomery's pair correlation conjecture (1973):
    The pair correlation function for the nontrivial zeros is

        1 - (sin(pi*u) / (pi*u))^2

    This is EXACTLY the pair correlation of eigenvalues of
    random matrices from the GUE (Gaussian Unitary Ensemble).

    This connection (Montgomery-Odlyzko law) is one of the strongest
    hints that a spectral interpretation exists.
    """
    n = len(gammas)
    if n < 2:
        return {}

    # Normalize spacings by mean spacing
    mean_spacing = (gammas[-1] - gammas[0]) / (n - 1)

    # Compute all pairwise normalized differences
    diffs = []
    for i in range(n):
        for j in range(i + 1, n):
            delta = abs(gammas[j] - gammas[i]) / mean_spacing
            diffs.append(delta)

    # Bin the pair correlation
    bins = {}
    bin_width = 0.25
    for d in diffs:
        b = int(d / bin_width)
        if b < 20:  # Only look at nearby pairs
            bins[b] = bins.get(b, 0) + 1

    # Normalize
    total = len(diffs)
    result = {}
    for b in range(20):
        u = (b + 0.5) * bin_width
        count = bins.get(b, 0)
        # Density = count / (total * bin_width)
        density = count / (total * bin_width) if total > 0 else 0

        # GUE prediction
        if u > 0.01:
            gue_pred = 1.0 - (sin(PI * u) / (PI * u)) ** 2
        else:
            gue_pred = 0.0

        result[u] = {"density": density, "gue_prediction": gue_pred}

    return result


def zero_spacing_statistics(gammas: list[float]):
    """Analyze the statistical properties of zero spacings.

    The Montgomery-Odlyzko law predicts these match GUE statistics.
    """
    print("=" * 78)
    print("ZERO SPACING STATISTICS (Montgomery-Odlyzko Law)")
    print("Do zeta zeros behave like random matrix eigenvalues?")
    print("=" * 78)
    print()

    n = len(gammas)
    spacings = [gammas[i + 1] - gammas[i] for i in range(n - 1)]
    mean_spacing = sum(spacings) / len(spacings)

    # Normalize spacings
    norm_spacings = [s / mean_spacing for s in spacings]

    print(f"Number of zeros: {n}")
    print(f"Mean spacing: {mean_spacing:.4f}")
    print(f"Expected mean spacing (from N(T)): "
          f"~{2*PI / log(gammas[-1]/(2*PI)):.4f}")
    print()

    # Nearest-neighbor spacing distribution
    print("--- Normalized nearest-neighbor spacings ---")
    print("(GUE predicts: level repulsion at s=0, peak near s~1)")
    print()

    hist_bins = [0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0]
    hist = [0] * (len(hist_bins) - 1)
    for s in norm_spacings:
        for i in range(len(hist_bins) - 1):
            if hist_bins[i] <= s < hist_bins[i + 1]:
                hist[i] += 1
                break

    for i in range(len(hist)):
        lo, hi = hist_bins[i], hist_bins[i + 1]
        count = hist[i]
        bar = "#" * (count * 3)
        print(f"  [{lo:.2f}, {hi:.2f}): {count:>3} {bar}")

    print()
    print("Key feature: LEVEL REPULSION (very few small spacings)")
    print("This is the hallmark of GUE statistics and is NOT what you'd")
    print("get from random uncorrelated points (which would show many")
    print("small spacings following a Poisson distribution).")
    print()

    # Pair correlation
    pc = pair_correlation(gammas)
    print("--- Pair correlation ---")
    print(f"{'u':>6} {'observed':>10} {'GUE pred':>10} {'match':>8}")
    print("-" * 38)

    for u in sorted(pc.keys()):
        obs = pc[u]["density"]
        pred = pc[u]["gue_prediction"]
        match = abs(obs - pred) < 0.3
        print(f"{u:>6.2f} {obs:>10.4f} {pred:>10.4f} "
              f"{'~' if match else '':>8}")

    print()
    print("With only 30 zeros, statistics are rough. Odlyzko verified")
    print("the GUE connection using millions of zeros near height 10^20.")


def regularity_graded_operator():
    """Explore a regularity-graded matrix inspired by the Hilbert-Polya idea.

    SPECULATIVE: Build a matrix M indexed by integers, where the
    (m,n) entry depends on the regularity structure of m and n.

    If such a matrix could be made self-adjoint with eigenvalues
    matching zeta zeros... that would be a proof. (It can't, from
    a finite construction. But the structure is interesting.)
    """
    print("=" * 78)
    print("REGULARITY-GRADED OPERATOR (SPECULATIVE)")
    print("Can CUNEIFORM's regularity structure inform operator construction?")
    print("=" * 78)
    print()

    N = 30  # Matrix dimension
    print(f"Building {N}x{N} matrix with regularity-dependent entries...")
    print()

    # Build matrix: M[m][n] depends on regularity of m*n and gcd(m,n)
    matrix = []
    for m in range(1, N + 1):
        row = []
        for n in range(1, N + 1):
            if m == n:
                # Diagonal: log of smooth part
                smooth, cofactor = extract_smooth_part(m)
                val = log(smooth) if smooth > 1 else 0.0
            elif m < n:
                # Off-diagonal: depends on interaction
                product = m * n
                smooth, cofactor = extract_smooth_part(product)
                # Regularity-weighted interaction
                val = log(smooth) / log(product) if product > 1 else 0.0
                # Make it decay
                val /= abs(m - n)
            else:
                # Symmetric
                product = m * n
                smooth, cofactor = extract_smooth_part(product)
                val = log(smooth) / log(product) if product > 1 else 0.0
                val /= abs(m - n)
            row.append(val)
        matrix.append(row)

    # Check symmetry (should be by construction)
    is_symmetric = all(
        abs(matrix[i][j] - matrix[j][i]) < 1e-10
        for i in range(N) for j in range(N)
    )
    print(f"Matrix is symmetric: {is_symmetric}")

    # Compute eigenvalues using power iteration (rough, since we avoid numpy)
    # Instead, just show the matrix structure
    print()
    print("Matrix structure (first 8x8 block, values * 100):")
    print()
    print("     ", end="")
    for j in range(1, 9):
        print(f"{j:>7}", end="")
    print()
    for i in range(8):
        print(f"{i+1:>3}: ", end="")
        for j in range(8):
            print(f"{matrix[i][j]*100:>7.1f}", end="")
        print()

    print()
    print("The diagonal encodes the 'smooth content' of each integer.")
    print("Off-diagonal entries measure regularity of pairwise interactions.")
    print()
    print("A REAL spectral approach to RH would need an INFINITE-dimensional")
    print("operator, not a finite matrix. Known attempts include:")
    print("  - Berry-Keating: quantization of xp (position times momentum)")
    print("  - Connes: adelic framework and trace formulas")
    print("  - de Branges: Hilbert spaces of entire functions")
    print("  - Sierra-Townsend: quantum mechanical Hamiltonians")
    print()
    print("CUNEIFORM's contribution: the regularity grading provides a")
    print("natural filtration that COULD inform how such an operator is")
    print("organized — smooth numbers vs. increasingly irregular numbers")
    print("create a hierarchy that mirrors the Euler product factorization.")


def mertens_function():
    """The Mertens function M(x) = sum_{n<=x} mu(n).

    RH is equivalent to: M(x) = O(x^(1/2 + epsilon)) for all epsilon > 0.

    The Mobius function mu(n) is deeply connected to CUNEIFORM's
    regularity decomposition:
    - mu(n) = 0 if n has any squared prime factor
    - mu(n) = (-1)^k if n is a product of k distinct primes

    So mu detects "square-free" numbers, while CUNEIFORM detects
    "smooth" numbers. Both are structural decompositions.
    """
    print("=" * 78)
    print("MERTENS FUNCTION AND RH")
    print("M(x) = sum_{n<=x} mu(n) = O(x^(1/2+eps)) iff RH")
    print("=" * 78)
    print()

    limit = 10000

    # Compute Mobius function via sieve
    mu = [0] * (limit + 1)
    mu[1] = 1
    # Simple factorization approach
    for n in range(2, limit + 1):
        temp = n
        num_factors = 0
        has_square = False
        d = 2
        while d * d <= temp:
            if temp % d == 0:
                num_factors += 1
                temp //= d
                if temp % d == 0:
                    has_square = True
                    break
            d += 1
        if has_square:
            mu[n] = 0
        else:
            if temp > 1:
                num_factors += 1
            mu[n] = (-1) ** num_factors

    # Compute Mertens function
    M = [0] * (limit + 1)
    for n in range(1, limit + 1):
        M[n] = M[n - 1] + mu[n]

    # Analyze
    print(f"{'x':>8} {'M(x)':>8} {'|M(x)|/sqrt(x)':>16} {'smooth?':>8}")
    print("-" * 44)

    checkpoints = [10, 50, 100, 500, 1000, 2000, 5000, 10000]
    for x in checkpoints:
        m_x = M[x]
        ratio = abs(m_x) / sqrt(x)
        _, cofactor = extract_smooth_part(abs(m_x)) if m_x != 0 else (0, 0)
        is_sm = cofactor <= 1 if m_x != 0 else "-"
        print(f"{x:>8} {m_x:>8} {ratio:>16.4f} {str(is_sm):>8}")

    print()
    print(f"Maximum |M(x)| / sqrt(x) for x <= {limit}: "
          f"{max(abs(M[x])/sqrt(x) for x in range(1, limit+1)):.4f}")
    print()
    print("The Mertens conjecture (|M(x)| < sqrt(x)) is FALSE —")
    print("disproved by Odlyzko & te Riele (1985). But the weaker")
    print("bound M(x) = O(x^(1/2+eps)) IS equivalent to RH.")
    print()

    # Regularity analysis of Mertens values
    smooth_count = sum(1 for x in range(1, limit + 1)
                       if M[x] != 0 and extract_smooth_part(abs(M[x]))[1] == 1)
    total_nonzero = sum(1 for x in range(1, limit + 1) if M[x] != 0)
    print(f"M(x) values that are 5-smooth: {smooth_count}/{total_nonzero} "
          f"({100*smooth_count/total_nonzero:.1f}%)")
    print("(Interesting but probably not deep — small values tend to be smooth)")


if __name__ == "__main__":
    print()
    print("RIEMANN HYPOTHESIS: SPECTRAL AND STRUCTURAL EXPLORATIONS")
    print("Using CUNEIFORM regularity framework")
    print()

    from primes.reimann.explicit_formula import KNOWN_ZERO_GAMMAS

    zero_spacing_statistics(KNOWN_ZERO_GAMMAS)
    print()
    regularity_graded_operator()
    print()
    mertens_function()
