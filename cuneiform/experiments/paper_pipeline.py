"""Paper pipeline — run experiments and generate a complete LaTeX paper.

Orchestrates the smooth density experiment, scaling analysis, RSA analysis,
and PQC survey, then feeds all results into the publication generators.

Usage:
    pipeline = PaperPipeline(bits=32, trials=10, seed=42)
    results = pipeline.run_all()
    latex = pipeline.generate_latex()
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from cuneiform.experiments.smooth_density import SmoothDensityExperiment
from cuneiform.crypto.scaling import ScalingAnalysis
from cuneiform.crypto.rsa_analysis import RSAAnalysis
from cuneiform.crypto.post_quantum import PostQuantumRegularityAnalysis
from cuneiform.publication.paper import PaperGenerator
from cuneiform.publication.figures import FigureGenerator
from cuneiform.publication.tables import TableGenerator


@dataclass
class PipelineResults:
    """All results from a paper pipeline run."""
    smooth_density: dict = field(default_factory=dict)
    scaling: dict = field(default_factory=dict)
    scaling_fit: dict = field(default_factory=dict)
    rsa: dict = field(default_factory=dict)
    pqc: dict = field(default_factory=dict)
    elapsed_seconds: float = 0.0


class PaperPipeline:
    """Run all experiments and generate a complete paper.

    Parameters:
        bit_sizes: bit sizes for scaling analysis (default: small for speed)
        trials_per_size: semiprimes per bit size in scaling
        sieve_range: sieve window width per semiprime
        smooth_bits: bit size for the main smooth density experiment
        smooth_trials: number of trials for smooth density
        seed: random seed for reproducibility
    """

    def __init__(self, bit_sizes: list[int] | None = None,
                 trials_per_size: int = 3,
                 sieve_range: int = 1000,
                 smooth_bits: int = 32,
                 smooth_trials: int = 50,
                 seed: int = 42):
        self.bit_sizes = bit_sizes or [32, 48]
        self.trials_per_size = trials_per_size
        self.sieve_range = sieve_range
        self.smooth_bits = smooth_bits
        self.smooth_trials = smooth_trials
        self.seed = seed

    def run_all(self) -> PipelineResults:
        """Run every experiment and collect results."""
        start = time.monotonic()
        results = PipelineResults()

        # 1. Smooth density experiment (the core result)
        exp = SmoothDensityExperiment(
            bits=self.smooth_bits,
            trials=self.smooth_trials,
            seed=self.seed,
        )
        exp_result = exp.run()
        results.smooth_density = exp_result.to_dict()

        # 2. Scaling analysis across bit sizes
        sa = ScalingAnalysis(bit_sizes=self.bit_sizes)
        results.scaling = sa.smooth_density_scaling(
            trials_per_size=self.trials_per_size,
            sieve_range=self.sieve_range,
        )
        results.scaling_fit = sa.compute_scaling_exponent()

        # 3. RSA challenge analysis
        rsa = RSAAnalysis()
        results.rsa = rsa.analyze_factored_rsa()

        # 4. PQC parameter survey
        pqc = PostQuantumRegularityAnalysis()
        results.pqc = pqc.parameter_regularity_survey()

        results.elapsed_seconds = time.monotonic() - start
        return results

    def generate_latex(self, results: PipelineResults | None = None) -> str:
        """Generate complete LaTeX paper from results."""
        if results is None:
            results = self.run_all()

        # Build the phase3/phase4 dicts that PaperGenerator expects
        phase3_results = {
            "smooth_density": results.smooth_density,
        }
        phase4_results = {
            "scaling": results.scaling,
            "scaling_fit": results.scaling_fit,
            "rsa": results.rsa,
            "pqc": results.pqc,
        }

        gen = PaperGenerator(phase3_results, phase4_results)
        base_latex = gen.generate_latex()

        # Generate figures and tables from the real data
        fig_gen = FigureGenerator()
        tab_gen = TableGenerator()

        # Build tier_rates dict for figure/table generators
        tier_rates = _build_tier_rates(results)
        inserts = []

        # Results section replacements
        results_content = _build_results_section(
            results, fig_gen, tab_gen, tier_rates)
        base_latex = base_latex.replace(
            _RESULTS_PLACEHOLDER, results_content)

        # Abstract placeholder
        abstract_sentence = _build_abstract_sentence(results)
        base_latex = base_latex.replace(
            "[RESULTS PLACEHOLDER --- fill from experimental data]",
            abstract_sentence)

        # Discussion placeholder
        discussion_content = _build_discussion(results)
        base_latex = base_latex.replace(
            _DISCUSSION_PLACEHOLDER, discussion_content)

        # Conclusion placeholder
        conclusion_content = _build_conclusion(results)
        base_latex = base_latex.replace(
            "[CONCLUSION PLACEHOLDER --- state main finding and future work.]",
            conclusion_content)

        return base_latex

    def summary(self, results: PipelineResults | None = None) -> str:
        """Human-readable summary of pipeline run."""
        if results is None:
            results = self.run_all()

        lines = [
            "Paper Pipeline Results",
            f"  Time: {results.elapsed_seconds:.2f}s",
            f"  Smooth density: {results.smooth_density.get('total_tested', 0)} values tested",
            f"  Scaling: {len(results.scaling)} bit sizes",
            f"  RSA challenges: {len(results.rsa)} analyzed",
            f"  PQC schemes: {len(results.pqc)} surveyed",
        ]

        if results.scaling_fit and "alpha" in results.scaling_fit:
            alpha = results.scaling_fit["alpha"]
            interp = results.scaling_fit.get("interpretation", "unknown")
            lines.append(f"  Scaling exponent alpha={alpha:.4f} ({interp})")

        return "\n".join(lines)


# --- Internal helpers ---

_RESULTS_PLACEHOLDER = r"""[RESULTS PLACEHOLDER --- to be filled from experimental data.

Key tables and figures:
\begin{itemize}
\item Table 1: Smooth density by regularity tier (the money table)
\item Figure 1: Scaling curve --- advantage ratio vs.\ bit size
\item Table 2: QS comparison --- relations found, time, prefilter saves
\item Table 3: PQC parameter regularity survey
\item Figure 2: Lattice reduction swap count comparison
\end{itemize}]"""

_DISCUSSION_PLACEHOLDER = r"""[DISCUSSION PLACEHOLDER --- adapt based on paper type and results.

Key points to address:
\begin{itemize}
\item Does the advantage persist at cryptographic bit sizes?
\item Is the effect specific to QS or generalizable to NFS?
\item What does the PQC parameter survey reveal?
\item Connection to Murphy--Brent polynomial selection (which already
      implicitly uses smooth leading coefficients)
\item Limitations: pure Python implementation, small bit sizes tested
\end{itemize}]"""


def _build_tier_rates(results: PipelineResults) -> dict:
    """Extract tier_rates in the format FigureGenerator/TableGenerator expect."""
    tiers = results.smooth_density.get("tiers", {})
    tier_rates = {}
    for k, v in tiers.items():
        tier_rates[int(k)] = {
            "total": v["count"],
            "smooth": v["smooth_count"],
            "rate": v["smooth_rate"],
        }
    return tier_rates


def _build_results_section(results: PipelineResults,
                           fig_gen: FigureGenerator,
                           tab_gen: TableGenerator,
                           tier_rates: dict) -> str:
    """Build the complete results section with real data."""
    parts = []

    # Smooth density table and figure
    if tier_rates:
        parts.append(r"\subsection{Smooth Density by Regularity Tier}")
        parts.append("")
        sd = results.smooth_density
        parts.append(
            f"We tested {sd.get('total_tested', 0):,} QS polynomial values "
            f"at {sd.get('bits', '?')}-bit size with smoothness bound "
            f"$B = {sd.get('smoothness_bound', '?')}$. "
            f"The overall smooth rate was {sd.get('overall_smooth_rate', 0):.4f}."
        )
        parts.append("")
        parts.append(tab_gen.smooth_density_table(tier_rates))
        parts.append("")
        parts.append(fig_gen.smooth_density_by_tier(tier_rates))

    # Scaling results
    if results.scaling:
        parts.append("")
        parts.append(r"\subsection{Scaling Analysis}")
        parts.append("")
        parts.append(tab_gen.scaling_table(results.scaling))
        parts.append("")
        parts.append(fig_gen.scaling_curve(results.scaling))

        if results.scaling_fit and "alpha" in results.scaling_fit:
            alpha = results.scaling_fit["alpha"]
            r_sq = results.scaling_fit.get("r_squared", 0)
            interp = results.scaling_fit.get("interpretation", "unknown")
            parts.append("")
            parts.append(
                f"Log-log regression yields scaling exponent "
                f"$\\alpha = {alpha:.4f}$ ($R^2 = {r_sq:.4f}$), "
                f"indicating {interp}."
            )

    # RSA challenge table
    if results.rsa:
        parts.append("")
        parts.append(r"\subsection{RSA Challenge Analysis}")
        parts.append("")
        parts.append(tab_gen.rsa_challenge_table(results.rsa))

    # PQC survey
    if results.pqc:
        parts.append("")
        parts.append(r"\subsection{Post-Quantum Parameter Survey}")
        parts.append("")
        parts.append(fig_gen.pqc_parameter_chart(results.pqc))

    return "\n".join(parts)


def _build_abstract_sentence(results: PipelineResults) -> str:
    """Generate the abstract's results sentence from real data."""
    sd = results.smooth_density
    rate = sd.get("overall_smooth_rate", 0)

    tiers = sd.get("tiers", {})
    tier_0_rate = tiers.get("0", {}).get("smooth_rate", 0)

    if results.scaling_fit and "alpha" in results.scaling_fit:
        alpha = results.scaling_fit["alpha"]
        if alpha > 0.1:
            return (
                f"a scaling advantage (exponent $\\alpha = {alpha:.3f}$) "
                f"for low-regularity-tier values in smooth number detection, "
                f"with tier-0 smooth rate {tier_0_rate:.4f} vs.\\ "
                f"overall rate {rate:.4f}"
            )
        elif alpha > -0.1:
            return (
                f"a constant-factor advantage for low-regularity-tier values "
                f"(scaling exponent $\\alpha = {alpha:.3f}$), "
                f"with tier-0 smooth rate {tier_0_rate:.4f} vs.\\ "
                f"overall rate {rate:.4f}"
            )
        else:
            return (
                f"that the regularity tier effect diminishes at larger bit "
                f"sizes (scaling exponent $\\alpha = {alpha:.3f}$), "
                f"providing a rigorous null result"
            )
    return (
        f"preliminary smooth density measurements with overall rate "
        f"{rate:.4f} across regularity tiers"
    )


