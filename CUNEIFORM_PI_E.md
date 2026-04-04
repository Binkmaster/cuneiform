# Pi, e, and Their Expressions in Babylonian Sexagesimal Cuneiform

## The Constants on a Clay Tablet

### Pi in Base 60

```
π = 3;8,29,44,0,47,25,53,7,...
    𒐗 ; 𒐜 𒐹𒐝 𒐻𒐘 𒐿 𒐻𒐛 𒐹𒐙
```

This reads: **3** whole units, plus **8** sixtieths, plus **29** thirty-six-hundredths,
plus **44**/216000ths, and so on. Each "digit" ranges from 0 to 59.

### Euler's Number in Base 60

```
e = 2;43,5,48,52,29,48,35,6,...
    𒐖 ; 𒐻𒐗 𒐙 𒐻𒐜 𒐼𒐖 𒐹𒐝 𒐻𒐜
```

### Expressions

| Expression | Decimal | Sexagesimal | Cuneiform |
|---|---|---|---|
| π + e | 5.85987... | 5;51,35,32,53,17,14 | 𒐙 ; 𒐼𒐕 𒐺𒐙 𒐺𒐖 𒐼𒐗 |
| π − e | 0.42331... | 0;25,23,55,8,17,37 | 𒐿 ; 𒐹𒐙 𒐹𒐗 𒐼𒐙 𒐜 |
| π × e | 8.53973... | 8;32,23,2,35,31,33 | 𒐜 ; 𒐺𒐖 𒐹𒐗 𒐖 𒐺𒐙 |
| π / e | 1.15572... | 1;9,20,37,6,27,11 | 𒐕 ; 𒐝 𒐹 𒐺𒐛 𒐚 |
| π^π | 36.4621... | 36;27,43,46,28,30,33 | 𒐺𒐚 ; 𒐹𒐛 𒐻𒐗 𒐻𒐚 𒐹𒐜 |
| e^e | 15.1542... | 15;9,15,20,38,38,58 | 𒌋𒐙 ; 𒐝 𒌋𒐙 𒐹 𒐺𒐜 |
| π^e | 22.4591... | 22;27,32,58,4,1,47 | 𒐹𒐖 ; 𒐹𒐛 𒐺𒐖 𒐼𒐜 𒐘 |
| π^√2 | 5.04749... | 5;2,50,59,24,35,6 | 𒐙 ; 𒐖 𒐼 𒐼𒐝 𒐹𒐘 |
| e^(π²) | 19333.6... | 5,22,13;41,20,40,3,46,20 | 𒐙 𒐹𒐖 𒌋𒐗 ; 𒐻𒐕 𒐹 𒐻 𒐗 |


## How a Babylonian Scribe Could Have Approximated π and e

### Pi: 3;7,30 and Beyond

The Old Babylonian approximation **3;7,30** (= 25/8 = 3.125) appears on tablet YBC 7302
(c. 1800 BCE). This is a *regular number* — its denominator 8 = 2³ is 5-smooth, so it
terminates in base 60. The scribes likely derived it empirically: measure a circle's
circumference and diameter with a rope, compute the ratio, and round to the nearest
convenient regular fraction.

A scribe could have improved on this. If they measured more carefully and obtained
something near 3;8,30 (= 3.14166..., error ~0.00007), they would have been remarkably
close. The fraction 3;8,29,44 is accurate to about 4 sexagesimal places. But 3;8,30
is *regular* (terminates) while π never terminates in any integer base — a fact
the Babylonians could not have known.

### Euler's Number: The Compound Interest Constant

The Babylonians had sophisticated financial mathematics. They computed compound interest
using tables of powers: if a debt grows by 1/60th per month, after n months it is
multiplied by (61/60)^n. The scribes had tables of (61/60)^n for n up to 60.

The limit of (1 + 1/n)^n as n→∞ is e. With n=60 (fitting their base!):
```
(1 + 1/60)^60 = (61/60)^60 ≈ 2.6971...(≈ 2;41,49,...)
```
This is within 0.8% of e. A scribe working with their standard tables of powers
could have stumbled upon this constant, though there is no evidence they recognized
it as special.


## Sexagesimal vs. Decimal: Precision for Irrationals

### The Resolution Advantage

Each sexagesimal "digit" carries more information than a decimal digit:
- 1 sexagesimal place = 1/60 ≈ 0.01667 (finer than 1/10)
- 2 sexagesimal places = 1/3600 ≈ 0.000278 (finer than 3 decimal places)
- n sexagesimal digits ≈ 1.778n decimal digits of precision

So **6 sexagesimal places** give the precision of about **10-11 decimal places**.

### The Regularity Constraint

