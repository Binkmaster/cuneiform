"""Tests for the geometry layer: rational trigonometry."""

import pytest
from fractions import Fraction

from cuneiform.core.rational import SexaRational
from cuneiform.geometry.point import RatPoint
from cuneiform.geometry.line import RatLine, GeometryError
from cuneiform.geometry.quadrance import Quadrance
from cuneiform.geometry.spread import Spread
from cuneiform.geometry.triangle import RatTriangle
from cuneiform.geometry import laws, constructions
from cuneiform.tablet.plimpton322 import Plimpton322


# ============================================================
# RatPoint tests
# ============================================================

class TestRatPoint:
    def test_creation(self):
        p = RatPoint(SexaRational(3), SexaRational(4))
        assert p.x == SexaRational(3)
        assert p.y == SexaRational(4)

    def test_creation_from_int(self):
        p = RatPoint(3, 4)
        assert p.x == SexaRational(3)

    def test_equality(self):
        assert RatPoint(1, 2) == RatPoint(1, 2)
        assert RatPoint(1, 2) != RatPoint(1, 3)

    def test_collinear_true(self):
        a = RatPoint(0, 0)
        b = RatPoint(1, 1)
        c = RatPoint(2, 2)
        assert a.collinear(b, c)

    def test_collinear_false(self):
        a = RatPoint(0, 0)
        b = RatPoint(1, 0)
        c = RatPoint(0, 1)
        assert not a.collinear(b, c)

    def test_collinear_horizontal(self):
        a = RatPoint(0, 5)
        b = RatPoint(3, 5)
        c = RatPoint(7, 5)
        assert a.collinear(b, c)

    def test_midpoint(self):
        a = RatPoint(0, 0)
        b = RatPoint(4, 6)
        m = a.midpoint(b)
        assert m == RatPoint(2, 3)

    def test_midpoint_rational(self):
        a = RatPoint(SexaRational(1, 3), SexaRational(0))
        b = RatPoint(SexaRational(2, 3), SexaRational(1))
        m = a.midpoint(b)
        assert m.x == SexaRational(1, 2)
        assert m.y == SexaRational(1, 2)


# ============================================================
# RatLine tests
# ============================================================

class TestRatLine:
    def test_through_points(self):
        l = RatLine.through_points(RatPoint(0, 0), RatPoint(1, 1))
        assert l.contains(RatPoint(2, 2))
        assert l.contains(RatPoint(0, 0))
        assert not l.contains(RatPoint(1, 0))

    def test_through_same_point_raises(self):
        with pytest.raises(GeometryError):
            RatLine.through_points(RatPoint(1, 1), RatPoint(1, 1))

    def test_intersection(self):
        # x-axis (y=0) and y-axis (x=0)
        x_axis = RatLine(0, 1, 0)  # y = 0
        y_axis = RatLine(1, 0, 0)  # x = 0
        p = x_axis.intersection(y_axis)
        assert p == RatPoint(0, 0)

    def test_intersection_general(self):
        # y = x (x - y = 0) and y = -x + 2 (x + y - 2 = 0)
        l1 = RatLine(1, -1, 0)
        l2 = RatLine(1, 1, -2)
        p = l1.intersection(l2)
        assert p == RatPoint(1, 1)

    def test_parallel_raises_on_intersection(self):
        l1 = RatLine(1, 0, 0)   # x = 0
        l2 = RatLine(1, 0, -1)  # x = 1
        with pytest.raises(GeometryError):
            l1.intersection(l2)

    def test_is_parallel(self):
        l1 = RatLine(1, 1, 0)
        l2 = RatLine(2, 2, -5)
        assert l1.is_parallel(l2)

    def test_not_parallel(self):
        l1 = RatLine(1, 0, 0)
        l2 = RatLine(0, 1, 0)
        assert not l1.is_parallel(l2)

    def test_is_perpendicular(self):
        l1 = RatLine(1, 0, 0)   # vertical: x = 0
        l2 = RatLine(0, 1, 0)   # horizontal: y = 0
        assert l1.is_perpendicular(l2)

    def test_perpendicular_diagonal(self):
        l1 = RatLine(1, -1, 0)   # y = x
        l2 = RatLine(1, 1, 0)    # y = -x
        assert l1.is_perpendicular(l2)

    def test_with_slope_through(self):
        p = RatPoint(1, 2)
        l = RatLine.with_slope_through(SexaRational(3), p)
        assert l.contains(p)
        # slope 3: y - 2 = 3(x - 1) => y = 3x - 1 => at x=0, y=-1
        assert l.contains(RatPoint(0, -1))

    def test_line_equality(self):
        l1 = RatLine(1, -1, 0)    # x - y = 0
        l2 = RatLine(2, -2, 0)    # 2x - 2y = 0 (same line)
        assert l1 == l2


