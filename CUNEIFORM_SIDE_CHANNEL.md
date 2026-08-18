# Can Base 60 Push a Cryptographic Boundary? One Honest Experiment

The hardness of the elliptic-curve discrete log problem is **representation
invariant**: writing a secret scalar in binary, base 16, or base 60 is a
polynomial-time relabeling and cannot change how hard it is to recover. So a
sexagesimal number system cannot break ECC, and any claim that it "reveals
hidden structure" that factoring or discrete log misses is a dead end.

There is exactly one place where a number's representation legitimately
matters to cryptography, and it is not the math — it is the **implementation**.
A scalar multiplication `k·P` executes a sequence of point DOUBLE and ADD
operations, and that sequence is dictated by how the secret `k` is *encoded*.
A power-analysis side channel sees the sequence, not the number. So the honest
question is narrow and testable:

> Does a base-60 / mixed-radix encoding of the secret scalar leak less to a
> side channel than plain binary?

This experiment answers it with a pre-committed metric and exhaustive
enumeration. The result is graded, and it is not the flattering one.

## The leakage model

Stated up front so the numbers can be judged against it (standard SPA
assumptions):

- The attacker can tell a point **DOUBLE** apart from a point **ADD**.
- The attacker **cannot** tell an ADD from a SUBTRACT (point negation is free
  and looks identical in the trace).
- The attacker **cannot** see which precomputed table entry an ADD used — the
  "hidden table index" assumption. One variant drops this to show how much of
  the base-60 result depends on it.

## The metric (pre-committed, exhaustive)

**Residual attacker uncertainty** = log₂(number of secret scalars consistent
with one observed operation-trace), averaged over all fixed-length scalars.
Higher is safer. It is computed by brute force — enumerate every scalar in
`[2ⁿ⁻¹, 2ⁿ)`, group by the trace the attacker would observe, and measure the
group sizes. No formula is trusted; a second, independent brute-force count is
asserted equal to it in the tests. The leak *rate* (leaked / n) is bitlength
independent, so a 16-bit sweep measures the same rate a 256-bit key shows.

## The result

Exhaustive over all 16-bit scalars; residual projected to a 256-bit key:

| Encoding | Leak rate | Residual (16-bit) | Projected residual @256 |
|----------|-----------|-------------------|--------------------------|
| binary double-and-add | **100%** | 0.0 b | 0.0 b |
| constant ladder (Montgomery) | **0%** | 15.0 b | 256.0 b |
| NAF (signed-digit) | 73% | 4.1 b | 70.2 b |
| base-16 window, hidden index | 7% | 14.0 b | 238.7 b |
| **base-60 window, hidden index** | **2%** | 14.8 b | 251.8 b |
| base-60 window, **leaking index** | **100%** | 0.0 b | 0.0 b |

DPA axis (representation randomization vs. trace averaging): a fixed encoding
produces **1** trace for a fixed secret — no protection against averaging
attacks. A randomized signed-binary recoding produces **~143 distinct traces**
(minimum 75) over 200 runs of the *same* secret, which is what defeats
trace-averaging DPA.

## What it means — the graded, honest reading

**Base 60 does not push a cryptographic boundary, and the table says why.**

1. **The base value, by itself, buys nothing.** Binary double-and-add leaks
   100% of the scalar, and so does a base-60 window whose table lookup leaks
   its index. Same number system, opposite outcomes — because what changed was
   the *operation sequence*, not the base.

2. **What lowers leakage is a generic mechanism, not sexagesimal.** Windowing
   hides digit values behind a table; signed-digit form hides digit signs; a
   constant operation-sequence (Montgomery ladder) hides everything at the SPA
   level. Every one of these is available in any radix. **Base-16 gets
   essentially the same protection as base-60** (7% vs 2% here — a small edge
   that comes from base 60's wider digits, and base 60 pays for it with a
   larger, more leak-prone 59-entry table). There is no sense in which 60 is
   the *right* base.

3. **The one genuine "win" is contingent and reversible.** The base-60 window's
   near-zero leak rate holds *only* while the table lookup is constant-time.
   Drop that assumption and the same encoding jumps to 100% leakage — worse in
   practice than binary, because the table lookup is now the vulnerability.

4. **The only durable idea here is randomization, and it isn't about 60
   either.** Re-randomizing the representation each run defeats DPA averaging.
   A mixed-radix system offers a large, natural randomization space — but the
   protection comes from the *randomness*, not from the base being 60.

## Verdict

This is the strongest honest thread from "cuneiform for crypto," and it lands
as: **no new boundary.** Representation matters to side channels, base-60
windowing sits in the good tier, but for the generic reason any radix-b window
does, and only under an assumption (constant-time table lookup) that is exactly
where real implementations get attacked. The experiment's value is that it is
*falsifiable and came out negative cleanly* — which is worth more than a demo
built to look positive.

## Reproduce

```bash
python ideas/scalar_leakage_experiment.py   # the table above, exhaustively
pytest tests/test_scalar_leakage.py         # 49 tests: encodings, metric vs
                                            # brute force, orderings, DPA axis
```

Every encoding is checked to reconstruct its scalar exactly (so the leakage of
the *wrong* number is never measured), and the residual metric is asserted
equal to an independent brute-force count. Implementation:
`cuneiform/crypto/scalar_leakage.py`.
