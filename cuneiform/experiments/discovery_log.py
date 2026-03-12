"""Discovery log — structured experiment logging.

Implements the Unexpected Discovery Protocol from Phase 7 Section 7.3.
Every experiment observation is logged with enough context to reproduce
it later. When something unexpected appears, the protocol kicks in.

Usage:
    log = DiscoveryLog()
    obs = log.record(
        experiment="smooth_density",
        parameters={"bits": 64, "trials": 100},
        result={"tier_0_rate": 0.15, "tier_1_rate": 0.12},
        notes="Tier 0 consistently higher across all seeds"
    )
    if obs.is_anomalous:
        log.flag_for_review(obs)
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path


class SignalType(Enum):
    """Types of unexpected signals (from Phase 7.3)."""
    ORTHOGONAL = "orthogonal"        # Results don't match ANY hypothesis
    SANITY_FAILURE = "sanity_failure"  # Sanity check fails interestingly
    EMERGENT_STRUCTURE = "emergent"   # Debugging quantity has structure
    NONE = "none"                     # Normal result


class Status(Enum):
    """Observation lifecycle."""
    RECORDED = "recorded"
    REPRODUCED = "reproduced"
    VARIED = "varied"         # Parameters varied, pattern persists
    EXPLAINED = "explained"   # Simple explanation found
    CONJECTURE = "conjecture" # Survives disproof attempts
    DISMISSED = "dismissed"   # Bug, fluke, or known phenomenon


@dataclass
class Observation:
    """A single experiment observation."""
    id: int
    timestamp: float
    experiment: str
    parameters: dict
    result: dict
    notes: str = ""
    signal_type: str = "none"
    status: str = "recorded"
    reproduction_count: int = 0
    related_observations: list[int] = field(default_factory=list)

    @property
    def is_anomalous(self) -> bool:
        return self.signal_type != "none"

    def to_dict(self) -> dict:
        return asdict(self)


class DiscoveryLog:
    """Structured log for experiment observations.

    Follows the Phase 7.3 protocol:
    1. DOCUMENT IT IMMEDIATELY
    2. REPRODUCE IT
    3. VARY THE PARAMETERS
    4. LOOK FOR SIMPLE EXPLANATION
    5. IF NONE: formalize as conjecture
    6. A CONJECTURE IS NOT A THEOREM
    """

    def __init__(self):
        self._observations: list[Observation] = []
        self._next_id = 1
        self._flagged: list[int] = []

    @property
    def observations(self) -> list[Observation]:
        return list(self._observations)

    @property
    def flagged(self) -> list[Observation]:
        return [o for o in self._observations if o.id in self._flagged]

    @property
    def anomalies(self) -> list[Observation]:
        return [o for o in self._observations if o.is_anomalous]

    def record(self, experiment: str, parameters: dict,
               result: dict, notes: str = "",
               signal_type: str = "none") -> Observation:
        """Record an observation. Step 1 of the protocol."""
        obs = Observation(
            id=self._next_id,
            timestamp=time.time(),
            experiment=experiment,
            parameters=parameters,
            result=result,
            notes=notes,
            signal_type=signal_type,
        )
        self._observations.append(obs)
        self._next_id += 1
        return obs

    def flag_for_review(self, obs: Observation):
        """Flag an observation as needing further investigation."""
        if obs.id not in self._flagged:
            self._flagged.append(obs.id)

    def mark_reproduced(self, obs_id: int):
        """Mark an observation as reproduced. Step 2."""
        obs = self._get(obs_id)
        obs.reproduction_count += 1
        obs.status = "reproduced"

    def mark_varied(self, obs_id: int, notes: str = ""):
        """Mark that parameter variation confirmed the pattern. Step 3."""
        obs = self._get(obs_id)
        obs.status = "varied"
        if notes:
            obs.notes += f" | Variation: {notes}"

    def mark_explained(self, obs_id: int, explanation: str):
        """Mark with a simple explanation. Step 4."""
        obs = self._get(obs_id)
        obs.status = "explained"
        obs.notes += f" | Explanation: {explanation}"

    def mark_conjecture(self, obs_id: int, statement: str):
        """Promote to conjecture. Step 5."""
        obs = self._get(obs_id)
        obs.status = "conjecture"
        obs.notes += f" | Conjecture: {statement}"

    def mark_dismissed(self, obs_id: int, reason: str):
        """Dismiss as bug/fluke/known. Step 4 (negative)."""
        obs = self._get(obs_id)
        obs.status = "dismissed"
        obs.notes += f" | Dismissed: {reason}"

    def link_observations(self, obs_id1: int, obs_id2: int):
        """Link two related observations."""
        o1 = self._get(obs_id1)
        o2 = self._get(obs_id2)
        if obs_id2 not in o1.related_observations:
            o1.related_observations.append(obs_id2)
        if obs_id1 not in o2.related_observations:
            o2.related_observations.append(obs_id1)

    def search(self, experiment: str | None = None,
               status: str | None = None,
               signal_type: str | None = None) -> list[Observation]:
        """Search observations by criteria."""
        results = self._observations
        if experiment:
            results = [o for o in results if o.experiment == experiment]
        if status:
            results = [o for o in results if o.status == status]
        if signal_type:
            results = [o for o in results if o.signal_type == signal_type]
        return results

    def summary(self) -> dict:
        """Summary statistics for the log."""
        by_status = {}
        by_signal = {}
        by_experiment = {}
        for o in self._observations:
            by_status[o.status] = by_status.get(o.status, 0) + 1
            by_signal[o.signal_type] = by_signal.get(o.signal_type, 0) + 1
            by_experiment[o.experiment] = by_experiment.get(o.experiment, 0) + 1

        return {
            "total_observations": len(self._observations),
            "flagged": len(self._flagged),
            "anomalies": len(self.anomalies),
            "by_status": by_status,
            "by_signal_type": by_signal,
            "by_experiment": by_experiment,
        }

    def to_json(self, indent: int = 2) -> str:
        """Export full log as JSON."""
        return json.dumps({
            "observations": [o.to_dict() for o in self._observations],
            "flagged_ids": self._flagged,
            "summary": self.summary(),
        }, indent=indent)

    @classmethod
    def from_json(cls, data: str) -> DiscoveryLog:
        """Import log from JSON."""
        parsed = json.loads(data)
        log = cls()
        for o_data in parsed.get("observations", []):
            obs = Observation(**o_data)
            log._observations.append(obs)
            log._next_id = max(log._next_id, obs.id + 1)
        log._flagged = parsed.get("flagged_ids", [])
        return log

    def save(self, path: str | Path):
        """Save log to file."""
        Path(path).write_text(self.to_json())

    @classmethod
    def load(cls, path: str | Path) -> DiscoveryLog:
        """Load log from file."""
        return cls.from_json(Path(path).read_text())

    def _get(self, obs_id: int) -> Observation:
        for o in self._observations:
            if o.id == obs_id:
                return o
        raise KeyError(f"Observation {obs_id} not found")
