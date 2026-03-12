"""Phase 7 tests — Experiments, CLI, Discovery Protocol, Validation.

Section 7.3: Discovery log and observation protocol
Section 7.4: Experiment runner framework
Section 7.5: Minimum viable legacy (tabulator, smooth density, CLI)
"""

import json
import subprocess
import sys
import tempfile
from fractions import Fraction
from pathlib import Path

import pytest

from cuneiform.core.rational import SexaRational
from cuneiform.core.sexagesimal import Sexa

# === Smooth Density Experiment ===

from cuneiform.experiments.smooth_density import SmoothDensityExperiment


class TestSmoothDensityExperiment:
    def test_basic_run(self):
        exp = SmoothDensityExperiment(bits=32, trials=10, seed=42)
        result = exp.run()
        assert result.total_tested > 0
        assert result.bits == 32
        assert result.trials == 10
        assert result.seed == 42

    def test_deterministic(self):
        r1 = SmoothDensityExperiment(bits=32, trials=20, seed=123).run()
        r2 = SmoothDensityExperiment(bits=32, trials=20, seed=123).run()
        assert r1.total_smooth == r2.total_smooth
        assert r1.total_tested == r2.total_tested

    def test_different_seeds(self):
        r1 = SmoothDensityExperiment(bits=32, trials=20, seed=1).run()
        r2 = SmoothDensityExperiment(bits=32, trials=20, seed=2).run()
        # Same structure, possibly different counts
        assert r1.total_tested == r2.total_tested

    def test_has_tier_results(self):
        result = SmoothDensityExperiment(bits=32, trials=50, seed=42).run()
        assert len(result.tier_results) > 0

    def test_smooth_rate_bounded(self):
        result = SmoothDensityExperiment(bits=32, trials=50, seed=42).run()
        assert 0 <= result.overall_smooth_rate <= 1

    def test_to_json(self):
        result = SmoothDensityExperiment(bits=32, trials=10, seed=42).run()
        j = result.to_json()
        parsed = json.loads(j)
        assert parsed["bits"] == 32
        assert parsed["trials"] == 10
        assert "tiers" in parsed

    def test_summary(self):
        exp = SmoothDensityExperiment(bits=32, trials=10, seed=42)
        result = exp.run()
        summary = exp.summary(result)
        assert "Smooth Density Experiment" in summary
        assert "bits=32" in summary

    def test_elapsed_time(self):
        result = SmoothDensityExperiment(bits=32, trials=10, seed=42).run()
        assert result.elapsed_seconds >= 0

    def test_larger_bits(self):
        result = SmoothDensityExperiment(bits=48, trials=5, seed=42).run()
        assert result.total_tested > 0


# === Plimpton Tabulator ===

from cuneiform.experiments.plimpton_tabulate import PlimptonTabulator


class TestPlimptonTabulator:
    def test_basic_generation(self):
        tab = PlimptonTabulator(max_regular=100)
        rows = tab.generate()
        assert len(rows) > 0

    def test_all_pythagorean(self):
        tab = PlimptonTabulator(max_regular=100)
        rows = tab.generate()
        for row in rows:
            assert row.width ** 2 + row.length ** 2 == row.diagonal ** 2

    def test_sorted_by_spread(self):
        tab = PlimptonTabulator(max_regular=100)
        rows = tab.generate()
        spreads = [Fraction(r.spread) for r in rows]
        for i in range(len(spreads) - 1):
            assert spreads[i] >= spreads[i + 1]

    def test_original_15_present(self):
        tab = PlimptonTabulator(max_regular=200)
        rows = tab.generate()
        original = [r for r in rows if r.is_original]
        assert len(original) == 15

    def test_row_numbers_sequential(self):
        tab = PlimptonTabulator(max_regular=100)
        rows = tab.generate()
        for i, row in enumerate(rows):
            assert row.row_number == i + 1

    def test_csv_output(self):
        tab = PlimptonTabulator(max_regular=50)
        csv = tab.to_csv()
        lines = csv.strip().split("\n")
        assert lines[0].startswith("row,")
        assert len(lines) > 1

    def test_json_output(self):
        tab = PlimptonTabulator(max_regular=50)
        j = tab.to_json()
        parsed = json.loads(j)
        assert isinstance(parsed, list)
        assert len(parsed) > 0
        assert "width" in parsed[0]

    def test_statistics(self):
        tab = PlimptonTabulator(max_regular=100)
        stats = tab.statistics()
        assert stats["total_rows"] > 0
        assert stats["max_regular"] == 100

    def test_larger_table(self):
        tab = PlimptonTabulator(max_regular=500)
        rows = tab.generate()
        # Should have many more rows than the original 15
        assert len(rows) > 50

    def test_p_greater_than_q(self):
        tab = PlimptonTabulator(max_regular=100)
        rows = tab.generate()
        for row in rows:
            assert row.p > row.q


