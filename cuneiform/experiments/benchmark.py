"""Benchmark framework — the "verify 10x" requirement.

When you find something, verify it 10 times on different inputs,
different seeds, different parameters. This module provides the
framework for systematic verification.

Usage:
    bm = Benchmark("smooth_density_tier_effect")
    for seed in range(10):
        result = run_experiment(seed=seed)
        bm.add_run({"seed": seed}, result)
    report = bm.report()
"""

from __future__ import annotations

import json
import statistics
import time
from dataclasses import dataclass, field, asdict


@dataclass
class BenchmarkRun:
    """A single benchmark run."""
    run_id: int
    parameters: dict
    metrics: dict
    timestamp: float
    elapsed_seconds: float = 0.0


class Benchmark:
    """Systematic benchmarking with statistical analysis.

    Collects multiple runs of the same experiment with varying
    parameters and computes consistency metrics.
    """

    def __init__(self, name: str):
        self.name = name
        self._runs: list[BenchmarkRun] = []
        self._next_id = 1

    @property
    def runs(self) -> list[BenchmarkRun]:
        return list(self._runs)

    @property
    def num_runs(self) -> int:
        return len(self._runs)

    def add_run(self, parameters: dict, metrics: dict,
                elapsed: float = 0.0) -> BenchmarkRun:
        """Add a benchmark run."""
        run = BenchmarkRun(
            run_id=self._next_id,
            parameters=parameters,
            metrics=metrics,
            timestamp=time.time(),
            elapsed_seconds=elapsed,
        )
        self._runs.append(run)
        self._next_id += 1
        return run

    def metric_values(self, metric_name: str) -> list[float]:
        """Extract all values of a named metric across runs."""
        values = []
        for run in self._runs:
            if metric_name in run.metrics:
                val = run.metrics[metric_name]
                if isinstance(val, (int, float)):
                    values.append(float(val))
        return values

    def metric_stats(self, metric_name: str) -> dict | None:
        """Compute statistics for a single metric across all runs."""
        values = self.metric_values(metric_name)
        if len(values) < 2:
            return None

        return {
            "metric": metric_name,
            "n": len(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "stdev": statistics.stdev(values),
            "min": min(values),
            "max": max(values),
            "cv": statistics.stdev(values) / statistics.mean(values)
            if statistics.mean(values) != 0 else float("inf"),
        }

    def all_metric_names(self) -> set[str]:
        """All metric names across all runs."""
        names = set()
        for run in self._runs:
            names.update(run.metrics.keys())
        return names

    def report(self) -> dict:
        """Full benchmark report with per-metric statistics."""
        metric_names = self.all_metric_names()
        metric_reports = {}
        for name in sorted(metric_names):
            stats = self.metric_stats(name)
            if stats:
                metric_reports[name] = stats

        return {
            "benchmark": self.name,
            "num_runs": self.num_runs,
            "metrics": metric_reports,
        }

    def is_consistent(self, metric_name: str,
                       max_cv: float = 0.1) -> bool:
        """Check if a metric is consistent across runs.

        Uses coefficient of variation (CV). CV < max_cv means consistent.
        Default threshold: 10% variation.
        """
        stats = self.metric_stats(metric_name)
        if stats is None:
            return False
        return stats["cv"] < max_cv

    def compare_groups(self, metric_name: str,
                        group_key: str) -> dict:
        """Compare metric values across groups defined by a parameter.

        Example: compare smooth_rate across different 'tier' values.
        """
        groups: dict[str, list[float]] = {}
        for run in self._runs:
            group_val = str(run.parameters.get(group_key, "unknown"))
            if metric_name in run.metrics:
                val = run.metrics[metric_name]
                if isinstance(val, (int, float)):
                    if group_val not in groups:
                        groups[group_val] = []
                    groups[group_val].append(float(val))

        result = {}
        for group, values in sorted(groups.items()):
            if len(values) >= 2:
                result[group] = {
                    "n": len(values),
                    "mean": statistics.mean(values),
                    "stdev": statistics.stdev(values),
                }
            elif len(values) == 1:
                result[group] = {
                    "n": 1,
                    "mean": values[0],
                    "stdev": 0.0,
                }

        return {
            "metric": metric_name,
            "group_key": group_key,
            "groups": result,
        }

    def to_json(self, indent: int = 2) -> str:
        """Export as JSON."""
        return json.dumps({
            "name": self.name,
            "runs": [asdict(r) for r in self._runs],
            "report": self.report(),
        }, indent=indent)

    def summary_text(self) -> str:
        """Human-readable summary."""
        report = self.report()
        lines = [
            f"Benchmark: {self.name}",
            f"Runs: {self.num_runs}",
            "",
        ]
        for name, stats in report["metrics"].items():
            cv_pct = stats["cv"] * 100
            lines.append(
                f"  {name}: mean={stats['mean']:.4f} "
                f"±{stats['stdev']:.4f} "
                f"(CV={cv_pct:.1f}%, n={stats['n']})"
            )
        return "\n".join(lines)
