"""Table generation for the paper — LaTeX tabular output."""

from __future__ import annotations


class TableGenerator:
    """Generate publication-ready LaTeX tables from results."""

    def smooth_density_table(self, tier_rates: dict) -> str:
        """The money table: smooth rate by tier."""
        rows = []
        for tier in sorted(tier_rates.keys()):
            d = tier_rates[tier]
            rows.append(
                f"    {tier} & {d['total']:,} & {d['smooth']:,} & "
                f"{d['rate']:.6f} \\\\"
            )

        return r"""\begin{table}[ht]
\centering
\caption{$B$-smooth rate of QS polynomial values by regularity tier.}
\label{tab:smooth-density}
\begin{tabular}{rrrr}
\toprule
Tier & Total & Smooth & Rate \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}"""

    def scaling_table(self, scaling_data: dict) -> str:
        """Scaling results across bit sizes."""
        rows = []
        for bits in sorted(scaling_data.keys()):
            d = scaling_data[bits]
            rows.append(
                f"    {bits} & {d.get('low_tier_rate', 0):.6f} & "
                f"{d.get('high_tier_rate', 0):.6f} & "
                f"{d.get('advantage_ratio', 0):.4f} \\\\"
            )

        return r"""\begin{table}[ht]
\centering
\caption{Smooth rate scaling across bit sizes.}
\label{tab:scaling}
\begin{tabular}{rrrr}
\toprule
Bits & Low-Tier Rate & High-Tier Rate & Advantage Ratio \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}"""

    def qs_comparison_table(self, comparison: dict) -> str:
        """Standard vs sexagesimal QS comparison."""
        std = comparison.get("standard", {})
        sexa = comparison.get("sexagesimal", {})
        comp = comparison.get("comparison", {})

        return r"""\begin{table}[ht]
\centering
\caption{Quadratic Sieve comparison: standard vs.\ sexagesimal variant.}
\label{tab:qs-comparison}
\begin{tabular}{lrr}
\toprule
Metric & Standard QS & Sexagesimal QS \\
\midrule""" + f"""
    Success rate & {std.get('success_rate', 0):.2f} & {sexa.get('success_rate', 0):.2f} \\\\
    Avg.\ time (s) & {std.get('avg_time', 0):.4f} & {sexa.get('avg_time', 0):.4f} \\\\
    Avg.\ relations & {std.get('avg_relations', 0):.1f} & {sexa.get('avg_relations', 0):.1f} \\\\
    Prefilter saves & --- & {sexa.get('total_prefilter_saves', 0)} \\\\
    Time ratio & \\multicolumn{{2}}{{c}}{{{comp.get('time_ratio', 0):.4f}}} \\\\""" + r"""
\bottomrule
\end{tabular}
\end{table}"""

    def rsa_challenge_table(self, rsa_data: dict) -> str:
        """RSA challenge regularity analysis."""
        rows = []
        for name, d in sorted(rsa_data.items()):
            rows.append(
                f"    {name} & {d['n_bits']} & {d['n_tier']} & "
                f"{d['p_tier']} & {d['q_tier']} & "
                f"{d['phi_n_tier']} \\\\"
            )

        return r"""\begin{table}[ht]
\centering
\caption{Regularity analysis of factored RSA challenges.}
\label{tab:rsa}
\begin{tabular}{lrrrrr}
\toprule
Challenge & Bits & $n$ tier & $p$ tier & $q$ tier & $\varphi(n)$ tier \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}"""

    def standard_curves_table(self, curve_data: dict) -> str:
        """Standard ECC curve audit results."""
        rows = []
        for name, d in sorted(curve_data.items()):
            rows.append(
                f"    {name} & {d['p_bits']} & {d['p_mod_60']} & "
                f"{d['order_mod_60']} & "
                f"{'Yes' if d['order_is_prime'] else 'No'} \\\\"
            )

        return r"""\begin{table}[ht]
\centering
\caption{Regularity audit of standard elliptic curves.}
\label{tab:curves}
\begin{tabular}{lrrrr}
\toprule
Curve & Bits & $p \bmod 60$ & $\#E \bmod 60$ & Prime order? \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}"""
