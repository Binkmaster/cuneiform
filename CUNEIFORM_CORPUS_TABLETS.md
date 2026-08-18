# Four Old Babylonian Tablets, Verified in Exact Sexagesimal

The tablet corpus (`cuneiform/archaeology/tablet_corpus.py`) now holds four
real, well-documented Old Babylonian mathematical tablets beyond the founding
Plimpton 322 and YBC 7289. Each is stored with its published values, rendered
in base 60 and cuneiform, and checked by the corpus analyzer — every
relationship below is verified in exact rational arithmetic, no floating point.

These are not new discoveries. No genuinely *new* mathematical tablet has been
deciphered recently — the 2025 AI-assisted cuneiform work (the Hymn to Babylon,
the Hammurabi Code) is literary and legal text. What these four are is
established, auditable mathematics that fits this library's Pythagorean and
rational-geometry core, sourced from published transliterations.

Two themes run through all four: the Old Babylonians commanded the Pythagorean
relation in practice a millennium before Pythagoras, and they knew π = 3 was a
convenience, not the truth.

## Si.427 — the oldest applied geometry

*Sippar, c. 1900–1600 BCE. Istanbul Archaeological Museums. Identified by
Daniel Mansfield (2021).*

Si.427 is a surveyor's field plan — a cadastral tablet laying out the
boundaries of land for sale. Its mathematical content is that the perpendicular
boundaries are constructed with **Pythagorean ("diagonal") triples**, the
oldest known application of them anywhere. Three triples underlie the survey:

| Triple | a² + b² = c² | Cuneiform |
|--------|--------------|-----------|
| (3, 4, 5) | 9 + 16 = 25 | 𒐗  𒐘  𒐙 |
| (8, 15, 17) | 64 + 225 = 289 | 𒐜  𒌋𒐙  𒌋𒐛 |
| (5, 12, 13) | 25 + 144 = 169 | 𒐙  𒌋𒐖  𒌋𒐗 |

The corpus analyzer classifies Si.427 as a `pythagorean_table` and confirms
every row is an exact triple. What makes these three special to a Babylonian
surveyor is that their sides have **regular (5-smooth) reciprocals**, so the
perpendiculars they build can be scaled and subdivided using the standard
reciprocal tables — the same regularity property that organizes Plimpton 322.

## IM 67118 (Db₂-146) — the Pythagorean theorem, worked and proved

*Tell edh-Dhiba'i (Eshnunna), c. 1770 BCE. Iraq Museum.*

Where Si.427 *uses* triples, IM 67118 *derives* one. It is a complete worked
problem: given a rectangle of area **0;45** (= ¾) and diagonal **1;15** (= 5/4),
find the sides. The scribe solves it by completing the square — cut-and-paste
"naïve geometry" in Høyrup's reading — and then closes the text by verifying the
answer with the Pythagorean relation itself.

| Quantity | Sexagesimal | Value | Cuneiform |
|----------|-------------|-------|-----------|
| width | 0;45 | ¾ | 𒐿 ; 𒐻𒐙 |
| length | 1 | 1 | 𒐕 |
| diagonal | 1;15 | 5/4 | 𒐕 ; 𒌋𒐙 |

The sides are a **3-4-5 triangle scaled by ¼**: (¾)² + 1² = 9/16 + 16/16 =
25/16 = (5/4)², and the area ¾ × 1 = ¾ matches the stated 0;45. This is among
the clearest surviving evidence that Old Babylonian scribes held the
Pythagorean theorem as a computational tool, centuries before Plimpton 322 is
usually dated.

## YBC 11120 — the area of a circle, with π = 3

*Yale Babylonian Collection, Old Babylonian.*

A circle problem: from the circumference, compute the area. The scribe squares
the circumference and multiplies by a fixed coefficient **0;05** (= 1/12):

| Step | Sexagesimal | Value | Cuneiform |
|------|-------------|-------|-----------|
| circumference C | 1;30 | 3/2 | 𒐕 ; 𒐺 |
| C² | 2;15 | 9/4 | 𒐖 ; 𒌋𒐙 |
| area = 0;05 · C² | 0;11,15 | 3/16 | 𒐿 ; 𒌋𒐕 𒌋𒐙 |