# === Discovery Log ===

from cuneiform.experiments.discovery_log import DiscoveryLog, Observation


class TestDiscoveryLog:
    def test_record(self):
        log = DiscoveryLog()
        obs = log.record("test_exp", {"bits": 64}, {"rate": 0.15})
        assert obs.id == 1
        assert obs.experiment == "test_exp"
        assert not obs.is_anomalous

    def test_record_anomaly(self):
        log = DiscoveryLog()
        obs = log.record("test", {}, {}, signal_type="orthogonal")
        assert obs.is_anomalous

    def test_sequential_ids(self):
        log = DiscoveryLog()
        o1 = log.record("a", {}, {})
        o2 = log.record("b", {}, {})
        assert o2.id == o1.id + 1

    def test_flag_for_review(self):
        log = DiscoveryLog()
        obs = log.record("test", {}, {}, signal_type="emergent")
        log.flag_for_review(obs)
        assert len(log.flagged) == 1
        assert log.flagged[0].id == obs.id

    def test_mark_reproduced(self):
        log = DiscoveryLog()
        obs = log.record("test", {}, {})
        log.mark_reproduced(obs.id)
        assert obs.status == "reproduced"
        assert obs.reproduction_count == 1

    def test_mark_varied(self):
        log = DiscoveryLog()
        obs = log.record("test", {}, {})
        log.mark_varied(obs.id, "pattern persists at 128 bits")
        assert obs.status == "varied"

    def test_mark_explained(self):
        log = DiscoveryLog()
        obs = log.record("test", {}, {})
        log.mark_explained(obs.id, "known finite-size effect")
        assert obs.status == "explained"

    def test_mark_conjecture(self):
        log = DiscoveryLog()
        obs = log.record("test", {}, {}, signal_type="orthogonal")
        log.mark_conjecture(obs.id, "Tier 0 smooth rate > average by O(1/log n)")
        assert obs.status == "conjecture"

    def test_mark_dismissed(self):
        log = DiscoveryLog()
        obs = log.record("test", {}, {})
        log.mark_dismissed(obs.id, "off-by-one bug in sieve")
        assert obs.status == "dismissed"

    def test_link_observations(self):
        log = DiscoveryLog()
        o1 = log.record("exp1", {}, {})
        o2 = log.record("exp2", {}, {})
        log.link_observations(o1.id, o2.id)
        assert o2.id in o1.related_observations
        assert o1.id in o2.related_observations

    def test_search_by_experiment(self):
        log = DiscoveryLog()
        log.record("alpha", {}, {})
        log.record("beta", {}, {})
        log.record("alpha", {}, {})
        assert len(log.search(experiment="alpha")) == 2

    def test_search_by_status(self):
        log = DiscoveryLog()
        o1 = log.record("a", {}, {})
        o2 = log.record("b", {}, {})
        log.mark_reproduced(o1.id)
        assert len(log.search(status="reproduced")) == 1

    def test_summary(self):
        log = DiscoveryLog()
        log.record("a", {}, {})
        log.record("b", {}, {}, signal_type="orthogonal")
        s = log.summary()
        assert s["total_observations"] == 2
        assert s["anomalies"] == 1

    def test_json_roundtrip(self):
        log = DiscoveryLog()
        log.record("exp1", {"bits": 64}, {"rate": 0.15}, notes="interesting")
        log.record("exp2", {"bits": 128}, {"rate": 0.12})
        j = log.to_json()
        log2 = DiscoveryLog.from_json(j)
        assert len(log2.observations) == 2
        assert log2.observations[0].experiment == "exp1"

    def test_save_load(self, tmp_path):
        log = DiscoveryLog()
        log.record("test", {"x": 1}, {"y": 2})
        path = tmp_path / "log.json"
        log.save(path)
        log2 = DiscoveryLog.load(path)
        assert len(log2.observations) == 1

    def test_anomalies_property(self):
        log = DiscoveryLog()
        log.record("a", {}, {})
        log.record("b", {}, {}, signal_type="sanity_failure")
        log.record("c", {}, {}, signal_type="emergent")
        assert len(log.anomalies) == 2


