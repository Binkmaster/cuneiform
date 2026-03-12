# 𒌋𒐕 CUNEIFORM

**Exact sexagesimal rational mathematics for Python.**

CUNEIFORM is a Python library for working with **base-60 rational arithmetic**, **exact geometry**, and **Plimpton 322 style computation** without relying on floating-point approximations.

The project combines three ideas:

- **Sexagesimal arithmetic** for exact rational representation when denominators divide powers of 60
- **Rational trigonometry** in the style of quadrance and spread rather than distance and angle
- **Regularity / smoothness experiments** to test whether a base-60 view exposes useful structure in number-theoretic computations

The strongest claim of the project is not that ancient mathematics “beats” modern mathematics. It is that a Babylonian-style exact rational framework is worth implementing, testing, and using as a serious computational lens. The cryptographic angle is treated as an **experimental research question**, not as a settled result. fileciteturn3file5L1-L18 fileciteturn3file16L1-L16

---

## Why base 60?

Base 60 has many divisors: 2, 3, 4, 5, 6, 10, 12, 15, 20, and 30. That means many fractions that repeat forever in base 10 terminate cleanly in base 60.

Example:

- `1/3` in base 10 = `0.3333...`
- `1/3` in base 60 = `0;20`

That is not mysticism. It is a direct consequence of the factorization of 60. fileciteturn3file5L1-L12

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

This is the point where the project stops being a number-format curiosity and becomes a usable computational framework. fileciteturn3file7L1-L18 fileciteturn3file14L1-L18

### 3. Plimpton 322 extension and analysis

CUNEIFORM treats the Old Babylonian table tradition as something you can generate, extend, and analyze computationally.

That includes:
- reproducing the classical Plimpton material
- generating larger exact tables of Pythagorean-style data
- measuring how coverage improves as the regular-number bound increases

Even by itself, an extended exact Plimpton table is a worthwhile artifact. fileciteturn3file18L1-L16 fileciteturn3file16L17-L28

### 4. Number theory experiments

The experimental side of the project studies whether organizing numbers by **base-60 regularity** or **smoothness tier** reveals anything useful in computational number theory.

The most important early experiment is simple:
- generate semiprimes
- compute sieve-style polynomial values
- classify values by regularity tier
- measure smoothness rates by tier

That is the cheap, decisive experiment. It should be run before investing heavily in larger cryptographic machinery. fileciteturn3file9L1-L13 fileciteturn3file16L29-L40

---

## What CUNEIFORM does **not** claim

CUNEIFORM does **not** assume that base 60 breaks RSA, outperforms standard algorithms, or overturns accepted number theory.

The research posture is:
- maybe there is no advantage
- maybe there is a small measurable effect
- maybe the interesting output is a negative result

A rigorous negative result would still matter, because it would answer a real representation question rather than leaving it at speculation. fileciteturn3file11L1-L18 fileciteturn3file16L1-L16

---

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

---

## Suggested repository structure

A clean public repo should emphasize the parts that already make sense on their own:

- `core/` — sexagesimal and rational arithmetic
- `geometry/` — quadrance, spread, triangle laws, constructions
- `tablet/` or `plimpton/` — original and extended table generation
- `number_theory/` — regularity, smoothness, experiments
- `examples/` — minimal demos and worked examples
- `docs/` — history, math background, experimental notes

The README should lead with what exists and what can be tested now, not with the most ambitious future branch. fileciteturn3file4L1-L18 fileciteturn3file2L1-L18

---

## Best framing for GitHub

The most defensible framing is:

> CUNEIFORM is an exact mathematics library inspired by Babylonian sexagesimal computation and modern rational trigonometry.

That pitch is strong because it is true even if every cryptographic experiment comes back neutral.

The crypto line should remain secondary:

> The project also includes experiments testing whether base-60 regularity classes reveal useful structure in smooth-number problems.

That keeps the repo interesting without overselling it. fileciteturn3file11L19-L31

---

## Historical stance

The project does not need to win the historical argument over what Plimpton 322 “really” was.

The useful synthesis is simpler:
- the historical intent is debated
- the mathematical framework is still worth testing computationally
- exact ratio-based geometry is valid whether or not the Babylonians described it in modern terms

That keeps the project out of needless historical overclaim while preserving the interesting mathematical thread. fileciteturn3file11L1-L15

---

## Practical roadmap

The shortest credible roadmap is:

1. Ship the exact arithmetic core
2. Ship the rational geometry layer
3. Ship the extended Plimpton generator and coverage analysis
4. Ship the regularity classifier and smoothness tester
5. Run the smooth-density experiment
6. Expand only if the results justify expansion

This sequence keeps the project grounded in artifacts and evidence. fileciteturn3file7L1-L18 fileciteturn3file16L29-L40

---

## Why the project is worth publishing even without big results

Because it already contains three independently valuable things:

1. a distinctive exact-arithmetic framework
2. a practical implementation of rational trigonometry
3. a computational extension of one of the most famous mathematical tablets in history

If the experiments produce more than that, great.
If they do not, the library still stands on its own.

---

## One-sentence version

**CUNEIFORM is a Python library for exact sexagesimal rational arithmetic, rational geometry, and Plimpton-style number theory experiments.**

---

## Recommendation

Use this README tone on GitHub.

Keep the bolder speculation in separate files such as:
- `docs/research-notes.md`
- `docs/open-questions.md`
- `docs/vision.md`

Your front page should make a skeptical technical reader think: “This is unusual, but it is concrete.”
