# Taylor Series in Babylonian Sexagesimal Cuneiform

## What a Taylor Series Looks Like in Base 60

A Taylor series is an infinite polynomial whose coefficients are simple
rationals — reciprocals of factorials, or of the integers themselves:

```
e^x  =  1 + x + x²/2! + x³/3! + x⁴/4! + ...
```

In base 60 a rational number terminates exactly when its reduced denominator
is **regular** (5-smooth: only prime factors 2, 3, 5). So the natural question
for a Babylonian scribe is: *which Taylor coefficients can be written exactly
on a clay tablet?*

The answer has a sharp and beautiful boundary — and the same boundary shows
up again in the Basel problem, Σ 1/n² = π²/6, treated at the end.

## The Exponential Series: Exactly Seven Regular Terms

The coefficients of e^x are 1/k!, and k! is 5-smooth precisely for k ≤ 6 —
because 7! = 5040 is the first factorial to contain the prime 7. So exactly
the **first seven terms** of the exponential series are regular numbers:

| k | 1/k! | Sexagesimal | Status | Cuneiform |
|---|------|-------------|--------|-----------|
| 0 | 1 | 1 | regular | 𒐕 |
| 1 | 1 | 1 | regular | 𒐕 |
| 2 | 1/2 | 0;30 | regular | 𒐿 ; 𒐺 |
| 3 | 1/6 | 0;10 | regular | 𒐿 ; 𒌋 |
| 4 | 1/24 | 0;2,30 | regular | 𒐿 ; 𒐖 𒐺 |
| 5 | 1/120 | 0;0,30 | regular | 𒐿 ; 𒐿 𒐺 |
| 6 | 1/720 | 0;0,5 | regular | 𒐿 ; 𒐿 𒐙 |
| 7 | 1/5040 | 0;0,0,42,51,25,42,... | **irregular** | 𒐿 ; 𒐿 𒐿 𒐻𒐖 𒐼𒐕 𒐹𒐙 ... |
| 8 | 1/40320 | 0;0,0,5,21,25,42,... | **irregular** | 𒐿 ; 𒐿 𒐿 𒐙 𒐹𒐕 𒐹𒐙 ... |
| 9 | 1/362880 | 0;0,0,0,35,42,51,... | **irregular** | 𒐿 ; 𒐿 𒐿 𒐿 𒐺𒐙 𒐻𒐖 ... |

The regular coefficients are strikingly clean in base 60: 1/6 is a single
digit (0;10), 1/720 is a single digit two places down (0;0,5). These are
exactly the numbers that appear in the standard Old Babylonian reciprocal
tables. The moment the prime 7 enters, the expansion becomes periodic and
non-terminating — the digit block 42,51,25,42,51,25 (the base-60 period of
1/7) repeats forever.

## Sine and Cosine

The odd/even split of the exponential series inherits the same boundary:
sin picks up the irregular coefficients starting at x⁷, cos at x⁸.

**sin x = x − x³/3! + x⁵/5! − ...**

| Term | Coefficient | Sexagesimal | Status | Cuneiform |
|------|-------------|-------------|--------|-----------|
| x¹ | 1 | 1 | regular | 𒐕 |
| x³ | −1/6 | −0;10 | regular | −𒐿 ; 𒌋 |
| x⁵ | 1/120 | 0;0,30 | regular | 𒐿 ; 𒐿 𒐺 |
| x⁷ | −1/5040 | −0;0,0,42,51,25,... | **irregular** | −𒐿 ; 𒐿 𒐿 𒐻𒐖 𒐼𒐕 ... |
| x⁹ | 1/362880 | 0;0,0,0,35,42,51,... | **irregular** | 𒐿 ; 𒐿 𒐿 𒐿 𒐺𒐙 ... |

**cos x = 1 − x²/2! + x⁴/4! − ...**

| Term | Coefficient | Sexagesimal | Status | Cuneiform |
|------|-------------|-------------|--------|-----------|
| x⁰ | 1 | 1 | regular | 𒐕 |
| x² | −1/2 | −0;30 | regular | −𒐿 ; 𒐺 |
| x⁴ | 1/24 | 0;2,30 | regular | 𒐿 ; 𒐖 𒐺 |
| x⁶ | −1/720 | −0;0,5 | regular | −𒐿 ; 𒐿 𒐙 |
| x⁸ | 1/40320 | 0;0,0,5,21,25,... | **irregular** | 𒐿 ; 𒐿 𒐿 𒐙 𒐹𒐕 ... |

The three-term cosine approximation 1 − x²/2 + x⁴/24 — good to ~10⁻⁴ across
[−0;30, 0;30] — uses only single- and double-digit regular coefficients. A
scribe with a reciprocal table could evaluate it exactly.

## Logarithm and Arctangent: Regularity Comes and Goes