# ============================================================
# Quadrance tests
# ============================================================

class TestQuadrance:
    def test_between_origin_and_point(self):
        Q = Quadrance.between(RatPoint(0, 0), RatPoint(3, 4))
        assert Q.value == SexaRational(25)

    def test_zero_distance(self):
        Q = Quadrance.between(RatPoint(5, 7), RatPoint(5, 7))
        assert Q.is_zero()

    def test_addition(self):
        Q1 = Quadrance(SexaRational(9))
        Q2 = Quadrance(SexaRational(16))
        assert (Q1 + Q2).value == SexaRational(25)

    def test_subtraction(self):
        Q1 = Quadrance(SexaRational(25))
        Q2 = Quadrance(SexaRational(16))
        assert (Q1 - Q2).value == SexaRational(9)

    def test_comparison(self):
        assert Quadrance(SexaRational(9)) < Quadrance(SexaRational(16))

    def test_pythagorean_triple(self):
        """Q(0→3) + Q(0→4) = Q(0→5) for (3,4,5) right triangle."""
        A = RatPoint(0, 0)
        B = RatPoint(4, 0)
        C = RatPoint(0, 3)
        Q_ab = Quadrance.between(A, B)
        Q_ac = Quadrance.between(A, C)
        Q_bc = Quadrance.between(B, C)
        assert Q_ab.value == SexaRational(16)
        assert Q_ac.value == SexaRational(9)
        assert Q_bc.value == SexaRational(25)
        assert (Q_ab + Q_ac) == Q_bc

    def test_rational_coordinates(self):
        """Quadrance between rational points is rational."""
        p1 = RatPoint(SexaRational(1, 3), SexaRational(1, 4))
        p2 = RatPoint(SexaRational(2, 3), SexaRational(3, 4))
        Q = Quadrance.between(p1, p2)
        assert Q.value == SexaRational(1, 9) + SexaRational(1, 4)
        assert Q.value == SexaRational(13, 36)


# ============================================================
# Spread tests
# ============================================================

class TestSpread:
    def test_perpendicular_lines(self):
        l1 = RatLine(1, 0, 0)   # x = 0 (vertical)
        l2 = RatLine(0, 1, 0)   # y = 0 (horizontal)
        s = Spread.between_lines(l1, l2)
        assert s.is_right()
        assert s.value == SexaRational(1)

    def test_parallel_lines(self):
        l1 = RatLine(1, 1, 0)
        l2 = RatLine(1, 1, -5)
        s = Spread.between_lines(l1, l2)
        assert s.is_parallel()
        assert s.value == SexaRational(0)

    def test_45_degree_spread(self):
        """y=x vs x-axis should have spread 1/2."""
        l1 = RatLine(0, 1, 0)    # y = 0 (x-axis)
        l2 = RatLine(1, -1, 0)   # x - y = 0 (y=x)
        s = Spread.between_lines(l1, l2)
        assert s.value == SexaRational(1, 2)

    def test_same_line_spread_zero(self):
        l = RatLine(3, 4, -7)
        s = Spread.between_lines(l, l)
        assert s.is_parallel()

    def test_from_pythagorean_triple(self):
        # (3,4,5): spread opposite side 3 = 9/25
        s = Spread.from_pythagorean_triple(3, 4, 5)
        assert s.value == SexaRational(9, 25)

        # (3,4,5): spread opposite side 4 = 16/25
        s = Spread.from_pythagorean_triple(4, 3, 5)
        assert s.value == SexaRational(16, 25)

    def test_from_sides(self):
        """Compute spread from three quadrances of (3,4,5) triangle."""
        Qa = Quadrance(SexaRational(9))    # side a=3
        Qb = Quadrance(SexaRational(16))   # side b=4
        Qc = Quadrance(SexaRational(25))   # side c=5

        # Spread opposite Qa (side 3) using adj sides Qb, Qc
        s = Spread.from_sides(Qa, Qb, Qc)
        assert s.value == SexaRational(9, 25)

        # Spread opposite Qc (hypotenuse) = 1 (right angle)
        s_right = Spread.from_sides(Qc, Qa, Qb)
        assert s_right.is_right()

    def test_classical_angle_approx(self):
        s = Spread(SexaRational(1, 2))  # 45 degrees
        angle = s.classical_angle_approx()
        assert abs(angle - 45.0) < 0.01


