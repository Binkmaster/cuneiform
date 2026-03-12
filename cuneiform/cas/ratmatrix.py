"""Exact rational matrix operations.

All operations are exact over SexaRational. No floating point.
Determinant, inverse, row reduction, solve Ax=b, characteristic polynomial.
"""

from __future__ import annotations

from fractions import Fraction

from cuneiform.core.rational import SexaRational
from .ratpoly import RatPoly


class RatMatrix:
    """An m×n matrix with SexaRational entries.

    Stored as list of rows, each row a list of SexaRational.
    """

    __slots__ = ("rows", "m", "n")

    def __init__(self, rows: list[list[SexaRational | int | Fraction]]):
        if not rows or not rows[0]:
            raise ValueError("Matrix must have at least one entry")
        self.m = len(rows)
        self.n = len(rows[0])
        self.rows = []
        for row in rows:
            if len(row) != self.n:
                raise ValueError("All rows must have the same length")
            self.rows.append([
                v if isinstance(v, SexaRational) else SexaRational(v)
                for v in row
            ])

    @classmethod
    def identity(cls, n: int) -> RatMatrix:
        rows = []
        for i in range(n):
            row = [SexaRational(0)] * n
            row[i] = SexaRational(1)
            rows.append(row)
        return cls(rows)

    @classmethod
    def zero(cls, m: int, n: int) -> RatMatrix:
        return cls([[SexaRational(0)] * n for _ in range(m)])

    @property
    def is_square(self) -> bool:
        return self.m == self.n

    @property
    def shape(self) -> tuple[int, int]:
        return (self.m, self.n)

    def __getitem__(self, idx: tuple[int, int]) -> SexaRational:
        i, j = idx
        return self.rows[i][j]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RatMatrix):
            return NotImplemented
        return self.rows == other.rows

    def __add__(self, other: RatMatrix) -> RatMatrix:
        if self.shape != other.shape:
            raise ValueError("Matrix dimensions must match for addition")
        return RatMatrix([
            [self.rows[i][j] + other.rows[i][j] for j in range(self.n)]
            for i in range(self.m)
        ])

    def __sub__(self, other: RatMatrix) -> RatMatrix:
        if self.shape != other.shape:
            raise ValueError("Matrix dimensions must match for subtraction")
        return RatMatrix([
            [self.rows[i][j] - other.rows[i][j] for j in range(self.n)]
            for i in range(self.m)
        ])

    def __mul__(self, other: RatMatrix) -> RatMatrix:
        """Matrix multiplication."""
        if self.n != other.m:
            raise ValueError(
                f"Cannot multiply {self.m}×{self.n} by {other.m}×{other.n}"
            )
        result = []
        for i in range(self.m):
            row = []
            for j in range(other.n):
                s = SexaRational(0)
                for k in range(self.n):
                    s = s + self.rows[i][k] * other.rows[k][j]
                row.append(s)
            result.append(row)
        return RatMatrix(result)

    def __neg__(self) -> RatMatrix:
        return RatMatrix([[-v for v in row] for row in self.rows])

    def scale(self, s: SexaRational | int) -> RatMatrix:
        if isinstance(s, int):
            s = SexaRational(s)
        return RatMatrix([[v * s for v in row] for row in self.rows])

    def transpose(self) -> RatMatrix:
        return RatMatrix([
            [self.rows[i][j] for i in range(self.m)]
            for j in range(self.n)
        ])

    def det(self) -> SexaRational:
        """Determinant via Bareiss algorithm (fraction-free). Exact."""
        if not self.is_square:
            raise ValueError("Determinant requires square matrix")
        n = self.m
        if n == 1:
            return self.rows[0][0]

        # Copy to working matrix (as Fractions for speed)
        M = [[v.as_fraction for v in row] for row in self.rows]

        sign = 1
        for col in range(n):
            # Find pivot
            pivot_row = None
            for r in range(col, n):
                if M[r][col] != 0:
                    pivot_row = r
                    break
            if pivot_row is None:
                return SexaRational(0)
            if pivot_row != col:
                M[col], M[pivot_row] = M[pivot_row], M[col]
                sign *= -1

            pivot = M[col][col]
            for r in range(col + 1, n):
                if M[r][col] == 0:
                    continue
                factor = M[r][col] / pivot
                for c in range(col, n):
                    M[r][c] = M[r][c] - factor * M[col][c]

        result = Fraction(sign)
        for i in range(n):
            result *= M[i][i]
        return SexaRational(result)

    def inverse(self) -> RatMatrix:
        """Matrix inverse via Gauss-Jordan elimination. Exact."""
        if not self.is_square:
            raise ValueError("Inverse requires square matrix")
        n = self.m

        # Augment [A | I]
        aug = [
            [v.as_fraction for v in self.rows[i]] +
            [Fraction(1) if j == i else Fraction(0) for j in range(n)]
            for i in range(n)
        ]

        for col in range(n):
            # Find pivot
            pivot_row = None
            for r in range(col, n):
                if aug[r][col] != 0:
                    pivot_row = r
                    break
            if pivot_row is None:
                raise ValueError("Matrix is singular")
            if pivot_row != col:
                aug[col], aug[pivot_row] = aug[pivot_row], aug[col]

            pivot = aug[col][col]
            # Scale pivot row
            for c in range(2 * n):
                aug[col][c] /= pivot
            # Eliminate
            for r in range(n):
                if r == col or aug[r][col] == 0:
                    continue
                factor = aug[r][col]
                for c in range(2 * n):
                    aug[r][c] -= factor * aug[col][c]

        # Extract right half
        return RatMatrix([
            [SexaRational(aug[i][n + j]) for j in range(n)]
            for i in range(n)
        ])

    def solve(self, b: list[SexaRational | int]) -> list[SexaRational]:
        """Solve Ax = b for x. Exact. Raises ValueError if no unique solution."""
        if not self.is_square:
            raise ValueError("solve requires square matrix")
        if len(b) != self.m:
            raise ValueError("Dimension mismatch")

        b_vec = [v if isinstance(v, SexaRational) else SexaRational(v) for v in b]
        inv = self.inverse()
        result = []
        for i in range(self.m):
            s = SexaRational(0)
            for j in range(self.n):
                s = s + inv.rows[i][j] * b_vec[j]
            result.append(s)
        return result

    def trace(self) -> SexaRational:
        if not self.is_square:
            raise ValueError("Trace requires square matrix")
        s = SexaRational(0)
        for i in range(self.m):
            s = s + self.rows[i][i]
        return s

    def characteristic_polynomial(self) -> RatPoly:
        """Compute det(A - λI) using Faddeev-LeVerrier algorithm.

        Returns polynomial in λ. Exact.
        """
        if not self.is_square:
            raise ValueError("Characteristic polynomial requires square matrix")
        n = self.m

        # Faddeev-LeVerrier: compute coefficients c_0, c_1, ..., c_n
        # where char poly = λ^n + c_{n-1} λ^{n-1} + ... + c_0
        coeffs_rev = [SexaRational(1)]  # c_n = 1 (monic)
        M = RatMatrix.identity(n)

        for k in range(1, n + 1):
            AM = self * M
            tr = AM.trace()
            ck = SexaRational(0) - tr / SexaRational(k)
            coeffs_rev.append(ck)
            if k < n:
                # M = AM + ck * I
                M = AM + RatMatrix.identity(n).scale(ck)

        # coeffs_rev = [1, c_{n-1}, c_{n-2}, ..., c_0]
        # We need [c_0, c_1, ..., c_{n-1}, 1] for RatPoly
        poly_coeffs = list(reversed(coeffs_rev))
        return RatPoly(poly_coeffs)

    def rank(self) -> int:
        """Matrix rank via row echelon form."""
        # Copy
        M = [[v.as_fraction for v in row] for row in self.rows]
        m, n = self.m, self.n
        r = 0
        for col in range(n):
            # Find pivot in column col, starting from row r
            pivot_row = None
            for row in range(r, m):
                if M[row][col] != 0:
                    pivot_row = row
                    break
            if pivot_row is None:
                continue
            M[r], M[pivot_row] = M[pivot_row], M[r]
            pivot = M[r][col]
            for row in range(r + 1, m):
                if M[row][col] == 0:
                    continue
                factor = M[row][col] / pivot
                for c in range(col, n):
                    M[row][c] -= factor * M[r][c]
            r += 1
        return r

    def __repr__(self) -> str:
        rows_str = "; ".join(
            "[" + ", ".join(str(v) for v in row) + "]"
            for row in self.rows
        )
        return f"RatMatrix([{rows_str}])"
