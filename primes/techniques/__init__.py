"""Factoring technique modules — consistent interface for attacking semiprimes.

Each module exposes:
    factor(n, **kwargs) -> tuple[int, int] | None

Returns (p, q) such that p * q == n, or None if no factor was found.
All techniques use cuneiform.core.accel for gmpy2-accelerated arithmetic.

Usage from primes/ scripts:
    from techniques import trial_division, pollard_rho, ecm
    result = trial_division.factor(n)
    result = pollard_rho.factor(n, iterations=10_000_000)
    result = ecm.factor(n, curves=200, B1=1_000_000)

Available techniques (by category):

  Classical:
    trial_division    — Divide by all primes up to a bound
    fermat            — Difference of squares (close factors)
    squfof            — Square form factorization (fast for <60 digits)
    hart_lehman       — Hart's one-line + Lehman's O(n^1/3) method

  Group-order:
    pollard_rho       — Birthday paradox (Brent's improvement)
    pollard_pm1       — Exploits smooth p-1
    williams_pp1      — Exploits smooth p+1 (Lucas sequences)

  Sieve-based:
    dixon             — Random squares (foundation of all sieves)
    cfrac             — Continued fraction factoring (Morrison-Brillhart)
    rational_sieve    — Historical predecessor to NFS
    quadratic_sieve   — Standard/Sexagesimal QS (cuneiform library)
    mpqs              — Multiple Polynomial Quadratic Sieve
    siqs              — Self-Initializing QS (fastest QS variant)

  Elliptic curve:
    ecm               — Standard + Plimpton-322 ECM (cuneiform library)

  RSA structural:
    wiener            — CF attack on small private exponent d
    boneh_durfee      — Extended Wiener (d < N^0.292)
    coppersmith       — Small roots mod N (partial factor knowledge)
    batch_gcd         — Shared prime detection across key sets

  Cuneiform-specific:
    reciprocal_pairs  — Babylonian reciprocal pair analysis
    gcd_bombardment   — Heuristic GCD with special sequences
    random_congruences — Random square-root witnesses

  Novel (Claude originals):
    claude_resonance  — Multi-discriminant Lucas cascade (class number heuristics)
    claude_fractal    — Multi-walk ergodic collision factoring (IFS-inspired)
    claude_quantum    — Classical period detection via FFT (Shor-inspired)
    claude_sexagesimal_cfrac — Sexagesimal CF factoring (5-smooth quotient rounding)
    claude_regularity_sieve — Regularity-guided QS with smooth-part pre-filter
    claude_babylon_gcd    — Babylonian smooth-power GCD cascade (5-smooth exponents)
"""

from . import (
    trial_division,
    fermat,
    squfof,
    hart_lehman,
    pollard_rho,
    pollard_pm1,
    williams_pp1,
    dixon,
    cfrac,
    rational_sieve,
    quadratic_sieve,
    mpqs,
    siqs,
    ecm,
    wiener,
    boneh_durfee,
    coppersmith,
    batch_gcd,
    reciprocal_pairs,
    gcd_bombardment,
    random_congruences,
    claude_resonance,
    claude_fractal,
    claude_quantum,
    claude_sexagesimal_cfrac,
    claude_regularity_sieve,
    claude_babylon_gcd,
)

ALL_TECHNIQUES = [
    trial_division,
    fermat,
    squfof,
    hart_lehman,
    pollard_rho,
    pollard_pm1,
    williams_pp1,
    dixon,
    cfrac,
    rational_sieve,
    quadratic_sieve,
    mpqs,
    siqs,
    ecm,
    wiener,
    boneh_durfee,
    coppersmith,
    batch_gcd,
    reciprocal_pairs,
    gcd_bombardment,
    random_congruences,
    claude_resonance,
    claude_fractal,
    claude_quantum,
    claude_sexagesimal_cfrac,
    claude_regularity_sieve,
    claude_babylon_gcd,
]

__all__ = [
    "trial_division",
    "fermat",
    "squfof",
    "hart_lehman",
    "pollard_rho",
    "pollard_pm1",
    "williams_pp1",
    "dixon",
    "cfrac",
    "rational_sieve",
    "quadratic_sieve",
    "mpqs",
    "siqs",
    "ecm",
    "wiener",
    "boneh_durfee",
    "coppersmith",
    "batch_gcd",
    "reciprocal_pairs",
    "gcd_bombardment",
    "random_congruences",
    "claude_resonance",
    "claude_fractal",
    "claude_quantum",
    "claude_sexagesimal_cfrac",
    "claude_regularity_sieve",
    "claude_babylon_gcd",
    "ALL_TECHNIQUES",
]
