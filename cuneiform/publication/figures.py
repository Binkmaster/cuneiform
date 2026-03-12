"""Figure generation — pgfplots/LaTeX code for publication-quality figures."""

from __future__ import annotations


class FigureGenerator:
    """Generate all publication-quality figures as pgfplots LaTeX code."""

    def smooth_density_by_tier(self, tier_rates: dict) -> str:
        """The primary figure: smooth rate by regularity tier.

        tier_rates: {tier: {"rate": float, "total": int, "smooth": int}}
        """
        coords = []
        for tier in sorted(tier_rates.keys()):
            rate = tier_rates[tier]["rate"]
            coords.append(f"({tier}, {rate:.6f})")

        return r"""\begin{figure}[ht]
\centering
\begin{tikzpicture}
\begin{axis}[
    xlabel={Regularity Tier},
    ylabel={$B$-Smooth Rate},
    ybar,
    bar width=15pt,
    xtick=data,
    nodes near coords,
    nodes near coords align={vertical},
    every node near coord/.append style={font=\tiny},
    ymin=0,
    title={Smooth Density by Regularity Tier}
]
\addplot coordinates {""" + " ".join(coords) + r"""};
\end{axis}
\end{tikzpicture}
\caption{$B$-smooth rate of QS polynomial values classified by
regularity tier. Tier~0 (5-smooth) values are trivially smooth.
Lower tiers show higher smooth rates, confirming the sexagesimal
hypothesis at this bit size.}
\label{fig:smooth-density}
\end{figure}"""

    def scaling_curve(self, scaling_data: dict) -> str:
        """Advantage ratio vs bit size."""
        coords = []
        for bits, data in sorted(scaling_data.items()):
            ratio = data.get("advantage_ratio", 0)
            if ratio != float("inf") and ratio > 0:
                coords.append(f"({bits}, {ratio:.4f})")

        return r"""\begin{figure}[ht]
\centering
\begin{tikzpicture}
\begin{axis}[
    xlabel={Bit Size},
    ylabel={Advantage Ratio (Tier 0--1 / Tier 2+)},
    mark=*,
    title={Scaling of Sexagesimal Advantage}
]
\addplot coordinates {""" + " ".join(coords) + r"""};
\end{axis}
\end{tikzpicture}
\caption{Smooth rate ratio (tier~0--1 vs.\ tier~2+) as a function
of number size. A flat line indicates constant advantage; a rising
line indicates scaling advantage.}
\label{fig:scaling}
\end{figure}"""

    def lattice_comparison(self, lattice_data: dict) -> str:
        """LLL swap count: standard vs reordered."""
        std_coords = []
        reord_coords = []
        for dim, data in sorted(lattice_data.items()):
            std_coords.append(
                f"({dim}, {data['standard']['avg_swaps']:.1f})")
            reord_coords.append(
                f"({dim}, {data['regularity_reordered']['avg_swaps']:.1f})")

        return r"""\begin{figure}[ht]
\centering
\begin{tikzpicture}
\begin{axis}[
    xlabel={Lattice Dimension},
    ylabel={Average LLL Swaps},
    legend pos=north west,
    mark=*,
    title={LLL Reduction: Standard vs.\ Regularity-Reordered}
]
\addplot coordinates {""" + " ".join(std_coords) + r"""};
\addlegendentry{Standard}
\addplot coordinates {""" + " ".join(reord_coords) + r"""};
\addlegendentry{Regularity-Reordered}
\end{axis}
\end{tikzpicture}
\caption{Average number of LLL swaps for standard vs.\
regularity-reordered basis. Fewer swaps indicates faster convergence.}
\label{fig:lattice}
\end{figure}"""

    def pqc_parameter_chart(self, pqc_data: dict) -> str:
        """PQC parameter regularity as a table figure."""
        rows = []
        for name, data in sorted(pqc_data.items()):
            rows.append(
                f"    {name} & {data['q']} & {data['q_mod_60']} & "
                f"{data['q_tier']} & {data.get('q_minus_1_smooth_fraction', 0):.4f} \\\\"
            )

        return r"""\begin{table}[ht]
\centering
\caption{Regularity properties of NIST PQC standard parameters.}
\label{tab:pqc}
\begin{tabular}{lrrrr}
\toprule
Scheme & $q$ & $q \bmod 60$ & Tier & $q{-}1$ smooth frac. \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}"""
