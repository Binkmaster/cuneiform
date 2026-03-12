"""Cuneiform-style display & notation utilities."""

from __future__ import annotations

from .sexagesimal import Sexa, _digit_to_cuneiform


def format_table_row(label: str, sexa: Sexa, show_cuneiform: bool = True) -> str:
    """Format a single value for table display."""
    parts = [f"{label:>12}: {sexa!r:>20}"]
    if show_cuneiform:
        parts.append(f"  {sexa.cuneiform()}")
    return "".join(parts)


def format_fraction_comparison(num: int, den: int) -> str:
    """Show a fraction in decimal, sexagesimal, and regularity info."""
    from .rational import SexaRational
    from .smooth import is_smooth

    sr = SexaRational(num, den)
    sexa = Sexa.from_fraction(num, den) if is_smooth(den) else None

    lines = [f"  Fraction:   {num}/{den}"]
    lines.append(f"  Decimal:    {float(sr):.10f}")
    if sexa is not None:
        lines.append(f"  Base-60:    {sexa!r} (EXACT)")
        lines.append(f"  Cuneiform:  {sexa.cuneiform()}")
        lines.append(f"  Regular:    YES (terminates in base 60)")
    else:
        lines.append(f"  Base-60:    non-terminating (IRREGULAR)")
        lines.append(f"  Regular:    NO ({den} has prime factors > 5)")
        lines.append(f"  Regularity: class {sr.regularity_class}")
    return "\n".join(lines)
