"""Sexagesimal (base-60) number representation & arithmetic.

The fundamental data type. Internally backed by Python's Fraction for exact
arithmetic; the sexagesimal digit representation is a display/conversion layer.

Convention: semicolon separates integer;fractional parts, commas separate digits.
This is standard Assyriological notation. E.g., 1;30,15 means 1*60^0 + 30*60^-1 + 15*60^-2.
"""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
from functools import total_ordering

from .smooth import is_smooth, smooth_exponents


class IrregularError(ArithmeticError):
    """Raised when an operation would produce a non-terminating
    sexagesimal expansion (division by non-regular number)."""
    pass


# Unicode cuneiform numeral blocks
# Old Babylonian used two symbols: a vertical wedge (1) and a corner wedge (10).
# Unicode cuneiform numbers: U+12400-U+1246E
_CUNEIFORM_ONES = [
    "",           # 0 (placeholder -- Babylonians had no zero initially)
    "\U00012415",  # 1  𒐕
    "\U00012416",  # 2  𒐖
    "\U00012417",  # 3  𒐗
    "\U00012418",  # 4  𒐘
    "\U00012419",  # 5  𒐙
    "\U0001241A",  # 6  𒐚
    "\U0001241B",  # 7  𒐛
    "\U0001241C",  # 8  𒐜
    "\U0001241D",  # 9  𒐝
]

_CUNEIFORM_TENS = [
    "",           # 0
    "\U0001230B",  # 10  𒌋
    "\U00012439",  # 20  𒐹
    "\U0001243A",  # 30  𒐺
    "\U0001243B",  # 40  𒐻
    "\U0001243C",  # 50  𒐼
]


def _digit_to_cuneiform(d: int) -> str:
    """Convert a single sexagesimal digit (0-59) to cuneiform Unicode."""
    if d == 0:
        return "\U0001243F"  # 𒐿 (a space/placeholder)
    tens, ones = divmod(d, 10)
    result = ""
    if tens > 0 and tens < len(_CUNEIFORM_TENS):
        result += _CUNEIFORM_TENS[tens]
    if ones > 0 and ones < len(_CUNEIFORM_ONES):
        result += _CUNEIFORM_ONES[ones]
    return result or "\U0001243F"