The constant 1/12 is exactly 1/(4π) when **π = 3** — the everyday Babylonian
working value, since area = πr² = C²/(4π). The corpus analyzer verifies the
squaring relation C² = (3/2)² = 9/4 and the exact area 3/16. This is the plain,
practical π that most tablets use — which is what makes the next tablet
striking.

## TMS 3 (Susa) — the sharpest Babylonian π, 3;7,30

*Susa (ancient Elam), Old Babylonian. Published by Bruins & Rutten,
*Textes Mathématiques de Suse* (1961).*

The Susa tablets show the scribes knew π = 3 was only an approximation. TMS 3
is a table of geometric coefficients; line 30 gives the constant **0;57,36**
(= 24/25), labeled by Bruins & Rutten *la constante du cercle* — the ratio of
a regular hexagon's perimeter to the circumference of its **circumscribed
circle**.

| Quantity | Sexagesimal | Value | Cuneiform |
|----------|-------------|-------|-----------|
| hexagon perimeter | 6 | 6 | 𒐚 |
| circle circumference | 6;15 | 25/4 | 𒐚 ; 𒌋𒐙 |
| ratio (coefficient) | 0;57,36 | 24/25 | 𒐿 ; 𒐼𒐛 𒐺𒐚 |

A regular hexagon inscribed in a circle has perimeter 6r and the circle has
circumference 2πr, so the ratio is exactly **3/π**. Setting it equal to the
tablet's coefficient:

```
3/π = 0;57,36 = 24/25   ⟹   π = 3 · 25/24 = 25/8 = 3;7,30 = 3.125
```

That is **π = 3;7,30** — 𒐗 ; 𒐛 𒐺 — the sharpest value of π attested in
Babylonian mathematics, and the historical constant reproduced in
`ideas/pi.py`. It is within 0.5% of the true π, and every number in the
derivation is a regular sexagesimal that terminates cleanly on a tablet.

## What the four add up to

| Tablet | Date | The point | Verified relation |
|--------|------|-----------|-------------------|
| Si.427 | c. 1900–1600 BCE | Pythagorean triples used to survey land | a² + b² = c² (3 rows) |
| IM 67118 | c. 1770 BCE | Pythagorean theorem solved and proved | (¾)² + 1² = (5/4)² |
| YBC 11120 | Old Babylonian | Circle area with the working π = 3 | C² = 9/4, area = 3/16 |
| TMS 3 (Susa) | Old Babylonian | The refined π = 3;7,30 = 25/8 | 3/π = 24/25 |

Together they trace a coherent picture: a mathematical culture that used exact
Pythagorean triples for real surveying (Si.427), could solve and justify
right-triangle problems (IM 67118), computed with a convenient π = 3 for
everyday work (YBC 11120), yet knew and recorded a far better value when it
mattered (TMS 3). Every value here is stored and checked in exact base-60
rational arithmetic — the same representation the scribes used.

## Reproduce

```bash
python -c "from cuneiform.archaeology.tablet_corpus import TabletCorpus; \
c = TabletCorpus(); c.load_known_tablets(); \
print({k: v['verified'] for k, v in c.verify_all().items()})"
pytest tests/test_phase6.py -k TabletCorpus   # includes the 5 new-tablet tests
```

## Sources

- Mansfield, D.F. "Plimpton 322: A Study of Rectangles." *Foundations of
  Science* 26, 977–1005 (2021).
- Mansfield, D.F. & Wildberger, N.J. "Perpendicular Lines and Diagonal Triples
  in Old Babylonian Surveying." *Journal of Cuneiform Studies* 72 (2020).
- Baqir, T. "Tell Dhiba'i: New Mathematical Texts." *Sumer* 18 (1962).
- Høyrup, J. *Lengths, Widths, Surfaces: A Portrait of Old Babylonian Algebra
  and Its Kin* (2002).
- Bruins, E.M. & Rutten, M. *Textes Mathématiques de Suse*, MDP 34 (1961).
- Robson, E. *Mathematics in Ancient Iraq: A Social History* (2008).