def _build_discussion(results: PipelineResults) -> str:
    """Build a real discussion section from results."""
    parts = []

    # Scaling interpretation
    if results.scaling_fit and "alpha" in results.scaling_fit:
        alpha = results.scaling_fit["alpha"]
        interp = results.scaling_fit.get("interpretation", "unknown")
        parts.append(
            f"The scaling exponent $\\alpha = {alpha:.4f}$ indicates "
            f"\\emph{{{interp}}}. "
        )
        if alpha > 0.1:
            parts.append(
                "This is a striking result that warrants verification at "
                "larger bit sizes with optimized implementations. "
            )
        elif alpha > -0.1:
            parts.append(
                "A constant advantage, while not changing asymptotic "
                "complexity, represents a genuine optimization applicable "
                "to practical implementations. "
            )
        else:
            parts.append(
                "The diminishing advantage suggests the tier effect is a "
                "finite-size artifact that vanishes at cryptographic scales. "
                "This is itself an informative result. "
            )

    # PQC observations
    pqc = results.pqc
    if pqc:
        falcon_q = pqc.get("Falcon-512", {})
        if falcon_q:
            smooth_frac = falcon_q.get("q_minus_1_smooth_fraction", 0)
            parts.append(
                f"\n\nThe PQC parameter survey reveals that Falcon's modulus "
                f"$q = 12289$ has $q - 1$ with smooth fraction "
                f"{smooth_frac:.4f}, meaning its NTT arithmetic operates "
                f"largely within the sexagesimal ``regular'' domain. "
            )

    # Limitations
    parts.append(
        "\n\n\\paragraph{Limitations.} "
        "Our experiments use a pure Python implementation with small bit "
        "sizes. The scaling analysis covers only the range tested; "
        "extrapolation to RSA-2048 or beyond requires verification. "
        "The smooth density experiment uses a fixed smoothness bound "
        "rather than the optimal bound for each number size."
    )

    return "".join(parts)