# ============================================================
# Five Laws tests
# ============================================================

class TestFiveLaws:
    """Test all five laws against known triangles."""

    def _345_triangle(self):
        """(3,4,5) right triangle."""
        Qa = Quadrance(SexaRational(9))
        Qb = Quadrance(SexaRational(16))
        Qc = Quadrance(SexaRational(25))
        sa = Spread(SexaRational(9, 25))
        sb = Spread(SexaRational(16, 25))
        sc = Spread(SexaRational(1))
        return Qa, Qb, Qc, sa, sb, sc

    def test_pythagoras_345(self):
        Qa, Qb, Qc, sa, sb, sc = self._345_triangle()
        assert laws.verify_pythagoras(Qa, Qb, Qc, sc)

    def test_spread_law_345(self):
        Qa, Qb, Qc, sa, sb, sc = self._345_triangle()
        assert laws.verify_spread_law(sa, Qa, sb, Qb)
        assert laws.verify_spread_law(sa, Qa, sc, Qc)

    def test_cross_law_345(self):
        Qa, Qb, Qc, sa, sb, sc = self._345_triangle()
        assert laws.verify_cross_law(Qb, Qc, Qa, sa)
        assert laws.verify_cross_law(Qa, Qc, Qb, sb)
        assert laws.verify_cross_law(Qa, Qb, Qc, sc)

    def test_triple_spread_345(self):
        Qa, Qb, Qc, sa, sb, sc = self._345_triangle()
        assert laws.verify_triple_spread(sa, sb, sc)

    def test_triple_quad_collinear(self):
        """Collinear points should satisfy triple quad formula."""
        A = RatPoint(0, 0)
        B = RatPoint(1, 1)
        C = RatPoint(3, 3)
        Q1 = Quadrance.between(B, C)  # 8
        Q2 = Quadrance.between(A, C)  # 18
        Q3 = Quadrance.between(A, B)  # 2
        assert laws.verify_triple_quad(Q1, Q2, Q3)

    def test_triple_quad_not_collinear(self):
        A = RatPoint(0, 0)
        B = RatPoint(1, 0)
        C = RatPoint(0, 1)
        Q1 = Quadrance.between(B, C)
        Q2 = Quadrance.between(A, C)
        Q3 = Quadrance.between(A, B)
        assert not laws.verify_triple_quad(Q1, Q2, Q3)

    def test_equilateral_triple_spread(self):
        """Equilateral triangle: all spreads = 3/4.

        Points: (0,0), (2,0), (1, sqrt(3)) -- but sqrt(3) is irrational!
        Use the known spread value directly.
        """
        s = Spread(SexaRational(3, 4))
        assert laws.verify_triple_spread(s, s, s)

    def test_5_12_13_triangle(self):
        Qa = Quadrance(SexaRational(25))
        Qb = Quadrance(SexaRational(144))
        Qc = Quadrance(SexaRational(169))
        sc = laws.solve_cross_law_for_spread(Qa, Qb, Qc)
        assert sc.is_right()  # (5,12,13) is a right triangle
        assert laws.verify_cross_law(Qa, Qb, Qc, sc)

    def test_solve_spread_law(self):
        s1 = Spread(SexaRational(9, 25))  # from (3,4,5)
        Q1 = Quadrance(SexaRational(9))
        Q2 = Quadrance(SexaRational(16))
        s2 = laws.solve_spread_law(s1, Q1, Q2)
        assert s2.value == SexaRational(16, 25)

    def test_solve_cross_law_for_quadrance(self):
        """Given Q1=9, Q2=16, s3=1 (right angle), solve for Q3."""
        Q1 = Quadrance(SexaRational(9))
        Q2 = Quadrance(SexaRational(16))
        s3 = Spread(SexaRational(1))
        solutions = laws.solve_cross_law_for_quadrance(Q1, Q2, s3)
        values = [q.value for q in solutions]
        assert SexaRational(25) in values

    def test_solve_triple_spread(self):
        """Given two spreads of (3,4,5), find third."""
        s1 = Spread(SexaRational(9, 25))
        s2 = Spread(SexaRational(16, 25))
        solutions = laws.solve_triple_spread(s1, s2)
        values = [s.value for s in solutions]
        assert SexaRational(1) in values


