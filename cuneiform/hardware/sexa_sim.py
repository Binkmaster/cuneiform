"""Sexagesimal ALU — cycle-accurate behavioral simulation in Python.

Simulates the hardware ALU spec from the Phase 5 document:
- SEXA6 digits (0-59), SEXA48/SEXA96 words
- Carry-60 addition, 60x60 multiplication ROM
- 1-cycle regularity classification (COFACT)
- Rational arithmetic instructions
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from fractions import Fraction
from math import gcd


class Op(Enum):
    """ALU opcodes."""
    SADD = auto()    # Sexagesimal add
    SSUB = auto()    # Sexagesimal subtract
    SMUL = auto()    # Sexagesimal multiply
    SDIV = auto()    # Sexagesimal divide (regular divisors)
    SMOD = auto()    # Sexagesimal modular reduction
    SINV = auto()    # Reciprocal
    SPOW = auto()    # Power
    RADD = auto()    # Rational add
    RSUB = auto()    # Rational subtract
    RMUL = auto()    # Rational multiply
    RDIV = auto()    # Rational divide
    RNORM = auto()   # Normalize rational
    RCLASS = auto()  # Regularity classify
    SMOOTH = auto()  # B-smooth test
    COFACT = auto()  # Extract cofactor
    ISREG = auto()   # Test regular flag
    LOAD = auto()    # Load immediate
    STORE = auto()   # Store to memory
    NOP = auto()     # No operation


@dataclass
class Instruction:
    """A single ALU instruction."""
    op: Op
    dest: int = 0      # Destination register index
    src1: int = 0      # Source register 1
    src2: int = 0      # Source register 2
    imm: int = 0       # Immediate value


@dataclass
class SexaRegister:
    """A sexagesimal register holding up to 16 base-60 digits (96 bits)."""
    digits: list[int] = field(default_factory=lambda: [0] * 16)

    @classmethod
    def from_int(cls, n: int) -> SexaRegister:
        """Convert integer to sexagesimal digits (little-endian)."""
        digits = []
        val = abs(n)
        for _ in range(16):
            digits.append(val % 60)
            val //= 60
        reg = cls(digits)
        reg._negative = n < 0
        return reg

    def to_int(self) -> int:
        """Convert back to integer."""
        result = 0
        for i in range(len(self.digits) - 1, -1, -1):
            result = result * 60 + self.digits[i]
        if hasattr(self, '_negative') and self._negative:
            return -result
        return result

    def to_notation(self) -> str:
        """Display as sexagesimal notation."""
        # Find highest non-zero digit
        top = 15
        while top > 0 and self.digits[top] == 0:
            top -= 1
        parts = [str(self.digits[i]) for i in range(top, -1, -1)]
        return ",".join(parts)


# Precomputed 60x60 multiplication ROM (3600 entries)
_MUL_ROM: dict[tuple[int, int], tuple[int, int]] = {}
for _a in range(60):
    for _b in range(60):
        _prod = _a * _b
        _MUL_ROM[(_a, _b)] = (_prod % 60, _prod // 60)  # (low, carry)


# Precomputed reciprocal table for regular numbers up to 60^2
_RECIP_TABLE: dict[int, Fraction] = {}
for _a in range(1, 3601):
    _t = _a
    for _p in (2, 3, 5):
        while _t % _p == 0:
            _t //= _p
    if _t == 1:  # Regular number
        _RECIP_TABLE[_a] = Fraction(1, _a)


@dataclass
class ALUFlags:
    """Status flags."""
    regular: bool = False
    overflow: bool = False
    division_by_irregular: bool = False
    zero: bool = False


class SexaALU:
    """Sexagesimal Arithmetic Logic Unit — behavioral simulation.

    16 general-purpose SEXA96 registers (S0-S15).
    4 rational registers (R0-R3) as Fraction pairs.
    1 regularity register.
    Cycle counter for performance analysis.
    """

    def __init__(self):
        self.regs: list[SexaRegister] = [SexaRegister() for _ in range(16)]
        self.rat_regs: list[Fraction] = [Fraction(0)] * 4
        self.regularity_reg: tuple[int, int, int] = (0, 0, 0)  # (a,b,c) for 2^a*3^b*5^c
        self.flags = ALUFlags()
        self.cycles = 0
        self.instruction_count = 0

    def reset(self):
        """Reset all state."""
        self.regs = [SexaRegister() for _ in range(16)]
        self.rat_regs = [Fraction(0)] * 4
        self.regularity_reg = (0, 0, 0)
        self.flags = ALUFlags()
        self.cycles = 0
        self.instruction_count = 0

    def load(self, reg: int, value: int):
        """Load an integer into a register."""
        self.regs[reg] = SexaRegister.from_int(value)

    def read(self, reg: int) -> int:
        """Read integer from a register."""
        return self.regs[reg].to_int()

    def execute(self, inst: Instruction) -> int | None:
        """Execute a single instruction. Returns result value or None."""
        self.instruction_count += 1
        op = inst.op

        if op == Op.NOP:
            self.cycles += 1
            return None

        elif op == Op.LOAD:
            self.regs[inst.dest] = SexaRegister.from_int(inst.imm)
            self.cycles += 1
            return inst.imm

        elif op == Op.SADD:
            a = self.regs[inst.src1].to_int()
            b = self.regs[inst.src2].to_int()
            result = a + b
            self.regs[inst.dest] = SexaRegister.from_int(result)
            self.flags.zero = result == 0
            self.cycles += 1  # Single cycle
            return result

        elif op == Op.SSUB:
            a = self.regs[inst.src1].to_int()
            b = self.regs[inst.src2].to_int()
            result = a - b
            self.regs[inst.dest] = SexaRegister.from_int(result)
            self.flags.zero = result == 0
            self.cycles += 1
            return result

        elif op == Op.SMUL:
            a = self.regs[inst.src1].to_int()
            b = self.regs[inst.src2].to_int()
            result = a * b
            self.regs[inst.dest] = SexaRegister.from_int(result)
            self.cycles += 2  # ROM lookup + accumulate
            return result

        elif op == Op.SDIV:
            a = self.regs[inst.src1].to_int()
            b = self.regs[inst.src2].to_int()
            if b == 0:
                self.flags.division_by_irregular = True
                self.cycles += 1
                return None
            result = a // b
            self.regs[inst.dest] = SexaRegister.from_int(result)
            self.cycles += 3  # Iterative division
            return result

        elif op == Op.SMOD:
            a = self.regs[inst.src1].to_int()
            b = self.regs[inst.src2].to_int()
            if b == 0:
                self.cycles += 1
                return None
            result = a % b
            self.regs[inst.dest] = SexaRegister.from_int(result)
            self.cycles += 3
            return result

        elif op == Op.SINV:
            a = self.regs[inst.src1].to_int()
            if a == 0:
                self.flags.division_by_irregular = True
                self.cycles += 1
                return None
            # Check reciprocal table
            if abs(a) in _RECIP_TABLE:
                self.flags.regular = True
                frac = _RECIP_TABLE[abs(a)]
                self.rat_regs[inst.dest % 4] = frac if a > 0 else -frac
                self.cycles += 1  # Table lookup
                return int(frac.numerator)
            else:
                self.flags.regular = False
                self.flags.division_by_irregular = True
                self.cycles += 1
                return None

        elif op == Op.SPOW:
            base = self.regs[inst.src1].to_int()
            exp = inst.imm
            result = pow(base, exp)
            self.regs[inst.dest] = SexaRegister.from_int(result)
            # Repeated squaring: log2(exp) cycles
            self.cycles += max(1, exp.bit_length()) if exp > 0 else 1
            return result

        elif op == Op.COFACT:
            # THE KEY 1-CYCLE OPERATION: extract 5-smooth part
            a = abs(self.regs[inst.src1].to_int())
            if a == 0:
                self.cycles += 1
                return 0
            cofactor = a
            exp2 = exp3 = exp5 = 0
            while cofactor % 2 == 0:
                cofactor //= 2
                exp2 += 1
            while cofactor % 3 == 0:
                cofactor //= 3
                exp3 += 1
            while cofactor % 5 == 0:
                cofactor //= 5
                exp5 += 1
            self.regularity_reg = (exp2, exp3, exp5)
            self.regs[inst.dest] = SexaRegister.from_int(cofactor)
            self.flags.regular = cofactor == 1
            self.cycles += 1  # Combinational logic in hardware
            return cofactor

        elif op == Op.RCLASS:
            a = abs(self.regs[inst.src1].to_int())
            if a == 0:
                self.cycles += 1
                return 0
            cofactor = a
            for p in (2, 3, 5):
                while cofactor % p == 0:
                    cofactor //= p
            self.flags.regular = cofactor == 1
            # Count prime factors of cofactor for tier
            tier = 0
            if cofactor > 1:
                temp = cofactor
                d = 2
                while d * d <= temp:
                    while temp % d == 0:
                        tier += 1
                        temp //= d
                    d += 1
                if temp > 1:
                    tier += 1
            self.regs[inst.dest] = SexaRegister.from_int(tier)
            self.cycles += 1
            return tier

        elif op == Op.SMOOTH:
            a = abs(self.regs[inst.src1].to_int())
            B = inst.imm
            if a == 0:
                self.cycles += 1
                return 0
            temp = a
            d = 2
            while d <= B and d * d <= temp:
                while temp % d == 0:
                    temp //= d
                d += 1 if d == 2 else 2
            is_smooth = temp <= B
            self.flags.regular = is_smooth
            self.regs[inst.dest] = SexaRegister.from_int(1 if is_smooth else 0)
            self.cycles += 10  # Iterative
            return 1 if is_smooth else 0

        elif op == Op.ISREG:
            self.cycles += 1
            return 1 if self.flags.regular else 0

        # Rational operations
        elif op == Op.RADD:
            a = self.rat_regs[inst.src1 % 4]
            b = self.rat_regs[inst.src2 % 4]
            self.rat_regs[inst.dest % 4] = a + b
            self.cycles += 3
            return int((a + b).numerator)

        elif op == Op.RSUB:
            a = self.rat_regs[inst.src1 % 4]
            b = self.rat_regs[inst.src2 % 4]
            self.rat_regs[inst.dest % 4] = a - b
            self.cycles += 3
            return int((a - b).numerator)

        elif op == Op.RMUL:
            a = self.rat_regs[inst.src1 % 4]
            b = self.rat_regs[inst.src2 % 4]
            self.rat_regs[inst.dest % 4] = a * b
            self.cycles += 4
            return int((a * b).numerator)

        elif op == Op.RDIV:
            a = self.rat_regs[inst.src1 % 4]
            b = self.rat_regs[inst.src2 % 4]
            if b == 0:
                self.flags.division_by_irregular = True
                self.cycles += 1
                return None
            self.rat_regs[inst.dest % 4] = a / b
            self.cycles += 4
            return int((a / b).numerator)

        elif op == Op.RNORM:
            r = self.rat_regs[inst.src1 % 4]
            # Already normalized by Fraction, but check regularity
            if r.denominator > 0:
                temp = r.denominator
                for p in (2, 3, 5):
                    while temp % p == 0:
                        temp //= p
                self.flags.regular = temp == 1
            self.rat_regs[inst.dest % 4] = r
            self.cycles += 2
            return int(r.numerator)

        return None

    def run_program(self, instructions: list[Instruction]) -> list[int | None]:
        """Execute a sequence of instructions."""
        results = []
        for inst in instructions:
            results.append(self.execute(inst))
        return results

    def stats(self) -> dict:
        """Performance statistics."""
        return {
            "cycles": self.cycles,
            "instructions": self.instruction_count,
            "cpi": self.cycles / self.instruction_count if self.instruction_count > 0 else 0,
            "flags": {
                "regular": self.flags.regular,
                "overflow": self.flags.overflow,
                "zero": self.flags.zero,
            },
        }

    def benchmark_cofact(self, numbers: list[int]) -> dict:
        """Benchmark COFACT operation on a set of numbers."""
        self.reset()
        for n in numbers:
            self.load(0, n)
            self.execute(Instruction(Op.COFACT, dest=1, src1=0))
        return {
            "count": len(numbers),
            "total_cycles": self.cycles,
            "avg_cycles_per_cofact": self.cycles / len(numbers) if numbers else 0,
        }

    def benchmark_smooth(self, numbers: list[int], bound: int) -> dict:
        """Benchmark SMOOTH test on a set of numbers."""
        self.reset()
        smooth_count = 0
        for n in numbers:
            self.load(0, n)
            result = self.execute(Instruction(Op.SMOOTH, dest=1, src1=0, imm=bound))
            if result == 1:
                smooth_count += 1
        return {
            "count": len(numbers),
            "smooth_count": smooth_count,
            "total_cycles": self.cycles,
            "avg_cycles_per_test": self.cycles / len(numbers) if numbers else 0,
        }