def _build_conclusion(results: PipelineResults) -> str:
    """Build a real conclusion from results."""
    parts = []

    if results.scaling_fit and "alpha" in results.scaling_fit:
        alpha = results.scaling_fit["alpha"]
        if alpha > 0.1:
            parts.append(
                "Our experiments show a positive scaling exponent, suggesting "
                "the sexagesimal regularity framework provides a growing "
                "advantage in smooth number detection. If confirmed at "
                "larger scales, this has implications for factoring algorithm "
                "optimization."
            )
        elif alpha > -0.1:
            parts.append(
                "Our experiments show a roughly constant advantage for "
                "low-regularity-tier values. While this does not change "
                "asymptotic complexity, it provides a principled basis "
                "for polynomial selection and sieve optimization."
            )
        else:
            parts.append(
                "Our experiments show that the tier effect diminishes at "
                "larger bit sizes. This negative result is itself valuable: "
                "it establishes that the sexagesimal structure, while "
                "mathematically elegant, does not provide a scaling "
                "advantage for smooth number detection."
            )
    else:
        parts.append(
            "Our preliminary results demonstrate the viability of the "
            "regularity framework for analyzing smooth number density."
        )

    parts.append(
        "\n\n\\paragraph{Future work.} "
        "Optimized C/Rust implementation for large-scale experiments; "
        "integration with production NFS implementations; "
        "deeper analysis of the Falcon $q-1$ regularity; "
        "and extension of the regularity framework to "
        "number field sieve polynomial selection."
    )

    return "\n".join(parts)
