"""Scribe mode — step-by-step Babylonian calculation methods.

Shows each intermediate step the way an Old Babylonian scribe
would have computed it, in sexagesimal notation with explanations.
"""

from __future__ import annotations

from fractions import Fraction
from math import isqrt

from cuneiform.core.sexagesimal import Sexa
from cuneiform.core.smooth import is_smooth


# Standard Babylonian reciprocal table (base values)
_STANDARD_TABLE = {
    2: 30, 3: 20, 4: 15, 5: 12, 6: 10, 8: Fraction(7, 60) * 60 + 30,
    9: Fraction(6, 60) * 60 + 40, 10: 6, 12: 5, 15: 4, 16: Fraction(3, 60) * 60 + 45,
    18: Fraction(3, 60) * 60 + 20, 20: 3, 24: Fraction(2, 60) * 60 + 30,
    25: Fraction(2, 60) * 60 + 24, 27: Fraction(2, 60) * 60 + Fraction(13, 60) + Fraction(20, 3600),
    30: 2, 32: Fraction(1, 60) * 60 + Fraction(52, 60) * 60 + 30,
    36: Fraction(1, 60) * 60 + 40, 40: Fraction(1, 60) * 60 + 30,
    45: Fraction(1, 60) * 60 + 20, 48: Fraction(1, 60) * 60 + 15,
    50: Fraction(1, 60) * 60 + 12, 54: Fraction(1, 60) * 60 + Fraction(6, 60) * 60 + 40,
}


def _sexa_str(val) -> str:
    """Convert a value to sexagesimal string representation."""
    if isinstance(val, Sexa):
        return str(val)
    if isinstance(val, Fraction):
        return str(Sexa(val))
    return str(Sexa.from_int(val))