# === Benchmark ===

from cuneiform.experiments.benchmark import Benchmark


class TestBenchmark:
    def test_basic(self):
        bm = Benchmark("test")
        bm.add_run({"seed": 1}, {"rate": 0.15})
        bm.add_run({"seed": 2}, {"rate": 0.14})
        bm.add_run({"seed": 3}, {"rate": 0.16})
        assert bm.num_runs == 3

    def test_metric_values(self):
        bm = Benchmark("test")
        bm.add_run({}, {"rate": 0.1})
        bm.add_run({}, {"rate": 0.2})
        assert bm.metric_values("rate") == [0.1, 0.2]

    def test_metric_stats(self):
        bm = Benchmark("test")
        for v in [0.10, 0.12, 0.11, 0.10, 0.13]:
            bm.add_run({}, {"rate": v})
        stats = bm.metric_stats("rate")
        assert stats is not None
        assert stats["n"] == 5
        assert 0.10 <= stats["mean"] <= 0.13

    def test_is_consistent(self):
        bm = Benchmark("test")
        for v in [1.00, 1.01, 0.99, 1.00, 1.01]:
            bm.add_run({}, {"rate": v})
        assert bm.is_consistent("rate", max_cv=0.05)

    def test_not_consistent(self):
        bm = Benchmark("test")
        for v in [0.1, 0.5, 0.9, 0.2, 0.8]:
            bm.add_run({}, {"rate": v})
        assert not bm.is_consistent("rate", max_cv=0.05)

    def test_compare_groups(self):
        bm = Benchmark("test")
        bm.add_run({"tier": 0}, {"rate": 0.15})
        bm.add_run({"tier": 0}, {"rate": 0.16})
        bm.add_run({"tier": 1}, {"rate": 0.12})
        bm.add_run({"tier": 1}, {"rate": 0.11})
        result = bm.compare_groups("rate", "tier")
        assert "0" in result["groups"]
        assert "1" in result["groups"]

    def test_report(self):
        bm = Benchmark("test")
        bm.add_run({}, {"rate": 0.1, "count": 100})
        bm.add_run({}, {"rate": 0.2, "count": 200})
        report = bm.report()
        assert report["num_runs"] == 2
        assert "rate" in report["metrics"]
        assert "count" in report["metrics"]

    def test_to_json(self):
        bm = Benchmark("test")
        bm.add_run({}, {"x": 1})
        bm.add_run({}, {"x": 2})
        j = bm.to_json()
        parsed = json.loads(j)
        assert parsed["name"] == "test"
        assert len(parsed["runs"]) == 2

    def test_summary_text(self):
        bm = Benchmark("test")
        bm.add_run({}, {"rate": 0.15})
        bm.add_run({}, {"rate": 0.16})
        text = bm.summary_text()
        assert "Benchmark: test" in text
        assert "rate" in text

    def test_all_metric_names(self):
        bm = Benchmark("test")
        bm.add_run({}, {"a": 1, "b": 2})
        bm.add_run({}, {"b": 3, "c": 4})
        assert bm.all_metric_names() == {"a", "b", "c"}

    def test_no_stats_single_run(self):
        bm = Benchmark("test")
        bm.add_run({}, {"rate": 0.5})
        assert bm.metric_stats("rate") is None


