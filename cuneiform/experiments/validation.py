"""Self-validation — verify CUNEIFORM's mathematical correctness.

The "verify 10x" requirement from Phase 7 Failure Mode 5.
Runs internal consistency checks across the entire library.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from math import gcd

from cuneiform.core.sexagesimal import Sexa
from cuneiform.core.rational import SexaRational
from cuneiform.core.smooth import is_smooth, generate_smooth_numbers, extract_smooth_part
from cuneiform.tablet.plimpton322 import Plimpton322


@dataclass
class ValidationResult:
    """Result of a validation check."""
    name: str
    passed: bool
    details: str = ""


class SelfValidator:
    """Run all internal consistency checks.

    These are mathematical identities that must hold regardless
    of implementation details. If any fail, there's a bug.
    """

    def __init__(self):
        self.results: list[ValidationResult] = []

    def run_all(self) -> list[ValidationResult]:
        """Run every validation check."""
        self.results = []
        self._check_sexa_roundtrip()
        self._check_arithmetic_identities()
        self._check_plimpton_pythagorean()
        self._check_plimpton_original_15()
        self._check_smooth_number_properties()
        self._check_regularity_decomposition()
        self._check_rational_trig_laws()
        self._check_cas_polynomial_identities()
        return self.results

    @property
    def all_passed(self) -> bool:
        return all(r.passed for r in self.results)

    @property
    def num_passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def num_failed(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    def summary(self) -> str:
        lines = [f"Validation: {self.num_passed}/{len(self.results)} passed"]
        for r in self.results:
            status = "PASS" if r.passed else "FAIL"
            lines.append(f"  [{status}] {r.name}")
            if not r.passed and r.details:
                lines.append(f"         {r.details}")
        return "\n".join(lines)

    def _add(self, name: str, passed: bool, details: str = ""):
        self.results.append(ValidationResult(name, passed, details))

    def _check_sexa_roundtrip(self):
        """Verify Sexa notation roundtrip: parse -> format -> parse."""
        test_cases = ["1;30", "0;0,44,26,40", "1,0;0,0,15", "0;6"]
        all_ok = True
        for s in test_cases:
            sexa = Sexa(s)
            result = str(sexa)
            reparsed = Sexa(result)
            if sexa.as_fraction != reparsed.as_fraction:
                all_ok = False
                break
        self._add("Sexa notation roundtrip", all_ok)

    def _check_arithmetic_identities(self):
        """Verify: (a+b)*c = a*c + b*c for various rationals."""
        cases = [
            (SexaRational(1, 2), SexaRational(1, 3), SexaRational(1, 5)),
            (SexaRational(7), SexaRational(-3), SexaRational(11, 4)),
            (SexaRational(0), SexaRational(100), SexaRational(1, 60)),
        ]
        all_ok = True
        for a, b, c in cases:
            lhs = (a + b) * c
            rhs = a * c + b * c
            if lhs != rhs:
                all_ok = False
                break
        self._add("Distributive law (a+b)*c = a*c + b*c", all_ok)

    def _check_plimpton_pythagorean(self):
        """Every Plimpton row satisfies width^2 + length^2 = diagonal^2."""
        table = Plimpton322()
        rows = table.original()
        all_ok = True
        for row in rows:
            if row.width ** 2 + row.length ** 2 != row.diagonal ** 2:
                all_ok = False
                break
        self._add(f"Plimpton 322: all {len(rows)} rows Pythagorean", all_ok)

    def _check_plimpton_original_15(self):
        """All original 15 rows are present and use regular p, q."""
        table = Plimpton322()
        original = table.original()
        all_ok = len(original) == 15
        for row in original:
            if not is_smooth(row.p) or not is_smooth(row.q):
                all_ok = False
                break
        self._add("Plimpton 322: original 15 rows with regular p,q", all_ok)

    def _check_smooth_number_properties(self):
        """5-smooth numbers are closed under multiplication."""
        smooth = generate_smooth_numbers(100)
        all_ok = True
        for i in range(min(10, len(smooth))):
            for j in range(min(10, len(smooth))):
                product = smooth[i].value * smooth[j].value
                if not is_smooth(product):
                    all_ok = False
                    break
        self._add("5-smooth closure under multiplication", all_ok)

    def _check_regularity_decomposition(self):
        """For all n, n = smooth_part * cofactor, cofactor has no {2,3,5} factors."""
        all_ok = True
        for n in range(1, 200):
            sp, cf = extract_smooth_part(n)
            if sp * cf != n:
                all_ok = False
                break
            if cf > 1 and (cf % 2 == 0 or cf % 3 == 0 or cf % 5 == 0):
                all_ok = False
                break
        self._add("Regularity decomposition n = smooth * cofactor", all_ok)

    def _check_rational_trig_laws(self):
        """Verify spread + cross law for a 3-4-5 triangle."""
        try:
            from cuneiform.geometry.spread import Spread
            from cuneiform.geometry.quadrance import Quadrance
            Q1 = Quadrance(SexaRational(9))   # 3^2
            Q2 = Quadrance(SexaRational(16))  # 4^2
            Q3 = Quadrance(SexaRational(25))  # 5^2
            # Cross law: (Q1 + Q2 - Q3)^2 = 4 * Q1 * Q2 * (1 - s3)
            s3 = Spread.from_sides(Q3, Q1, Q2)
            # s3 = 1 - (9 + 16 - 25)^2 / (4*9*16) = 1 - 0 = 1
            self._add("Rational trig: 3-4-5 has spread 1 at right angle",
                       s3.value == SexaRational(1))
        except Exception as e:
            self._add("Rational trig: 3-4-5 has spread 1 at right angle",
                       False, str(e))

    def _check_cas_polynomial_identities(self):
        """Verify: (x-1)(x+1) = x^2 - 1."""
        try:
            from cuneiform.cas.ratpoly import RatPoly
            p1 = RatPoly([-1, 1])  # x - 1
            p2 = RatPoly([1, 1])   # x + 1
            product = p1 * p2
            expected = RatPoly([-1, 0, 1])  # x^2 - 1
            self._add("CAS: (x-1)(x+1) = x^2 - 1", product == expected)
        except Exception as e:
            self._add("CAS: (x-1)(x+1) = x^2 - 1", False, str(e))
