# Riemann Hypothesis Explorations with CUNEIFORM

## Honest disclaimer

**CUNEIFORM cannot prove the Riemann Hypothesis.** No computational tool can,
because RH is a statement about ALL nontrivial zeros of zeta, and checking
finitely many zeros (even trillions) is not a proof.

## What we CAN do

CUNEIFORM's exact rational arithmetic and prime/smooth-number machinery
connects to RH in several legitimate ways:

1. **Prime counting error analysis** (`prime_error.py`)
   - Compute pi(x), psi(x), and their deviations from predictions
   - Visualize what RH *means* for prime distribution
   - Show the sqrt(x) error bound that RH implies

2. **Explicit formula exploration** (`explicit_formula.py`)
   - Implement the von Mangoldt explicit formula for psi(x)
   - Use known zeros to reconstruct prime distribution
   - Show how zeros control oscillations in prime counting

3. **Smooth number connections** (`smooth_zeta.py`)
   - Analyze how 5-smooth numbers relate to partial Euler products
   - The {2,3,5}-truncated zeta function and its zeros
   - Regularity tiers and their zeta-function interpretation

4. **Zero verification** (`zero_verify.py`)
   - Numerical verification of known low-lying zeros
   - Argument principle for zero counting N(T)
   - Gram points and Z-function computation

5. **Sexagesimal zeta** (`sexa_zeta.py`)
   - Zeta function values at positive even integers (Bernoulli numbers)
   - These are EXACT RATIONALS -- CUNEIFORM's home turf
   - zeta(2) = pi^2/6, but the Bernoulli numbers themselves are rational

## The connection to primes

The Riemann zeta function is built from primes via the Euler product:

    zeta(s) = prod_p (1 - p^(-s))^(-1)

So every result about zeta zeros is really a result about prime distribution.
CUNEIFORM's regularity decomposition (n = smooth_part * cofactor) is essentially
asking: how does n relate to the first three Euler factors (p = 2, 3, 5)?

6. **Spectral exploration** (`spectral_exploration.py`)
   - Montgomery-Odlyzko zero spacing statistics (GUE connection)
   - Regularity-graded operator toy model (Hilbert-Polya direction)
   - Mertens function analysis (M(x) = O(x^(1/2+eps)) iff RH)

7. **Critical-line proportion bounds** (`critical_line.py`)
   - The 1914-2026 history of lower bounds on the proportion of zeros
     on the critical line, as exact rationals
   - Every quantified record (1/3, 2/5, 5/12, 269/400) is a *regular*
     sexagesimal — its base-60 expansion terminates
   - Exact computation of each jump and of the gap remaining to RH

## State of the art (August 2026)

On August 10, 2026, Anthropic announced that a research version of Claude
improved the unconditional lower bound on the proportion of nontrivial
zeta zeros lying on the critical line from 5/12 (~41.67%) to **at least
67.25%** — the largest single jump in the bound's history:

| Year | Record                              | Bound   | Base 60   |
|------|-------------------------------------|---------|-----------|
| 1914 | Hardy                               | infinitely many | — |
| 1942 | Selberg                             | positive proportion | — |
| 1974 | Levinson                            | 1/3     | `0;20`    |
| 1989 | Conrey                              | 2/5     | `0;24`    |
| 2020 | Pratt-Robles-Zaharescu-Zeindler     | 5/12    | `0;25`    |
| 2026 | Claude (Anthropic)                  | 269/400 | `0;40,21` |

The method combined Baluyot-Goldston-Suriajaya-Turnage-Butterbaugh's
unconditional adaptation of Montgomery's pair correlation with Bombieri's
2000 work on a suitable function space with a quadratic form. The proof
was reviewed by Brian Conrey and Dan Goldston and formalized in Lean 4;
independent community review is ongoing.

**This does not change the honest disclaimer above.** A lower bound on
the proportion of zeros on the line — even a dramatically better one —
is not RH, and Anthropic itself does not expect these techniques to
prove RH. It does show that progress on the bound is not frozen, and it
hands CUNEIFORM a gift: 269/400 has denominator 2^4 * 5^2, so the new
record — like every record before it — is exactly expressible on a
Babylonian tablet. See `critical_line.py`.

## Observations

### What CUNEIFORM genuinely contributes

- **Exact Bernoulli numbers**: zeta at even integers has rational parts — these
  are CUNEIFORM's home turf, computed with zero rounding error.
- **Euler product decomposition**: The regularity framework gives a natural
  factorization `zeta(s) = zeta_smooth(s) * zeta_irregular(s)`, where the smooth
  factor uses only primes {2, 3, 5} and is exactly computable as a rational.
- **91% of small prime gaps are fully 5-smooth**: Among the first 5,000 prime
  gaps, 91.1% have cofactor = 1 (i.e., the gap is a product of only 2s, 3s,
  and 5s). 40.4% are divisible by 6. This is partly explained by gaps being
  even, but the dominance of smooth gaps is striking.
- **Regularity-tier Dirichlet series**: Decomposing zeta's Dirichlet series by
  CUNEIFORM regularity tier shows that tier 0 (smooth numbers) accounts for
  ~95% of zeta(2), with higher tiers contributing rapidly diminishing amounts.

### Why it can't solve RH

- RH requires a proof about ALL infinitely many zeros — no computation suffices.
- CUNEIFORM has no complex number support (by design, it stays in exact rationals).
- The nontrivial zeros live entirely in `zeta_irregular`, which involves ALL
  primes > 5 and their collective interactions.
- A proof would require new mathematics (spectral interpretation, positivity
  theorem, trace formula breakthrough, etc.), not better computation.
- No existing mathematical framework has achieved this in 167 years — though
  the 2026 critical-line bound (see above) shows the partial results are
  still moving.

### The honest take

CUNEIFORM is a beautiful toolkit for exploring the *consequences* and
*manifestations* of RH in prime distribution. The regularity decomposition
offers a genuinely interesting lens on the Euler product. But proving RH
requires a fundamentally different kind of argument — not computation, but
a structural insight about why the zeros MUST align.

## Running

```bash
cd ~/coding/cuneiform
python -m primes.reimann.prime_error
python -m primes.reimann.explicit_formula
python -m primes.reimann.smooth_zeta
python -m primes.reimann.zero_verify
python -m primes.reimann.sexa_zeta
python -m primes.reimann.spectral_exploration
python -m primes.reimann.critical_line
```

## Sources for the 2026 result

- [Anthropic: Learning more about Claude's mathematical capabilities](https://www.anthropic.com/research/riemann-zeta)