class ScribeMode:
    """Step-by-step OB calculation methods with sexagesimal output."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.steps: list[str] = []

    def _step(self, msg: str):
        """Record a calculation step."""
        self.steps.append(msg)

    def _reset(self):
        self.steps = []

    def multiply(self, a: int, b: int) -> dict:
        """Multiply using the Babylonian method.

        For single-digit (< 60) operands: direct table lookup.
        For larger: decompose using base-60 positional notation.
        Also shows quarter-squares identity: a*b = ((a+b)/2)^2 - ((a-b)/2)^2
        """
        self._reset()
        self._step(f"Computing {a} × {b}")
        self._step(f"In sexagesimal: {_sexa_str(a)} × {_sexa_str(b)}")

        result = a * b

        if a < 60 and b < 60:
            self._step(f"Single-digit multiplication: look up {a} × {b} = {result}")
            self._step(f"Result: {_sexa_str(result)}")
        else:
            # Decompose into base-60 digits
            a_sexa = Sexa.from_int(a)
            b_sexa = Sexa.from_int(b)
            self._step(f"Decompose: {a} = {a_sexa}, {b} = {b_sexa}")

            # Show partial products
            a_int_digits, _, _ = a_sexa.digits()
            b_int_digits, _, _ = b_sexa.digits()
            self._step("Partial products:")
            for i, ad in enumerate(reversed(a_int_digits)):
                for j, bd in enumerate(reversed(b_int_digits)):
                    partial = ad * bd
                    pos = i + j
                    self._step(f"  {ad} × {bd} × 60^{pos} = {partial} × 60^{pos}")

            self._step(f"Sum of partial products: {result}")
            self._step(f"Result: {_sexa_str(result)}")

        # Quarter-squares method
        if a != b:
            s = a + b
            d = abs(a - b)
            if s % 2 == 0 and d % 2 == 0:
                half_s = s // 2
                half_d = d // 2
                self._step(f"\nQuarter-squares check: ((a+b)/2)² - ((a-b)/2)²")
                self._step(f"  = {half_s}² - {half_d}² = {half_s**2} - {half_d**2} = {half_s**2 - half_d**2}")

        return {
            "a": a, "b": b,
            "result": result,
            "result_sexa": _sexa_str(result),
            "steps": list(self.steps),
        }

    def find_reciprocal(self, n: int) -> dict:
        """Find reciprocal using the Babylonian method.

        1. Check standard table
        2. If not found, factor and use 1/n = (1/a)(1/b)
        3. If irregular, state it doesn't divide
        """
        self._reset()
        self._step(f"Finding the reciprocal of {n}")
        self._step(f"In sexagesimal: {_sexa_str(n)}")

        if not is_smooth(n):
            self._step(f"{n} is IRREGULAR — it does not divide (igi {n} nu)")
            self._step(f"The reciprocal does not terminate in base 60.")
            return {
                "n": n,
                "is_regular": False,
                "steps": list(self.steps),
            }

        self._step(f"{n} is REGULAR (5-smooth) — its reciprocal terminates")

        # Factor into simple parts
        recip = Fraction(1, n)
        sexa_recip = Sexa(recip)
        self._step(f"1/{n} = {sexa_recip}")

        # Show factoring approach
        factors = []
        temp = n
        for p in (2, 3, 5):
            while temp % p == 0:
                factors.append(p)
                temp //= p

        if len(factors) > 1:
            self._step(f"Factoring: {n} = {' × '.join(str(f) for f in factors)}")
            self._step(f"So 1/{n} = " + " × ".join(f"1/{f}" for f in factors))
            for f in factors:
                sexa_f = Sexa(Fraction(1, f))
                self._step(f"  1/{f} = {sexa_f}")

        return {
            "n": n,
            "is_regular": True,
            "reciprocal": recip,
            "reciprocal_sexa": str(sexa_recip),
            "factors": factors,
            "steps": list(self.steps),
        }

    def sqrt_babylonian(self, n: int, iterations: int = 5) -> dict:
        """Compute square root using the OB iterative method.

        Guess g. Compute n/g. New guess = (g + n/g) / 2. Repeat.
        This is Newton's method — but the Babylonians had it 1500 years before Newton.
        """
        self._reset()
        self._step(f"Finding √{n} by the Babylonian method")
        self._step(f"(The same algorithm Newton would 'discover' 3300 years later)")

        # Initial guess: integer square root
        g = Fraction(isqrt(n))
        if g == 0:
            g = Fraction(1)
        self._step(f"Initial guess: g₀ = {g}")

        approximations = [g]
        for i in range(iterations):
            n_over_g = Fraction(n) / g
            new_g = (g + n_over_g) / 2
            self._step(f"Step {i+1}: g_{i+1} = (g_{i} + {n}/g_{i}) / 2")
            self._step(f"  = ({g} + {n_over_g}) / 2 = {new_g}")

            # Show sexagesimal (only if denominator is regular)
            try:
                sexa_g = Sexa(new_g)
                self._step(f"  In sexagesimal: {sexa_g}")
            except Exception:
                self._step(f"  (non-terminating in base 60)")

            # Show error
            error = abs(new_g * new_g - n)
            self._step(f"  Error: g² - n = {float(new_g * new_g - n):.10f}")

            g = new_g
            approximations.append(g)

            if error == 0:
                self._step("Exact result found!")
                break

        # Result sexa string
        try:
            result_sexa = str(Sexa(g))
        except Exception:
            result_sexa = f"{float(g):.10f}"

        return {
            "n": n,
            "result": g,
            "result_float": float(g),
            "result_sexa": result_sexa,
            "iterations": len(approximations) - 1,
            "approximations": [float(a) for a in approximations],
            "steps": list(self.steps),
        }

    def generate_triple(self, p: int, q: int) -> dict:
        """Generate a Pythagorean triple from reciprocal pair (p, q).

        Shows each step as the scribe would have computed it:
        1. Compute x = p/q (regular ratio)
        2. Compute x̄ = q/p (reciprocal)
        3. Width = (x - x̄) / 2
        4. Length = 1 (normalized)
        5. Diagonal = (x + x̄) / 2
        6. Scale to integers
        """
        self._reset()
        self._step(f"Generating Pythagorean triple from pair (p={p}, q={q})")

        x = Fraction(p, q)
        x_bar = Fraction(q, p)
        self._step(f"x = p/q = {p}/{q}")
        self._step(f"x̄ = q/p = {q}/{p}")

        half_diff = (x - x_bar) / 2
        half_sum = (x + x_bar) / 2
        self._step(f"Width = (x - x̄)/2 = ({x} - {x_bar})/2 = {half_diff}")
        self._step(f"Diagonal = (x + x̄)/2 = ({x} + {x_bar})/2 = {half_sum}")
        self._step("Length = 1 (normalized)")

        # Scale to integers
        lcm_denom = half_diff.denominator * half_sum.denominator // \
            __import__('math').gcd(half_diff.denominator, half_sum.denominator)
        w = abs(int(half_diff * lcm_denom))
        l = lcm_denom
        d = abs(int(half_sum * lcm_denom))

        g = __import__('math').gcd(__import__('math').gcd(w, l), d)
        w, l, d = w // g, l // g, d // g

        self._step(f"Scale to integers: ({w}, {l}, {d})")
        self._step(f"Verify: {w}² + {l}² = {w**2} + {l**2} = {w**2 + l**2}")
        self._step(f"        {d}² = {d**2}")
        self._step(f"Check: {w**2 + l**2 == d**2}")

        self._step("\nIn sexagesimal:")
        self._step(f"  Width:    {_sexa_str(w)}")
        self._step(f"  Length:   {_sexa_str(l)}")
        self._step(f"  Diagonal: {_sexa_str(d)}")

        return {
            "p": p, "q": q,
            "triple": (w, l, d),
            "is_pythagorean": w**2 + l**2 == d**2,
            "width_sexa": _sexa_str(w),
            "length_sexa": _sexa_str(l),
            "diagonal_sexa": _sexa_str(d),
            "steps": list(self.steps),
        }