For ln(1+x) and arctan x the coefficients are ±1/k, so a term is regular
exactly when k is 5-smooth. Unlike the factorial series (regular then
irregular forever), regularity here **alternates** along the series:

**ln(1+x) = x − x²/2 + x³/3 − ...**

| Term | Coefficient | Sexagesimal | Status |
|------|-------------|-------------|--------|
| x¹ | 1 | 1 | regular |
| x² | −1/2 | −0;30 | regular |
| x³ | 1/3 | 0;20 | regular |
| x⁴ | −1/4 | −0;15 | regular |
| x⁵ | 1/5 | 0;12 | regular |
| x⁶ | −1/6 | −0;10 | regular |
| x⁷ | 1/7 | 0;8,34,17,8,... | **irregular** |
| x⁸ | −1/8 | −0;7,30 | regular |
| x⁹ | 1/9 | 0;6,40 | regular |
| x¹⁰ | −1/10 | −0;6 | regular |

The first six coefficients are the first six lines of the standard Babylonian
reciprocal table: 30, 20, 15, 12, 10. Only 1/7 breaks the pattern — the same
famously "impossible" reciprocal the scribes' tables skip (tables jump from
igi-6 to igi-8).

**arctan x = x − x³/3 + x⁵/5 − ...** hits irregular terms at 1/7, 1/11, 1/13,
but recovers regularity at 1/15 (= 0;4), 1/25, 1/27, ... — the terms whose
odd index is 5-smooth.

## Watching e Converge on a Clay Tablet

Summing the exponential series at x = 1 in exact arithmetic:

| Terms | Partial sum | Sexagesimal | Cuneiform |
|-------|-------------|-------------|-----------|
| 1 | 1 | 1 | 𒐕 |
| 2 | 2 | 2 | 𒐖 |
| 3 | 5/2 | 2;30 | 𒐖 ; 𒐺 |
| 4 | 8/3 | 2;40 | 𒐖 ; 𒐻 |
| 5 | 65/24 | 2;42,30 | 𒐖 ; 𒐻𒐖 𒐺 |
| 6 | 163/60 | 2;43 | 𒐖 ; 𒐻𒐗 |
| 7 | 1957/720 | 2;43,5 | 𒐖 ; 𒐻𒐗 𒐙 |
| 8 | 685/252 | 2;43,5,42,51,25,... | 𒐖 ; 𒐻𒐗 𒐙 𒐻𒐖 𒐼𒐕 ... |
| 9 | 109601/40320 | 2;43,5,48,12,51,... | 𒐖 ; 𒐻𒐗 𒐙 𒐻𒐜 𒌋𒐖 ... |
| 10 | 98641/36288 | 2;43,5,48,48,34,... | 𒐖 ; 𒐻𒐗 𒐙 𒐻𒐜 𒐻𒐜 ... |

The seven-term sum **2;43,5** (= 1957/720) is the last partial sum that
terminates in base 60 — the last one writable exactly on a tablet. It already
matches e = 2;43,5,48,52,29,48,... in its first two fractional digits; the
tail of the series is bounded by (1/7!)(8/7) = 1/4410 < 1/60².

After the seventh term, every partial sum is irregular, forever: once the
prime 7 enters the denominator it never cancels out.

## The Degree-6 Taylor Polynomial as a Tablet Computation

Truncating e^x to its seven regular terms gives

```
T₆(x) = 1 + x + x²/2 + x³/6 + x⁴/24 + x⁵/120 + x⁶/720
```

Every coefficient is regular, so evaluating T₆ at a regular argument is a
**closed computation in regular numbers** — products and reciprocals of
regular numbers are regular, so nothing ever leaves the world of terminating
sexagesimals:

| Input | T₆(x) exact | Cuneiform |
|-------|-------------|-----------|
| x = 1 | 2;43,5 | 𒐖 ; 𒐻𒐗 𒐙 |
| x = 1;30 | 4;28,39,8,26,15 | 𒐘 ; 𒐹𒐜 𒐺𒐝 𒐜 𒐹𒐚 𒌋𒐙 |
| x = 0;30 | 1;38,55,23,26,15 | 𒐕 ; 𒐺𒐜 𒐼𒐙 𒐹𒐗 𒐹𒐚 𒌋𒐙 |
| x = 0;1 | 1;1,0,30,10,2,30,30,5 | 𒐕 ; 𒐕 𒐿 𒐺 𒌋 𒐖 𒐺 𒐺 𒐙 |

This is exactly the kind of arithmetic Old Babylonian scribes actually did:
multiply, look up a reciprocal, add — every intermediate value exact and
terminating. The scribes had the tools (reciprocal tables, multiplication
tables, and table-based interpolation for functions like (61/60)ⁿ in
compound-interest problems); what they lacked was the *concept* of
approximating a function by a polynomial. Had someone handed them T₆, their
number system was uncannily well-suited to evaluating it: all seven
coefficients sit in their standard tables.