# === Validation ===

from cuneiform.experiments.validation import SelfValidator


class TestSelfValidator:
    def test_all_pass(self):
        v = SelfValidator()
        results = v.run_all()
        assert len(results) > 0
        for r in results:
            assert r.passed, f"Failed: {r.name} — {r.details}"

    def test_all_passed_property(self):
        v = SelfValidator()
        v.run_all()
        assert v.all_passed

    def test_num_checks(self):
        v = SelfValidator()
        v.run_all()
        assert v.num_passed >= 8

    def test_summary(self):
        v = SelfValidator()
        v.run_all()
        s = v.summary()
        assert "Validation:" in s
        assert "PASS" in s


# === CLI ===

class TestCLI:
    def test_info(self):
        result = subprocess.run(
            [sys.executable, "-m", "cuneiform", "info"],
            capture_output=True, text=True,
            cwd=str(Path(__file__).parent.parent),
        )
        assert result.returncode == 0
        assert "CUNEIFORM" in result.stdout
        assert "Modules:" in result.stdout

    def test_validate(self):
        result = subprocess.run(
            [sys.executable, "-m", "cuneiform", "validate"],
            capture_output=True, text=True,
            cwd=str(Path(__file__).parent.parent),
        )
        assert result.returncode == 0
        assert "PASS" in result.stdout

    def test_tabulate_text(self):
        result = subprocess.run(
            [sys.executable, "-m", "cuneiform", "tabulate",
             "--max-regular", "50"],
            capture_output=True, text=True,
            cwd=str(Path(__file__).parent.parent),
        )
        assert result.returncode == 0
        assert "Extended Plimpton" in result.stdout

    def test_tabulate_csv(self):
        result = subprocess.run(
            [sys.executable, "-m", "cuneiform", "tabulate",
             "--max-regular", "50", "--format", "csv"],
            capture_output=True, text=True,
            cwd=str(Path(__file__).parent.parent),
        )
        assert result.returncode == 0
        assert "row,p,q" in result.stdout

    def test_tabulate_json(self):
        result = subprocess.run(
            [sys.executable, "-m", "cuneiform", "tabulate",
             "--max-regular", "50", "--format", "json"],
            capture_output=True, text=True,
            cwd=str(Path(__file__).parent.parent),
        )
        assert result.returncode == 0
        parsed = json.loads(result.stdout)
        assert isinstance(parsed, list)

    def test_experiment_smooth_density(self):
        result = subprocess.run(
            [sys.executable, "-m", "cuneiform", "experiment",
             "smooth-density", "--bits", "32", "--trials", "5",
             "--seed", "42"],
            capture_output=True, text=True,
            cwd=str(Path(__file__).parent.parent),
        )
        assert result.returncode == 0
        assert "Smooth Density Experiment" in result.stdout

    def test_experiment_json(self):
        result = subprocess.run(
            [sys.executable, "-m", "cuneiform", "experiment",
             "smooth-density", "--bits", "32", "--trials", "5",
             "--seed", "42", "--format", "json"],
            capture_output=True, text=True,
            cwd=str(Path(__file__).parent.parent),
        )
        assert result.returncode == 0
        parsed = json.loads(result.stdout)
        assert parsed["bits"] == 32


# === Paper Pipeline ===

from cuneiform.experiments.paper_pipeline import PaperPipeline, PipelineResults


