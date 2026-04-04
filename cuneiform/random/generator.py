"""Sexagesimal Linear Congruential Generator (LCG).

A pseudorandom number generator that operates natively in base-60.
The state, multiplier, increment, and modulus are all expressed as
sexagesimal values. This mirrors how a Babylonian mathematician
might have conceived of generating "unpredictable" sequences using
only tablet-friendly arithmetic.

The default parameters use regular (5-smooth) numbers so that all
intermediate values have terminating sexagesimal expansions:

    modulus     = 60^4 = 12,960,000   (Plato's nuptial number!)
    multiplier = 3,541                (a = 59*60 + 1 = 0;59,1 — near-full-cycle)
    increment  = 1                    (odd, coprime to modulus)

These satisfy the Hull-Dobell theorem requirements for a full-period LCG:
    1. c and m are coprime                 (1 and 60^4 — yes)
    2. a-1 is divisible by all prime       (3540 = 2^2 * 3 * 5 * 59;
       factors of m                         m = 2^4 * 3^4 * 5^4 — needs 2,3,5 — yes)
    3. if 4 divides m, then 4 divides a-1  (4 | 12960000 and 4 | 3540 — yes)
"""

from __future__ import annotations

import os
import time
from fractions import Fraction

from cuneiform.core import Sexa


# Default LCG parameters (all 5-smooth friendly).
_DEFAULT_MODULUS = 60 ** 4          # 12,960,000
_DEFAULT_MULTIPLIER = 59 * 60 + 1  # 3,541
_DEFAULT_INCREMENT = 1


class SexaRandom:
    """Sexagesimal pseudorandom number generator.

    Uses a Linear Congruential Generator with base-60 aligned parameters.
    Produces Sexa values in the range [0, 1) with configurable fractional
    digit precision, or integer Sexa values in arbitrary ranges.

    Example::

        rng = SexaRandom(seed=42)
        print(rng.sexa())        # random Sexa in [0, 1)
        print(rng.randint(1, 60))  # random int 1..60
        print(rng.choice([Sexa(1), Sexa(2), Sexa(30)]))
    """

    def __init__(
        self,
        seed: int | None = None,
        *,
        modulus: int = _DEFAULT_MODULUS,
        multiplier: int = _DEFAULT_MULTIPLIER,
        increment: int = _DEFAULT_INCREMENT,
    ):
        self._m = modulus
        self._a = multiplier
        self._c = increment

        if seed is None:
            seed = self._auto_seed()
        self._state = seed % self._m

    @staticmethod
    def _auto_seed() -> int:
        """Derive a seed from OS entropy and current time."""
        return int.from_bytes(os.urandom(4), "big") ^ int(time.time() * 1000) & 0xFFFFFFFF

    def _next(self) -> int:
        """Advance the LCG state and return the raw integer."""
        self._state = (self._a * self._state + self._c) % self._m
        return self._state

    # --- Public API ---

    def raw(self) -> int:
        """Return the next raw integer in [0, modulus)."""
        return self._next()

    def sexa(self, digits: int = 4) -> Sexa:
        """Generate a random Sexa value in [0, 1) with *digits* fractional places.

        Each fractional sexagesimal digit is independently drawn from [0, 59].
        """
        value = Fraction(0)
        place = Fraction(1, 60)
        for _ in range(digits):
            d = self._next() % 60
            value += d * place
            place /= 60
        return Sexa._from_frac(value)

    def randint(self, lo: int, hi: int) -> int:
        """Return a random integer N such that lo <= N <= hi."""
        if lo > hi:
            raise ValueError(f"lo ({lo}) must be <= hi ({hi})")
        span = hi - lo + 1
        return lo + self._next() % span

    def sexa_int(self, lo: int = 0, hi: int = 59) -> Sexa:
        """Return a random Sexa integer in [lo, hi]."""
        return Sexa(self.randint(lo, hi))

    def choice(self, seq):
        """Return a random element from a non-empty sequence."""
        if not seq:
            raise IndexError("Cannot choose from an empty sequence")
        return seq[self._next() % len(seq)]

    def shuffle(self, seq: list) -> None:
        """Shuffle a list in place (Fisher-Yates)."""
        for i in range(len(seq) - 1, 0, -1):
            j = self._next() % (i + 1)
            seq[i], seq[j] = seq[j], seq[i]

    def sample(self, seq, k: int) -> list:
        """Return k unique random elements from seq."""
        pool = list(seq)
        if k > len(pool):
            raise ValueError(f"Sample size {k} exceeds population {len(pool)}")
        self.shuffle(pool)
        return pool[:k]

    def seed(self, s: int) -> None:
        """Reset the generator state."""
        self._state = s % self._m

    @property
    def state(self) -> int:
        """Current internal state (for serialization/debugging)."""
        return self._state
