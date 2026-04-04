"""Cuneiform dice — simulating ancient Mesopotamian randomness.

The Babylonians used astragali (knuckle bones) and later cubic dice
for divination and games. This module simulates various dice systems
with output in sexagesimal notation and cuneiform glyphs.

Astragali have four stable faces with traditional values 1, 3, 4, 6
(corresponding to the four sides of a sheep's ankle bone).
"""

from __future__ import annotations

from cuneiform.core import Sexa
from .generator import SexaRandom


# Astragalus (knuckle bone) face values — historically attested
_ASTRAGALUS_FACES = [1, 3, 4, 6]

# Standard six-sided die
_D6_FACES = [1, 2, 3, 4, 5, 6]


class CuneiformDice:
    """Dice roller with sexagesimal output and cuneiform display.

    Supports astragali (4-faced knuckle bones), standard d6, and
    arbitrary base-60 dice (d60).

    Example::

        dice = CuneiformDice(seed=42)
        roll = dice.astragalus()    # 1, 3, 4, or 6
        d60  = dice.d60()           # 1..59 as Sexa with cuneiform
        pool = dice.roll(n=3, sides=20)  # 3d20
    """

    def __init__(self, seed: int | None = None):
        self._rng = SexaRandom(seed=seed)

    def astragalus(self) -> dict:
        """Roll a single astragalus (knuckle bone).

        Returns dict with value, sexa representation, and cuneiform glyph.
        """
        val = self._rng.choice(_ASTRAGALUS_FACES)
        s = Sexa(val)
        return {
            "value": val,
            "sexa": str(s),
            "cuneiform": s.cuneiform(),
        }

    def d6(self) -> dict:
        """Roll a standard six-sided die."""
        val = self._rng.choice(_D6_FACES)
        s = Sexa(val)
        return {
            "value": val,
            "sexa": str(s),
            "cuneiform": s.cuneiform(),
        }

    def d60(self) -> dict:
        """Roll a sexagesimal die (1-59).

        A single base-60 digit — the natural "die" for Babylonian arithmetic.
        """
        val = self._rng.randint(1, 59)
        s = Sexa(val)
        return {
            "value": val,
            "sexa": str(s),
            "cuneiform": s.cuneiform(),
        }

    def roll(self, n: int = 1, sides: int = 60) -> list[dict]:
        """Roll n dice with the given number of sides (1-indexed).

        Returns a list of roll results with total.
        """
        if n < 1:
            raise ValueError(f"Must roll at least 1 die, got {n}")
        if sides < 2:
            raise ValueError(f"Die must have at least 2 sides, got {sides}")

        results = []
        for _ in range(n):
            val = self._rng.randint(1, sides)
            s = Sexa(val)
            results.append({
                "value": val,
                "sexa": str(s),
                "cuneiform": s.cuneiform(),
            })
        return results

    def roll_total(self, n: int = 1, sides: int = 60) -> dict:
        """Roll n dice and return the total as a Sexa value."""
        rolls = self.roll(n, sides)
        total = sum(r["value"] for r in rolls)
        s = Sexa(total)
        return {
            "rolls": rolls,
            "total": total,
            "sexa": str(s),
            "cuneiform": s.cuneiform(),
        }