## The Basel Problem: Σ 1/n² = π²/6

Euler's famous 1734 result gets the same treatment. The terms 1/n² are
regular exactly when n is 5-smooth — but the *partial sums* are regular only
through n = 6, because adding 1/49 at n = 7 plants the prime 7 in the
denominator permanently:

| n | 1/n² | Partial sum | Sexagesimal | Status | Cuneiform |
|---|------|-------------|-------------|--------|-----------|
| 1 | 1 | 1 | 1 | regular | 𒐕 |
| 2 | 1/4 | 5/4 | 1;15 | regular | 𒐕 ; 𒌋𒐙 |
| 3 | 1/9 | 49/36 | 1;21,40 | regular | 𒐕 ; 𒐹𒐕 𒐻 |
| 4 | 1/16 | 205/144 | 1;25,25 | regular | 𒐕 ; 𒐹𒐙 𒐹𒐙 |
| 5 | 1/25 | 5269/3600 | 1;27,49 | regular | 𒐕 ; 𒐹𒐛 𒐻𒐝 |
| 6 | 1/36 | 5369/3600 | 1;29,29 | regular | 𒐕 ; 𒐹𒐝 𒐹𒐝 |
| 7 | 1/49 | 266681/176400 | 1;30,42,28,9,... | **irregular** | 𒐕 ; 𒐺 𒐻𒐖 𒐹𒐜 𒐝 ... |
| 8 | 1/64 | 1077749/705600 | 1;31,38,43,9,... | **irregular** | 𒐕 ; 𒐺𒐕 𒐺𒐜 𒐻𒐗 𒐝 ... |
| 9 | 1/81 | 9778141/6350400 | 1;32,23,9,49,... | **irregular** | 𒐕 ; 𒐺𒐖 𒐹𒐗 𒐝 𒐻𒐝 ... |
| 10 | 1/100 | 1968329/1270080 | 1;32,59,9,49,... | **irregular** | 𒐕 ; 𒐺𒐖 𒐼𒐝 𒐝 𒐻𒐝 ... |
| 11 | 1/121 | 239437889/153679680 | 1;33,28,54,57,... | **irregular** | 𒐕 ; 𒐺𒐗 𒐹𒐜 𒐼𒐘 𒐼𒐛 ... |
| 12 | 1/144 | 240505109/153679680 | 1;33,53,54,57,... | **irregular** | 𒐕 ; 𒐺𒐗 𒐼𒐗 𒐼𒐘 𒐼𒐛 ... |

The target:

```
π²/6 = 1;38,41,45,45,30,22,52,15,...
       𒐕 ; 𒐺𒐜 𒐻𒐕 𒐻𒐙 𒐻𒐙 𒐺 𒐹𒐖 𒐼𒐖 𒌋𒐙 ...
```

Two things to notice:

**The regular partial sums are strikingly clean.** S₄ = 1;25,25 and
S₆ = 1;29,29 are exact two-digit repeated pairs — because their denominators
(144 and 3600) divide 60². The last tablet-writable partial sum of the Basel
series is the doubled digit **1;29,29**.

**Direct summation is hopeless.** The tail of Σ1/n² shrinks like 1/n, so
even S₁₂ has only reached 1;33 — nowhere near 1;38,41. Where the exponential
series hands a scribe two correct digits in seven terms, the Basel series
would demand thousands of terms per digit. Euler's genius wasn't summing
harder; it was the closed form π²/6 — a connection between reciprocal squares
and the circle that no amount of tablet arithmetic could reveal.

## Why the Boundary Falls at Seven

This is the same phenomenon this library's regularity classification
measures everywhere else. The factorials climb the regularity tiers:

- 1! … 6! — tier 0 (fully 5-smooth)
- 7! … 10! — tier 1 (one non-smooth prime: 7)
- 11! … 12! — tier 2 (7, 11)
- 13! — tier 3 (7, 11, 13) …

Each new prime p ≥ 7 permanently poisons every later factorial. The Taylor
series of e^x, sin, and cos thus have a finite regular "head" and an infinite
irregular "tail" — while series with 1/k coefficients (ln, arctan) keep
producing regular terms forever at the 5-smooth indices, a set with density
zero but infinite membership. The Basel series sits in between: its *terms*
recover regularity at every 5-smooth n, but its *partial sums* cross the
same boundary as the factorial series, at the same place — n = 7.

## Reproduce

```bash
python ideas/taylor_series.py   # all tables above, computed exactly
pytest tests/test_taylor.py     # 24 tests: coefficients, regularity boundary, Basel, rendering
```

All arithmetic is exact (`Fraction` / `Sexa` / `RationalTaylorSeries` from
`cuneiform.cas`). Non-terminating expansions are truncated and explicitly
marked with `...` — no floating point anywhere.
