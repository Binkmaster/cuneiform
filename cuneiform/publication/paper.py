"""Paper generation — complete LaTeX output from experimental results.

Adapts structure based on what was found: positive, negative, or mixed.
"""

from __future__ import annotations


class PaperGenerator:
    """Generate the complete academic paper from experimental results."""

    def __init__(self, phase3_results: dict | None = None,
                 phase4_results: dict | None = None):
        self.p3 = phase3_results or {}
        self.p4 = phase4_results or {}

    def determine_paper_type(self) -> str:
        """Based on results, choose paper framing."""
        scaling = self.p4.get("scaling", {})
        if not scaling:
            return "theoretical"

        alpha = scaling.get("scaling_fit", {}).get("alpha", 0)
        if alpha > 0.1:
            return "breakthrough"
        elif alpha > -0.1:
            return "technique"
        else:
            return "negative"

    def generate_latex(self) -> str:
        """Generate complete LaTeX source."""
        paper_type = self.determine_paper_type()
        sections = {
            "preamble": self._preamble(),
            "title": self._title(paper_type),
            "abstract": self._abstract(paper_type),
            "introduction": self._introduction(),
            "background": self._background(),
            "framework": self._framework(),
            "algorithms": self._algorithms(),
            "experiments": self._experiments(),
            "results": self._results(),
            "theoretical": self._theoretical(),
            "discussion": self._discussion(paper_type),
            "conclusion": self._conclusion(paper_type),
            "references": self._references(),
        }

        return "\n\n".join(sections.values()) + "\n\\end{document}\n"

    def _preamble(self) -> str:
        return r"""\documentclass[11pt]{article}
\usepackage{amsmath,amssymb,amsthm}
\usepackage{booktabs}
\usepackage{pgfplots}
\usepackage{hyperref}
\usepackage{algorithm}
\usepackage{algorithmic}

\pgfplotsset{compat=1.18}

\newtheorem{theorem}{Theorem}
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem{corollary}[theorem]{Corollary}
\newtheorem{conjecture}[theorem]{Conjecture}
\theoremstyle{definition}
\newtheorem{definition}[theorem]{Definition}

\begin{document}"""

    def _title(self, paper_type: str) -> str:
        titles = {
            "breakthrough": (
                "Sexagesimal Rational Arithmetic and Smooth Number Structure: "
                "A Babylonian Framework for Cryptographic Analysis"
            ),
            "technique": (
                "On the Relationship Between Number Representation and "
                "Smooth Number Detection in Integer Factorization"
            ),
            "theoretical": (
                "CUNEIFORM: Exact Sexagesimal Computation with Applications "
                "to Computational Number Theory"
            ),
            "negative": (
                "Representation Effects in Smooth Number Detection: "
                "A Rigorous Null Result"
            ),
        }
        title = titles.get(paper_type, titles["theoretical"])
        return f"\\title{{{title}}}\n\\author{{CUNEIFORM Project}}\n\\maketitle"

    def _abstract(self, paper_type: str) -> str:
        return r"""\begin{abstract}
We present CUNEIFORM, a computational framework for exact sexagesimal
(base-60) rational arithmetic inspired by Old Babylonian mathematics.
Building on the Mansfield--Wildberger interpretation of Plimpton 322
as an exact trigonometric table, we investigate whether the sexagesimal
number system's privileged treatment of 5-smooth numbers reveals
structure relevant to modern computational number theory and
cryptographic analysis.

We introduce a regularity classification that decomposes integers
by their ``distance'' from being 5-smooth, develop a tiered factor
base for the Quadratic Sieve, and measure smooth number density
differentials across regularity tiers. We analyze scaling behavior,
lattice reduction with sexagesimal preprocessing, elliptic curve
group order correlations, and post-quantum parameter regularity.

Our results show [RESULTS PLACEHOLDER --- fill from experimental data].
\end{abstract}"""

    def _introduction(self) -> str:
        return r"""\section{Introduction}

In 1945, Neugebauer and Sachs published a translation of Plimpton 322,
a Babylonian clay tablet dating to approximately 1800 BCE. For decades,
the tablet's purpose was debated. In 2017, Mansfield and Wildberger
proposed that it constitutes an exact trigonometric table --- one that
uses sexagesimal (base-60) arithmetic to represent Pythagorean triples
with exact rational precision, avoiding the irrational quantities
inherent in angular trigonometry~\cite{mansfield2017}.

This paper asks a computational question: does the Babylonian approach
to arithmetic --- specifically, its privileged treatment of 5-smooth
numbers (integers whose prime factors are limited to 2, 3, and 5) ---
reveal structure in modern number-theoretic problems?

The sexagesimal system is not merely base-60. It is a system where
\emph{regular numbers} (5-smooth numbers) have terminating reciprocals,
making them algebraically privileged. We formalize this privilege through
a \emph{regularity classification} (Definition~\ref{def:regularity})
and investigate its interaction with smooth number detection, the
computational bottleneck in factoring algorithms.

Our main contributions are:
\begin{enumerate}
\item A Python library (CUNEIFORM) implementing exact sexagesimal
      arithmetic with rational trigonometry;
\item A regularity-tiered Quadratic Sieve variant;
\item Smooth density measurements across regularity tiers, with
      scaling analysis to cryptographic bit sizes;
\item Analysis of post-quantum cryptographic parameters through
      the regularity lens.
\end{enumerate}"""

    def _background(self) -> str:
        return r"""\section{Background}

\subsection{Old Babylonian Mathematics}

The sexagesimal system, inherited from Sumerian mathematics, represents
numbers in base 60. A key property: the only primes dividing 60 are
2, 3, and 5. Consequently, a fraction $a/b$ has a terminating
sexagesimal expansion if and only if $b$ is \emph{5-smooth}.

\subsection{Rational Trigonometry}

Wildberger's rational trigonometry~\cite{wildberger2005} replaces
distance with \emph{quadrance} ($Q = d^2$) and angle with
\emph{spread} ($s = \sin^2\theta$). Five algebraic laws govern
rational trigonometric relationships, all expressible over~$\mathbb{Q}$.

\subsection{Smooth Numbers and Factoring}

The Number Field Sieve (NFS) and Quadratic Sieve (QS) factor integers
by finding $B$-smooth values among polynomial evaluations. The Dickman
function $\rho(u)$ governs the probability that a random integer near $N$
is $N^{1/u}$-smooth."""

    def _framework(self) -> str:
        return r"""\section{The Regularity Framework}

\begin{definition}[Regularity Classification]
\label{def:regularity}
For a positive integer $n$, write $n = r \cdot c$ where $r$ is the
largest 5-smooth divisor (the \emph{regular part}) and $c$ is the
\emph{cofactor}. The \emph{regularity tier} of $n$ is $\Omega(c)$,
the number of prime factors of $c$ counted with multiplicity.
\end{definition}

Tier~0 numbers are exactly the 5-smooth numbers. Tier~1 numbers have
a single non-regular prime factor. The tier measures the ``distance''
from being regular in the Babylonian sense.

\begin{theorem}[Tier Distribution]
For $n$ uniformly distributed in $[1, N]$, the density of tier-$k$
numbers is governed by the Dickman function applied to the cofactor:
\[
\Pr[\text{tier} = 0] \approx \rho\!\left(\frac{\log N}{\log 5}\right)
\]
where $\rho$ is the Dickman rho function.
\end{theorem}"""

    def _algorithms(self) -> str:
        return r"""\section{Algorithms}

\subsection{Sexagesimal Quadratic Sieve}

Our modified QS operates in two phases:
\begin{enumerate}
\item \textbf{Regularity prefilter:} For each polynomial value
      $Q(x) = (\lceil\sqrt{n}\rceil + x)^2 - n$, compute its
      regularity tier. Tier-0 values are guaranteed $B$-smooth
      for $B \geq 5$, providing ``free'' relations.
\item \textbf{Tiered sieve:} Remaining candidates are sieved with
      factor base primes ordered by sexagesimal tier (regular primes
      first, then tier-1, then tier-2).
\end{enumerate}

\subsection{Plimpton ECM}

Curve selection for ECM guided by extended Plimpton 322 triples.
Starting points $(w, \ell)$ from Pythagorean triples with 5-smooth
generators produce curves whose group orders may have enhanced
smooth structure."""

    def _experiments(self) -> str:
        return r"""\section{Experimental Methodology}

All experiments are reproducible via the CUNEIFORM Python library.
Random number generation uses fixed seeds throughout.

\subsection{Smooth Density Experiment}
For each target bit size, we generate random semiprimes, compute
QS polynomial values, classify by regularity tier, and measure
$B$-smooth rates per tier.

\subsection{Scaling Analysis}
Smooth density ratios measured at bit sizes 32, 48, 64, 80, 96,
128, and extrapolated to cryptographic sizes.

\subsection{Lattice Reduction}
LLL reduction applied to random lattices with and without
regularity-based basis reordering, measuring swap count and
shortest vector norm."""

    def _results(self) -> str:
        return r"""\section{Results}

[RESULTS PLACEHOLDER --- to be filled from experimental data.

Key tables and figures:
\begin{itemize}
\item Table 1: Smooth density by regularity tier (the money table)
\item Figure 1: Scaling curve --- advantage ratio vs.\ bit size
\item Table 2: QS comparison --- relations found, time, prefilter saves
\item Table 3: PQC parameter regularity survey
\item Figure 2: Lattice reduction swap count comparison
\end{itemize}]"""

    def _theoretical(self) -> str:
        return r"""\section{Theoretical Analysis}

\begin{theorem}[Conditional Smooth Probability]
Let $Q(x)$ be a QS polynomial value with regularity tier $k$.
Then:
\begin{align}
\Pr[B\text{-smooth} \mid \text{tier} = 0] &= 1 \\
\Pr[B\text{-smooth} \mid \text{tier} = 1] &\approx \frac{\pi(B)}{\pi(|Q|^{1/1})} \\
\Pr[B\text{-smooth} \mid \text{tier} = k] &\leq \rho\!\left(\frac{\log c_k}{\log B}\right)
\end{align}
where $c_k$ is the cofactor (with $k$ prime factors).
\end{theorem}

The sexagesimal advantage is exactly the count of tier-0 values
(guaranteed smooth) plus the enhanced probability for tier-1 values.

\begin{theorem}[Asymptotic Non-Improvement]
Sexagesimal preprocessing does not change the asymptotic complexity
class of QS or NFS. The preprocessing is polynomial-time and affects
only the constant factor in the sieving step.
\end{theorem}"""

    def _discussion(self, paper_type: str) -> str:
        return r"""\section{Discussion}

[DISCUSSION PLACEHOLDER --- adapt based on paper type and results.

Key points to address:
\begin{itemize}
\item Does the advantage persist at cryptographic bit sizes?
\item Is the effect specific to QS or generalizable to NFS?
\item What does the PQC parameter survey reveal?
\item Connection to Murphy--Brent polynomial selection (which already
      implicitly uses smooth leading coefficients)
\item Limitations: pure Python implementation, small bit sizes tested
\end{itemize}]"""

    def _conclusion(self, paper_type: str) -> str:
        return r"""\section{Conclusion}

We have presented CUNEIFORM, a framework for exact sexagesimal
computation applied to computational number theory. Our regularity
classification provides a structured decomposition of integers that
interacts non-trivially with smooth number detection.

[CONCLUSION PLACEHOLDER --- state main finding and future work.]

The CUNEIFORM library is available as open-source software,
enabling reproducibility and extension of all experiments reported here."""

    def _references(self) -> str:
        return r"""\begin{thebibliography}{99}

\bibitem{mansfield2017}
D.~F. Mansfield and N.~J. Wildberger,
``Plimpton 322 is Babylonian exact sexagesimal trigonometry,''
\emph{Historia Mathematica}, vol.~44, pp.~395--419, 2017.

\bibitem{wildberger2005}
N.~J. Wildberger,
\emph{Divine Proportions: Rational Trigonometry to Universal Geometry},
Wild Egg Books, 2005.

\bibitem{robson2002}
E.~Robson,
``Words and pictures: new light on Plimpton 322,''
\emph{American Mathematical Monthly}, vol.~109, pp.~105--120, 2002.

\bibitem{lenstra1987}
H.~W. Lenstra Jr.,
``Factoring integers with elliptic curves,''
\emph{Annals of Mathematics}, vol.~126, pp.~649--673, 1987.

\bibitem{lenstra1993}
A.~K. Lenstra and H.~W. Lenstra Jr., eds.,
\emph{The Development of the Number Field Sieve},
Lecture Notes in Mathematics, vol.~1554, Springer, 1993.

\bibitem{dickman1930}
K.~Dickman,
``On the frequency of numbers containing prime factors of a certain
relative magnitude,''
\emph{Arkiv f\"or Matematik, Astronomi och Fysik}, vol.~22, pp.~1--14, 1930.

\bibitem{pomerance1996}
C.~Pomerance,
``A tale of two sieves,''
\emph{Notices of the AMS}, vol.~43, pp.~1473--1485, 1996.

\end{thebibliography}"""