# ============================================================
# Plimpton 322 + Laws integration
# ============================================================

class TestPlimptonLaws:
    """Verify all 5 laws hold for every row of Plimpton 322."""

    @pytest.fixture
    def plimpton_rows(self):
        return Plimpton322().original()

    def test_cross_law_all_rows(self, plimpton_rows):
        for row in plimpton_rows:
            w, l, d = row.width, row.length, row.diagonal
            Qa = Quadrance(SexaRational(w * w))
            Qb = Quadrance(SexaRational(l * l))
            Qc = Quadrance(SexaRational(d * d))
            # Spread at vertex opposite Qc (the hypotenuse) should be 1
            sc = laws.solve_cross_law_for_spread(Qa, Qb, Qc)
            assert sc.is_right(), f"Row {row.row_number}: not right angle"
            assert laws.verify_cross_law(Qa, Qb, Qc, sc), \
                f"Row {row.row_number}: cross law fails"

    def test_spread_law_all_rows(self, plimpton_rows):
        for row in plimpton_rows:
            w, l, d = row.width, row.length, row.diagonal
            Qa = Quadrance(SexaRational(w * w))
            Qb = Quadrance(SexaRational(l * l))
            Qc = Quadrance(SexaRational(d * d))
            sa = Spread(SexaRational(w * w, d * d))
            sb = Spread(SexaRational(l * l, d * d))
            assert laws.verify_spread_law(sa, Qa, sb, Qb), \
                f"Row {row.row_number}: spread law fails"

    def test_triple_spread_all_rows(self, plimpton_rows):
        for row in plimpton_rows:
            w, l, d = row.width, row.length, row.diagonal
            sa = Spread(SexaRational(w * w, d * d))
            sb = Spread(SexaRational(l * l, d * d))
            sc = Spread(SexaRational(1))  # right angle
            assert laws.verify_triple_spread(sa, sb, sc), \
                f"Row {row.row_number}: triple spread fails"

    def test_pythagoras_all_rows(self, plimpton_rows):
        for row in plimpton_rows:
            w, l, d = row.width, row.length, row.diagonal
            Qa = Quadrance(SexaRational(w * w))
            Qb = Quadrance(SexaRational(l * l))
            Qc = Quadrance(SexaRational(d * d))
            sc = Spread(SexaRational(1))
            assert laws.verify_pythagoras(Qa, Qb, Qc, sc), \
                f"Row {row.row_number}: pythagoras fails"


# ============================================================
# RatTriangle tests
# ============================================================