The real advantage (and limitation) of base 60 is *regularity*. A fraction terminates
in base 60 if and only if its denominator divides some power of 60 — i.e., the
denominator is *5-smooth* (has no prime factors other than 2, 3, or 5). This means:

- 1/2, 1/3, 1/4, 1/5, 1/6, 1/8, 1/9, 1/10, 1/12, 1/15, 1/16, 1/20, 1/24, 1/25,
  1/27, 1/30, 1/32, 1/36, 1/40, 1/45, 1/48, ... all terminate in base 60
- In base 10, only 1/2, 1/4, 1/5, 1/8, 1/10, 1/16, 1/20, 1/25, ... terminate

Base 60 has **more terminating fractions** than base 10, making everyday arithmetic
smoother. But for *irrationals* like π and e, neither system terminates — the advantage
is purely in how many digits of approximation you need to achieve a given precision.

**Verdict:** Sexagesimal is genuinely more efficient for representing irrationals.
You need fewer symbols to achieve the same precision. A Babylonian scribe writing
6 sexagesimal digits of π captures more precision than someone writing 10 decimal
digits.


## Patterns in the Sexagesimal Digits

Some observations on the sexagesimal expansions:

- **π = 3;8,29,44,0,47,25,...** — The zero in position 4 is striking. In Babylonian
  notation (which originally lacked a zero placeholder), this would have caused
  ambiguity — exactly the kind of problem that eventually led to the Babylonian
  invention of a placeholder symbol around 300 BCE.

- **e = 2;43,5,48,52,29,...** — The small digit 5 in position 2 means e is very close
  to 2;43 = 2 + 43/60 = 163/60 ≈ 2.71667. This *regular number* approximation is
  already within 0.06% of e.

- **e^(π²) = 5,22,13;41,...** — This enormous value (≈ 19,334) requires three
  sexagesimal digits for the integer part alone: 5×3600 + 22×60 + 13.

- **π − e = 0;25,23,55,...** — Nearly 25/60 = 5/12, a common regular fraction.
  So π − e ≈ 5/12 to within 0.3%.


## Rational Trigonometry and the Philosophical Tension

Norman Wildberger's rational trigonometry — implemented in this library's `geometry`
module — replaces angles with *spreads* (s = sin²θ) and distances with *quadrances*
(Q = d²). This keeps everything in the rational numbers. The Plimpton 322 tablet, which
lists Pythagorean triples organized by spread, is arguably evidence that the Babylonians
were already thinking this way 3,800 years ago.

The philosophical tension with this exercise is sharp:

1. **The Babylonian approach**: Work entirely with regular rationals. Avoid π by working
   with specific circle measurements. Avoid √2 by working with quadrances. The
   Plimpton 322 tablet never mentions angles or π — it lists exact rational quantities.

2. **This exercise**: Force π, e, and their combinations into the Babylonian system.
   Every sexagesimal expansion we computed above is a *rational approximation* of an
   irrational number — the very thing the Babylonian system was designed to avoid.

3. **The deeper point**: The sexagesimal system is *complete* for practical computation
   without ever needing irrationals. A Babylonian engineer building a ziggurat needed
   the ratio of a circle's circumference to its diameter — but they only needed it to
   the precision of their measuring ropes (~3-4 sexagesimal places). The question
   "what is π to 50 digits?" would have been meaningless to them, not because they
   couldn't compute it, but because their mathematical framework didn't require it.

This library embodies that philosophy: its core arithmetic is exact rational,
its geometry avoids transcendentals entirely, and the `pi.py` module exists as
a deliberate bridge between the ancient rational world and modern analysis.


## Number-Theoretic Status

Perhaps the most remarkable fact about the expressions computed above: **for most of
them, we don't even know if they're irrational.**

| Expression | Known Status | Why It's Hard |
|---|---|---|
| π | Transcendental (Lindemann, 1882) | Proved via e^(iπ) = -1 |
| e | Transcendental (Hermite, 1873) | Direct proof from definition |
| π + e | **Unknown** | Would follow from Schanuel's conjecture |
| π × e | **Unknown** | At least one of π+e, πe must be transcendental |
| π^π | **Unknown** | Neither Gelfond-Schneider nor L-W applies |
| e^e | **Unknown** | Transcendental exponent blocks L-W |
| e^(π²) | **Unknown** | Doubly transcendental composition |

We *believe* all of these are transcendental, but proof eludes us. Schanuel's conjecture
(1960s, still unproven) would settle all of them at once, but it remains one of the
deepest open problems in transcendental number theory.

The Babylonians, working entirely with rationals, sidestepped this problem entirely.

---

*Generated using the [cuneiform](https://github.com/Binkmaster/cuneiform) Python library
for exact sexagesimal arithmetic, rational trigonometry, and Babylonian mathematical
computation.*