class TestPaperPipeline:
    def test_run_all(self):
        pipeline = PaperPipeline(
            bit_sizes=[32], trials_per_size=2, sieve_range=500,
            smooth_bits=32, smooth_trials=10, seed=42,
        )
        results = pipeline.run_all()
        assert isinstance(results, PipelineResults)
        assert results.elapsed_seconds > 0
        assert results.smooth_density["total_tested"] > 0
        assert len(results.rsa) > 0
        assert len(results.pqc) > 0

    def test_scaling_has_data(self):
        pipeline = PaperPipeline(
            bit_sizes=[32], trials_per_size=2, sieve_range=500,
            smooth_bits=32, smooth_trials=10, seed=42,
        )
        results = pipeline.run_all()
        assert 32 in results.scaling

    def test_generate_latex(self):
        pipeline = PaperPipeline(
            bit_sizes=[32], trials_per_size=2, sieve_range=500,
            smooth_bits=32, smooth_trials=10, seed=42,
        )
        latex = pipeline.generate_latex()
        assert r"\documentclass" in latex
        assert r"\end{document}" in latex
        # Placeholders should be replaced
        assert "[RESULTS PLACEHOLDER" not in latex
        assert "[CONCLUSION PLACEHOLDER" not in latex

    def test_latex_has_tables(self):
        pipeline = PaperPipeline(
            bit_sizes=[32], trials_per_size=2, sieve_range=500,
            smooth_bits=32, smooth_trials=10, seed=42,
        )
        latex = pipeline.generate_latex()
        assert r"\begin{tabular}" in latex
        assert "Smooth" in latex

    def test_latex_has_figures(self):
        pipeline = PaperPipeline(
            bit_sizes=[32], trials_per_size=2, sieve_range=500,
            smooth_bits=32, smooth_trials=10, seed=42,
        )
        latex = pipeline.generate_latex()
        assert r"\begin{tikzpicture}" in latex

    def test_summary(self):
        pipeline = PaperPipeline(
            bit_sizes=[32], trials_per_size=2, sieve_range=500,
            smooth_bits=32, smooth_trials=10, seed=42,
        )
        results = pipeline.run_all()
        summary = pipeline.summary(results)
        assert "Paper Pipeline Results" in summary
        assert "Scaling" in summary

    def test_pqc_in_results(self):
        pipeline = PaperPipeline(
            bit_sizes=[32], trials_per_size=2, sieve_range=500,
            smooth_bits=32, smooth_trials=10, seed=42,
        )
        results = pipeline.run_all()
        assert "Falcon-512" in results.pqc
        assert "ML-KEM-768" in results.pqc

    def test_cli_paper_summary(self):
        result = subprocess.run(
            [sys.executable, "-m", "cuneiform", "paper",
             "--bit-sizes", "32", "--trials", "2",
             "--sieve-range", "500", "--smooth-bits", "32",
             "--smooth-trials", "10", "--seed", "42",
             "--format", "summary"],
            capture_output=True, text=True,
            cwd=str(Path(__file__).parent.parent),
        )
        assert result.returncode == 0
        assert "Paper Pipeline Results" in result.stdout

    def test_cli_paper_latex(self):
        result = subprocess.run(
            [sys.executable, "-m", "cuneiform", "paper",
             "--bit-sizes", "32", "--trials", "2",
             "--sieve-range", "500", "--smooth-bits", "32",
             "--smooth-trials", "10", "--seed", "42"],
            capture_output=True, text=True,
            cwd=str(Path(__file__).parent.parent),
        )
        assert result.returncode == 0
        assert r"\documentclass" in result.stdout
        assert r"\end{document}" in result.stdout

    def test_cli_paper_output_file(self, tmp_path):
        outfile = tmp_path / "paper.tex"
        result = subprocess.run(
            [sys.executable, "-m", "cuneiform", "paper",
             "--bit-sizes", "32", "--trials", "2",
             "--sieve-range", "500", "--smooth-bits", "32",
             "--smooth-trials", "10", "--seed", "42",
             "-o", str(outfile)],
            capture_output=True, text=True,
            cwd=str(Path(__file__).parent.parent),
        )
        assert result.returncode == 0
        content = outfile.read_text()
        assert r"\documentclass" in content