class TestRatTriangle:
    def test_345_triangle(self):
        t = RatTriangle.from_triple(3, 4, 5)
        assert t.is_right()
        assert t.right_vertex() == "A"  # right angle at origin

    def test_345_quadrances(self):
        t = RatTriangle.from_triple(3, 4, 5)
        # Q_a = between B,C = Q((4,0),(0,3))= 16+9 = 25
        assert t.Q_a.value == SexaRational(25)
        # Q_b = between A,C = Q((0,0),(0,3)) = 9
        assert t.Q_b.value == SexaRational(9)
        # Q_c = between A,B = Q((0,0),(4,0)) = 16
        assert t.Q_c.value == SexaRational(16)

    def test_345_spreads(self):
        t = RatTriangle.from_triple(3, 4, 5)
        assert t.s_A.is_right()  # right angle at A
        assert t.s_B.value == SexaRational(9, 25)
        assert t.s_C.value == SexaRational(16, 25)

    def test_verify_all_laws(self):
        t = RatTriangle.from_triple(3, 4, 5)
        results = t.verify_all_laws()
        for name, ok in results.items():
            assert ok, f"Law {name} failed for (3,4,5)"

    def test_5_12_13(self):
        t = RatTriangle.from_triple(5, 12, 13)
        assert t.is_right()
        results = t.verify_all_laws()
        for name, ok in results.items():
            assert ok, f"Law {name} failed for (5,12,13)"

    def test_119_120_169(self):
        """Plimpton 322 row 1."""
        t = RatTriangle.from_triple(119, 120, 169)
        assert t.is_right()
        results = t.verify_all_laws()
        for name, ok in results.items():
            assert ok, f"Law {name} failed for (119,120,169)"

    def test_collinear_raises(self):
        with pytest.raises(GeometryError):
            RatTriangle(RatPoint(0, 0), RatPoint(1, 1), RatPoint(2, 2))

    def test_non_pythagorean_raises(self):
        with pytest.raises(GeometryError):
            RatTriangle.from_triple(3, 4, 6)

    def test_from_plimpton_row(self):
        rows = Plimpton322().original()
        for row in rows:
            t = RatTriangle.from_plimpton_row(row)
            assert t.is_right()
            results = t.verify_all_laws()
            for name, ok in results.items():
                assert ok, f"Row {row.row_number}: law {name} failed"

    def test_area_quadrance_345(self):
        t = RatTriangle.from_triple(3, 4, 5)
        # Area = (1/2)(3)(4) = 6, so 16*A^2 = 16*36 = 576
        assert t.area_quadrance_16() == SexaRational(576)

    def test_solve_QQQ(self):
        Q1 = Quadrance(SexaRational(9))
        Q2 = Quadrance(SexaRational(16))
        Q3 = Quadrance(SexaRational(25))
        s1, s2, s3 = RatTriangle.solve_QQQ(Q1, Q2, Q3)
        assert s3.is_right()
        assert s1.value == SexaRational(9, 25)
        assert s2.value == SexaRational(16, 25)

    def test_solve_QSQ(self):
        Q1 = Quadrance(SexaRational(9))
        Q2 = Quadrance(SexaRational(16))
        s3 = Spread(SexaRational(1))  # right angle between them
        Q3, s1, s2 = RatTriangle.solve_QSQ(Q1, s3, Q2)
        assert Q3.value == SexaRational(25)

    def test_non_right_triangle(self):
        """A non-right triangle: (0,0), (4,0), (2,3)."""
        t = RatTriangle(RatPoint(0, 0), RatPoint(4, 0), RatPoint(2, 3))
        assert not t.is_right()
        results = t.verify_all_laws()
        for name, ok in results.items():
            assert ok, f"Law {name} failed for non-right triangle"


# ============================================================
# Constructions tests
# ============================================================

