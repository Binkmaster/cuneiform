# 𒌋𒐕 CUNEIFORM

**Exact sexagesimal rational mathematics for Python.**

CUNEIFORM is a Python library for working with **base-60 rational arithmetic**, **exact geometry**, and **Plimpton 322 style computation** without relying on floating-point approximations.

The project combines three ideas:

- **Sexagesimal arithmetic** for exact rational representation when denominators divide powers of 60
- **Rational trigonometry** in the style of quadrance and spread rather than distance and angle
- **Regularity / smoothness experiments** to test whether a base-60 view exposes useful structure in number-theoretic computations

The strongest claim of the project is not that ancient mathematics “beats” modern mathematics. It is that a Babylonian-style exact rational framework is worth implementing, testing, and using as a serious computational lens. The cryptographic angle is treated as an **experimental research question**, not as a settled result.

---

## Why base 60?

Base 60 has many divisors: 2, 3, 4, 5, 6, 10, 12, 15, 20, and 30. That means many fractions that repeat forever in base 10 terminate cleanly in base 60.

Example:

- `1/3` in base 10 = `0.3333...`
- `1/3` in base 60 = `0;20`

For a math library, this makes base 60 a natural setting for exact rational work, especially when combined with a no-floats policy.

---

## What the library is for

CUNEIFORM is best understood as a library with four connected parts.

### 1. Exact sexagesimal arithmetic

Represent and manipulate numbers exactly in a base-60-friendly form.

Core goals include:
- exact rational values
- conversion to and from sexagesimal notation
- regularity / smoothness classification
- no silent float drift

### 2. Rational geometry

The geometry layer is built around **quadrance** and **spread** rather than square roots and transcendental trig functions.

This gives you:
- exact rational points and lines
- exact triangle solving
- the five laws of rational trigonometry
- geometric constructions without approximation

### 3. Plimpton 322 extension and analysis

CUNEIFORM treats the Old Babylonian table tradition as something you can generate, extend, and analyze computationally.

That includes:
- reproducing the classical Plimpton material
- generating larger exact tables of Pythagorean-style data
- measuring how coverage improves as the regular-number bound increases

### 4. Number theory experiments

The experimental side of the project studies whether organizing numbers by **base-60 regularity** or **smoothness tier** reveals anything useful in computational number theory.

The most important early experiment is simple:
- generate semiprimes
- compute sieve-style polynomial values
- classify values by regularity tier
- measure smoothness rates by tier

## What CUNEIFORM does **not** claim

CUNEIFORM does **not** assume that base 60 breaks RSA, outperforms standard algorithms, or overturns accepted number theory.

The research posture is:
- maybe there is no advantage
- maybe there is a small measurable effect
- maybe the interesting output is a negative result

A rigorous negative result would still matter, because it would answer a real representation question rather than leaving it at speculation.

## Public-facing project summary

CUNEIFORM is a Python library for:

- exact sexagesimal rational arithmetic
- rational trigonometry and exact geometry
- Plimpton 322 generation and coverage analysis
- regularity and smoothness experiments in number theory

At minimum, it is a useful exact-math and historical-math toolkit.
At maximum, it may also surface interesting structural results about smoothness and representation.

---

## Example directions

Typical examples for the library should look like this:

```python
from cuneiform import Sexa, Spread, PlimptonGenerator

x = Sexa.from_fraction(1, 3)
print(x)   # 0;20

table = PlimptonGenerator(max_regular=1000).generate()
print(len(table))

row = table[0]
print(row.triple)
print(row.spread_width)
```

The point of the examples is to show three things quickly:
- exact fractional representation
- exact geometric data
- concrete generated mathematical artifacts
