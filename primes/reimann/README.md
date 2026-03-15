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
- No existing mathematical framework has achieved this in 166 years.

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
```