class TestConstructions:
    def test_perpendicular_through(self):
        # Perpendicular to x-axis through (3,5) should be vertical at x=3
        x_axis = RatLine(0, 1, 0)
        perp = constructions.perpendicular_through(x_axis, RatPoint(3, 5))
        assert perp.is_perpendicular(x_axis)
        assert perp.contains(RatPoint(3, 5))
        assert perp.contains(RatPoint(3, 0))

    def test_parallel_through(self):
        x_axis = RatLine(0, 1, 0)
        par = constructions.parallel_through(x_axis, RatPoint(0, 5))
        assert par.is_parallel(x_axis)
        assert par.contains(RatPoint(0, 5))
        assert par.contains(RatPoint(99, 5))

    def test_foot_of_perpendicular(self):
        x_axis = RatLine(0, 1, 0)
        foot = constructions.foot_of_perpendicular(x_axis, RatPoint(3, 7))
        assert foot == RatPoint(3, 0)

    def test_foot_of_perpendicular_diagonal(self):
        # Line y = x (x - y = 0), point (2, 0)
        line = RatLine(1, -1, 0)
        foot = constructions.foot_of_perpendicular(line, RatPoint(2, 0))
        assert foot == RatPoint(1, 1)

    def test_midpoint(self):
        m = constructions.midpoint(RatPoint(0, 0), RatPoint(4, 6))
        assert m == RatPoint(2, 3)

    def test_perpendicular_bisector(self):
        pb = constructions.perpendicular_bisector(RatPoint(0, 0), RatPoint(4, 0))
        # Should pass through (2, 0) and be vertical (perpendicular to x-axis)
        assert pb.contains(RatPoint(2, 0))
        assert pb.contains(RatPoint(2, 99))

    def test_circumcenter_right_triangle(self):
        """Circumcenter of right triangle is midpoint of hypotenuse."""
        A = RatPoint(0, 0)
        B = RatPoint(4, 0)
        C = RatPoint(0, 3)
        O = constructions.circumcenter(A, B, C)
        # Midpoint of hypotenuse BC
        assert O == RatPoint(2, SexaRational(3, 2))

    def test_circumcenter_equidistant(self):
        """Circumcenter is equidistant from all three vertices."""
        A = RatPoint(0, 0)
        B = RatPoint(6, 0)
        C = RatPoint(2, 4)
        O = constructions.circumcenter(A, B, C)
        Q_OA = Quadrance.between(O, A)
        Q_OB = Quadrance.between(O, B)
        Q_OC = Quadrance.between(O, C)
        assert Q_OA == Q_OB
        assert Q_OB == Q_OC

    def test_circumquadrance(self):
        A = RatPoint(0, 0)
        B = RatPoint(4, 0)
        C = RatPoint(0, 3)
        CQ = constructions.circumquadrance(A, B, C)
        # For (3,4,5) right triangle, circumradius = hypotenuse/2 = 5/2
        # circumquadrance = (5/2)^2 = 25/4
        assert CQ.value == SexaRational(25, 4)

    def test_reflect_point(self):
        # Reflect (3, 0) across x-axis -> (3, 0) (already on axis)
        x_axis = RatLine(0, 1, 0)
        r = constructions.reflect_point(RatPoint(3, 5), x_axis)
        assert r == RatPoint(3, -5)

    def test_reflect_point_diagonal(self):
        # Reflect (2, 0) across y=x -> (0, 2)
        line = RatLine(1, -1, 0)
        r = constructions.reflect_point(RatPoint(2, 0), line)
        assert r == RatPoint(0, 2)

    def test_orthocenter_right_triangle(self):
        """Orthocenter of right triangle is at the right-angle vertex."""
        A = RatPoint(0, 0)
        B = RatPoint(4, 0)
        C = RatPoint(0, 3)
        H = constructions.orthocenter(A, B, C)
        assert H == A  # right angle at A

    def test_centroid(self):
        A = RatPoint(0, 0)
        B = RatPoint(6, 0)
        C = RatPoint(0, 9)
        G = constructions.centroid(A, B, C)
        assert G == RatPoint(2, 3)

    def test_altitude_foot(self):
        A = RatPoint(0, 3)
        B = RatPoint(0, 0)
        C = RatPoint(4, 0)
        foot = constructions.altitude_foot(A, B, C)
        assert foot == RatPoint(0, 0)  # altitude from A to BC lands at B

    def test_quadrance_to_line(self):
        # Distance from (3, 4) to x-axis (y=0) = 4, quadrance = 16
        x_axis = RatLine(0, 1, 0)
        Q = constructions.quadrance_to_line(RatPoint(3, 4), x_axis)
        assert Q.value == SexaRational(16)

    def test_quadrance_to_line_general(self):
        # Distance from origin to x + y - 2 = 0: |0+0-2|/sqrt(2) = sqrt(2)
        # Quadrance = 2
        line = RatLine(1, 1, -2)
        Q = constructions.quadrance_to_line(RatPoint(0, 0), line)
        assert Q.value == SexaRational(2)
