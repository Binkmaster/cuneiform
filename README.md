# CUNEIFORM

A Python library for exact sexagesimal (base-60) rational arithmetic, with applications to computational number theory and cryptographic analysis.

## What it does

The sexagesimal number system has a useful property: fractions with 5-smooth denominators (prime factors limited to 2, 3, 5) have terminating representations. CUNEIFORM formalizes this through a **regularity classification** that decomposes integers by their "distance" from being 5-smooth, then investigates whether this decomposition interacts usefully with smooth number detection — the computational bottleneck in integer factorization algorithms like the Quadratic Sieve and Number Field Sieve.

The library also implements Wildberger's rational trigonometry (quadrance/spread instead of distance/angle), reproduces and extends Plimpton 322 (a ~1800 BCE tablet containing 15 Pythagorean triples with 5-smooth generators), and provides a computer algebra system over the rationals.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Quick start

```python
from cuneiform.core.sexagesimal import Sexa
from cuneiform.core.rational import SexaRational

# Sexagesimal notation: 1;30 = 1 + 30/60 = 3/2
x = Sexa("1;30")
print(x.as_fraction)  # 3/2

# Exact rational arithmetic — no floats anywhere
a = SexaRational(1, 3)
b = SexaRational(1, 5)
print(a + b)  # 8/15

# Regularity classification
from cuneiform.number_theory.regularity import RegularityClass
rc = RegularityClass(360)
print(rc.regularity_tier)  # 0 (fully 5-smooth)
print(rc.is_regular)       # True

rc2 = RegularityClass(77)  # 7 * 11
print(rc2.regularity_tier)  # 2 (two non-smooth prime factors)
```

## CLI

```bash
python -m cuneiform info                    # library overview
python -m cuneiform validate                # 8 mathematical identity checks
python -m cuneiform tabulate --format csv   # extend Plimpton 322 to thousands of rows
python -m cuneiform experiment smooth-density --bits 64 --trials 100 --seed 42
python -m cuneiform paper -o paper.tex      # generate LaTeX paper with real data
```

## Modules

| Module | What it provides |
|--------|-----------------|
| `core` | `Sexa` (base-60 notation), `SexaRational` (exact rationals), `SmoothNumber` |
| `tablet` | Plimpton 322 reproduction — all 15 original rows verified against published scholarship |
| `geometry` | Rational trigonometry: `Quadrance`, `Spread`, all 5 laws, constructions |
| `number_theory` | Regularity classification, Quadratic Sieve (standard + sexagesimal variant), ECM, smoothness analysis |
| `crypto` | Scaling analysis, RSA regularity profiling, pure-Python LLL, elliptic curve arithmetic, post-quantum parameter survey |
| `cas` | `RatPoly` (polynomial algebra), `RatMatrix` (exact linear algebra), algebraic calculus, `SmoothRing` (Z[1/60]) |
| `quantum` | Classical simulation of Shor period-finding (binary vs sexagesimal QFT), Grover oracle gate analysis |
| `archaeology` | Tablet analyzer (relationship detection, scribal error detection, gap filling), corpus of known tablets |
| `hardware` | `SexaALU` behavioral simulation — 19 opcodes, 16 registers, cycle-accurate |
| `finance` | Rational price levels, support/resistance via regularity, pattern geometry |
| `math_expansion` | Chromogeometry, finite field rational trig, p-adic valuations |
| `education` | Interactive exercises (multiplication, reciprocals, square roots, triple generation) |
| `experiments` | Smooth density experiment, Plimpton tabulator, benchmark framework, paper pipeline |
| `publication` | LaTeX paper/figure/table generators with pgfplots output |

## Key concepts

**Regularity tier**: For integer n, extract the largest 5-smooth divisor (the "regular part") and count the prime factors of the remaining cofactor. Tier 0 = fully 5-smooth. Tier 1 = one non-smooth prime factor. Higher tiers = further from regular.

**The hypothesis**: QS polynomial values at low regularity tiers may have higher B-smooth rates than those at high tiers, because the 5-smooth factor is "already done." The `experiments` module measures this and the `crypto.scaling` module tests whether any effect persists at larger bit sizes.

**Rational trigonometry**: Replace distance with quadrance (d²) and angle with spread (sin²θ). All five laws are algebraic identities over Q — no transcendental functions, no floating point.

## Tests

```bash
pytest  # 672 tests, ~18s
```

## Project structure

```
cuneiform/          # library source
  core/             # Sexa, SexaRational, SmoothNumber
  tablet/           # Plimpton 322
  geometry/         # rational trigonometry
  number_theory/    # regularity, sieves, ECM, analysis
  crypto/           # RSA, lattice, EC, post-quantum, scaling
  cas/              # polynomials, matrices, calculus, Z[1/60]
  quantum/          # Shor/Grover simulations
  archaeology/      # tablet analysis and corpus
  hardware/         # SexaALU simulation
  finance/          # rational price analysis
  math_expansion/   # chromogeometry, finite fields, p-adic
  education/        # interactive exercises
  experiments/      # experiment runners and paper pipeline
  publication/      # LaTeX generation
tests/              # 672 tests
examples/           # standalone usage examples
primes/             # experimental RSA factoring scripts (just for fun)
```

## License

MIT