@total_ordering
class Sexa:
    """A sexagesimal (base-60) number with exact rational value.

    Internally stores a Fraction. The sexagesimal digit representation
    is computed on demand. All arithmetic is exact via Fraction.

    Convention: semicolon separates integer;fractional parts,
    commas separate digits. Standard Assyriological notation.
    """

    __slots__ = ("_frac",)

    def __init__(self, value: int | Fraction | str = 0):
        if isinstance(value, Fraction):
            self._frac = value
        elif isinstance(value, int):
            self._frac = Fraction(value)
        elif isinstance(value, str):
            self._frac = self._parse_notation(value)
        elif isinstance(value, Sexa):
            self._frac = value._frac
        else:
            raise TypeError(f"Cannot create Sexa from {type(value)}")

    @classmethod
    def _from_frac(cls, f: Fraction) -> Sexa:
        """Fast internal constructor."""
        obj = object.__new__(cls)
        obj._frac = f
        return obj

    # --- Constructors ---

    @classmethod
    def from_int(cls, n: int) -> Sexa:
        return cls(n)

    @classmethod
    def from_fraction(cls, num: int, den: int) -> Sexa:
        """Convert rational to sexagesimal.

        Raises IrregularError if denominator is not regular
        (non-terminating expansion).
        """
        if not is_smooth(den):
            raise IrregularError(
                f"Denominator {den} is not 5-smooth; "
                f"fraction {num}/{den} has no terminating sexagesimal expansion"
            )
        return cls(Fraction(num, den))

    @classmethod
    def from_decimal(cls, s: str) -> Sexa:
        """Parse a decimal string like '1.5' or '0.00694444'."""
        return cls(Fraction(s))

    @classmethod
    def from_notation(cls, s: str) -> Sexa:
        """Parse Assyriological notation like '1;30,15' or '0;0,44,26,40'."""
        return cls(s)

    @staticmethod
    def _parse_notation(s: str) -> Fraction:
        """Parse '1;30,15' notation into a Fraction."""
        s = s.strip()
        negative = s.startswith("-")
        if negative:
            s = s[1:].strip()

        if ";" in s:
            int_part_str, frac_part_str = s.split(";", 1)
        else:
            int_part_str = s
            frac_part_str = ""

        # Parse integer digits
        if int_part_str:
            int_digits = [int(d.strip()) for d in int_part_str.split(",") if d.strip()]
        else:
            int_digits = [0]

        # Compute integer part
        int_value = 0
        for d in int_digits:
            if not 0 <= d <= 59:
                raise ValueError(f"Sexagesimal digit must be 0-59, got {d}")
            int_value = int_value * 60 + d

        # Parse fractional digits
        frac_value = Fraction(0)
        if frac_part_str:
            frac_digits = [int(d.strip()) for d in frac_part_str.split(",") if d.strip()]
            place = Fraction(1, 60)
            for d in frac_digits:
                if not 0 <= d <= 59:
                    raise ValueError(f"Sexagesimal digit must be 0-59, got {d}")
                frac_value += d * place
                place /= 60

        result = Fraction(int_value) + frac_value
        if negative:
            result = -result
        return result

    # --- Properties ---

    @property
    def is_regular(self) -> bool:
        """Is the denominator 5-smooth? (Terminates in base 60.)"""
        return is_smooth(self._frac.denominator)

    @property
    def reciprocal(self) -> Sexa:
        """Exact reciprocal. Raises IrregularError if result is not regular."""
        if self._frac == 0:
            raise ZeroDivisionError("Reciprocal of zero")
        result = Fraction(1) / self._frac
        if not is_smooth(result.denominator):
            raise IrregularError(
                f"Reciprocal of {self} is not regular "
                f"(denominator {result.denominator} is not 5-smooth)"
            )
        return Sexa._from_frac(result)

    @property
    def as_fraction(self) -> Fraction:
        return self._frac

    @property
    def as_decimal(self) -> Decimal:
        return Decimal(self._frac.numerator) / Decimal(self._frac.denominator)

    # --- Sexagesimal digit extraction ---

    def digits(self, max_frac_digits: int = 20) -> tuple[list[int], list[int], bool]:
        """Extract sexagesimal digits.

        Returns (integer_digits, fractional_digits, negative).
        Integer digits are most-significant first.
        Fractional digits are most-significant first (i.e., 60ths, then 3600ths, etc).
        """
        f = self._frac
        negative = f < 0
        f = abs(f)

        int_part = int(f)
        frac_part = f - int_part

        # Integer digits
        if int_part == 0:
            int_digits = [0]
        else:
            int_digits = []
            n = int_part
            while n > 0:
                int_digits.append(n % 60)
                n //= 60
            int_digits.reverse()

        # Fractional digits
        frac_digits = []
        remainder = frac_part
        for _ in range(max_frac_digits):
            if remainder == 0:
                break
            remainder *= 60
            digit = int(remainder)
            frac_digits.append(digit)
            remainder -= digit

        return int_digits, frac_digits, negative

    # --- Arithmetic ---

    def __add__(self, other: Sexa | int) -> Sexa:
        other = self._coerce(other)
        return Sexa._from_frac(self._frac + other._frac)

    def __radd__(self, other: int) -> Sexa:
        return Sexa._from_frac(Fraction(other) + self._frac)

    def __sub__(self, other: Sexa | int) -> Sexa:
        other = self._coerce(other)
        return Sexa._from_frac(self._frac - other._frac)

    def __rsub__(self, other: int) -> Sexa:
        return Sexa._from_frac(Fraction(other) - self._frac)

    def __mul__(self, other: Sexa | int) -> Sexa:
        other = self._coerce(other)
        return Sexa._from_frac(self._frac * other._frac)

    def __rmul__(self, other: int) -> Sexa:
        return Sexa._from_frac(Fraction(other) * self._frac)

    def __truediv__(self, other: Sexa | int) -> Sexa:
        """Division. Returns exact result.

        Note: unlike from_fraction(), this does NOT enforce regularity.
        The result may be irregular (non-terminating in base 60).
        Use from_fraction() if you want the regularity check.
        """
        other = self._coerce(other)
        if other._frac == 0:
            raise ZeroDivisionError("Division by zero")
        return Sexa._from_frac(self._frac / other._frac)

    def __rtruediv__(self, other: int) -> Sexa:
        if self._frac == 0:
            raise ZeroDivisionError("Division by zero")
        return Sexa._from_frac(Fraction(other) / self._frac)

    def __mod__(self, other: Sexa | int) -> Sexa:
        other = self._coerce(other)
        return Sexa._from_frac(self._frac % other._frac)

    def __pow__(self, exp: int) -> Sexa:
        return Sexa._from_frac(self._frac ** exp)

    def __neg__(self) -> Sexa:
        return Sexa._from_frac(-self._frac)

    def __abs__(self) -> Sexa:
        return Sexa._from_frac(abs(self._frac))

    def __pos__(self) -> Sexa:
        return self

    # --- Comparison ---

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Sexa):
            return self._frac == other._frac
        if isinstance(other, (int, Fraction)):
            return self._frac == other
        return NotImplemented

    def __lt__(self, other: Sexa | int) -> bool:
        other = self._coerce(other)
        return self._frac < other._frac

    def __hash__(self) -> int:
        return hash(self._frac)

    def __bool__(self) -> bool:
        return self._frac != 0

    def __float__(self) -> float:
        return float(self._frac)

    def __int__(self) -> int:
        return int(self._frac)

    # --- Display ---

    def __repr__(self) -> str:
        """Assyriological notation: e.g., '1;30,15' or '0;0,44,26,40'."""
        int_digits, frac_digits, negative = self.digits()
        sign = "-" if negative else ""
        int_str = ",".join(str(d) for d in int_digits)
        if frac_digits:
            frac_str = ",".join(str(d) for d in frac_digits)
            return f"{sign}{int_str};{frac_str}"
        return f"{sign}{int_str}"

    def __str__(self) -> str:
        return self.__repr__()

    def cuneiform(self) -> str:
        """Unicode cuneiform numeral display."""
        int_digits, frac_digits, negative = self.digits()
        sign = "-" if negative else ""
        int_str = " ".join(_digit_to_cuneiform(d) for d in int_digits)
        if frac_digits:
            frac_str = " ".join(_digit_to_cuneiform(d) for d in frac_digits)
            return f"{sign}{int_str} ; {frac_str}"
        return f"{sign}{int_str}"

    # --- Conversion ---

    def to_sexarational(self) -> "SexaRational":
        """Convert to SexaRational."""
        from .rational import SexaRational
        return SexaRational._from_frac(self._frac)

    @staticmethod
    def _coerce(other) -> Sexa:
        if isinstance(other, Sexa):
            return other
        if isinstance(other, int):
            return Sexa._from_frac(Fraction(other))
        if isinstance(other, Fraction):
            return Sexa._from_frac(other)
        raise TypeError(f"Cannot coerce {type(other)} to Sexa")
