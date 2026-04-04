"""CUNEIFORM CLI — command-line interface.

Usage:
    python -m cuneiform tabulate [--max-regular N] [--format csv|json]
    python -m cuneiform experiment smooth-density [--bits N] [--trials N] [--seed N]
    python -m cuneiform paper [--bit-sizes 32,48] [--smooth-bits 32] [-o paper.tex]
    python -m cuneiform random [sexa|int|smooth|dice|d60] [options]
    python -m cuneiform validate
    python -m cuneiform info
"""

from __future__ import annotations

import argparse
import sys


def cmd_tabulate(args):
    """Generate extended Plimpton 322 table."""
    from cuneiform.experiments.plimpton_tabulate import PlimptonTabulator

    tab = PlimptonTabulator(max_regular=args.max_regular)
    rows = tab.generate()

    if args.format == "csv":
        print(tab.to_csv(rows), end="")
    elif args.format == "json":
        print(tab.to_json(rows))
    else:
        # Text summary
        stats = tab.statistics(rows)
        print(f"Extended Plimpton 322 Table")
        print(f"  max_regular: {stats['max_regular']}")
        print(f"  total rows: {stats['total_rows']}")
        print(f"  original 15 found: {stats['original_rows_found']}")
        print(f"  spread range: {stats['spread_range'][1]} to {stats['spread_range'][0]}")
        print(f"  max diagonal: {stats['max_diagonal']}")
        if not args.quiet:
            print()
            print("First 15 rows:")
            for row in rows[:15]:
                orig = " *" if row.is_original else ""
                print(f"  {row.row_number:4d}. ({row.width}, {row.length}, "
                      f"{row.diagonal}) p={row.p} q={row.q}{orig}")


def cmd_experiment(args):
    """Run experiments."""
    if args.type == "smooth-density":
        from cuneiform.experiments.smooth_density import SmoothDensityExperiment

        exp = SmoothDensityExperiment(
            bits=args.bits,
            trials=args.trials,
            smoothness_bound=args.bound,
            seed=args.seed,
        )
        result = exp.run()

        if args.format == "json":
            print(result.to_json())
        else:
            print(exp.summary(result))
    else:
        print(f"Unknown experiment type: {args.type}", file=sys.stderr)
        sys.exit(1)


def cmd_validate(args):
    """Run self-validation checks."""
    from cuneiform.experiments.validation import SelfValidator

    validator = SelfValidator()
    validator.run_all()
    print(validator.summary())
    if not validator.all_passed:
        sys.exit(1)


def cmd_paper(args):
    """Generate a complete LaTeX paper from experimental data."""
    from cuneiform.experiments.paper_pipeline import PaperPipeline

    bit_sizes = [int(b) for b in args.bit_sizes.split(",")]
    pipeline = PaperPipeline(
        bit_sizes=bit_sizes,
        trials_per_size=args.trials,
        sieve_range=args.sieve_range,
        smooth_bits=args.smooth_bits,
        smooth_trials=args.smooth_trials,
        seed=args.seed,
    )

    results = pipeline.run_all()

    if args.format == "summary":
        print(pipeline.summary(results))
    else:
        latex = pipeline.generate_latex(results)
        if args.output:
            with open(args.output, "w") as f:
                f.write(latex)
            print(f"Paper written to {args.output}", file=sys.stderr)
            print(pipeline.summary(results), file=sys.stderr)
        else:
            print(latex)


def cmd_random(args):
    """Generate random sexagesimal numbers."""
    from cuneiform.random import SexaRandom, SmoothRandom, CuneiformDice

    seed = args.seed
    count = args.count
    fmt = args.format

    def _format_sexa(s):
        if fmt == "cuneiform":
            return s.cuneiform()
        elif fmt == "decimal":
            return str(float(s))
        return str(s)

    sub = args.type

    if sub == "sexa":
        rng = SexaRandom(seed=seed)
        for _ in range(count):
            s = rng.sexa(digits=args.digits)
            print(_format_sexa(s))

    elif sub == "int":
        rng = SexaRandom(seed=seed)
        from cuneiform.core import Sexa
        for _ in range(count):
            val = rng.randint(args.lo, args.hi)
            s = Sexa(val)
            print(_format_sexa(s))

    elif sub == "smooth":
        sr = SmoothRandom(seed=seed, max_exp=args.max_exp)
        for _ in range(count):
            s = sr.regular()
            print(_format_sexa(s))

    elif sub == "dice":
        dice = CuneiformDice(seed=seed)
        result = dice.roll_total(n=args.n, sides=args.sides)
        for r in result["rolls"]:
            if fmt == "cuneiform":
                print(f"  {r['cuneiform']}  ({r['value']})")
            else:
                print(f"  {r['sexa']}")
        from cuneiform.core import Sexa
        total = Sexa(result["total"])
        print(f"Total: {_format_sexa(total)}")

    elif sub == "d60":
        dice = CuneiformDice(seed=seed)
        for _ in range(count):
            r = dice.d60()
            if fmt == "cuneiform":
                print(f"{r['cuneiform']}  ({r['value']})")
            else:
                print(r["sexa"])

    elif sub == "astragalus":
        dice = CuneiformDice(seed=seed)
        for _ in range(count):
            r = dice.astragalus()
            if fmt == "cuneiform":
                print(f"{r['cuneiform']}  ({r['value']})")
            else:
                print(r["sexa"])

    else:
        # Default: generate a sexa value
        rng = SexaRandom(seed=seed)
        for _ in range(count):
            s = rng.sexa(digits=4)
            print(_format_sexa(s))


def cmd_info(args):
    """Show library info."""
    from cuneiform import __version__

    print(f"CUNEIFORM v{__version__}")
    print(f"Sexagesimal Rational Mathematics Library")
    print()
    print("Modules:")
    modules = [
        ("core", "Sexa, SexaRational, SmoothNumber"),
        ("tablet", "Plimpton 322 (15 rows + extension)"),
        ("geometry", "RatPoint, Quadrance, Spread, 5 rational trig laws"),
        ("number_theory", "Regularity, QS sieve, ECM, analysis"),
        ("crypto", "RSA, lattice, elliptic, post-quantum analysis"),
        ("publication", "LaTeX paper generator, figures, tables"),
        ("cas", "RatPoly, RatMatrix, algebraic calculus, Z[1/60]"),
        ("quantum", "Shor simulation, Grover oracle analysis"),
        ("archaeology", "Tablet analyzer, corpus of known tablets"),
        ("random", "Sexagesimal RNG, smooth random, cuneiform dice"),
        ("experiments", "Smooth density, Plimpton tabulator, benchmarks"),
    ]
    for name, desc in modules:
        print(f"  {name:16s} {desc}")


def main():
    parser = argparse.ArgumentParser(
        prog="cuneiform",
        description="CUNEIFORM — Sexagesimal Rational Mathematics Library",
    )
    subparsers = parser.add_subparsers(dest="command")

    # tabulate
    p_tab = subparsers.add_parser("tabulate", help="Generate extended Plimpton table")
    p_tab.add_argument("--max-regular", type=int, default=1000,
                       help="Maximum regular number for p,q (default: 1000)")
    p_tab.add_argument("--format", choices=["text", "csv", "json"], default="text",
                       help="Output format (default: text)")
    p_tab.add_argument("--quiet", "-q", action="store_true",
                       help="Suppress row listing in text mode")

    # experiment
    p_exp = subparsers.add_parser("experiment", help="Run experiments")
    p_exp.add_argument("type", choices=["smooth-density"],
                       help="Experiment type")
    p_exp.add_argument("--bits", type=int, default=64,
                       help="Bit size for numbers (default: 64)")
    p_exp.add_argument("--trials", type=int, default=100,
                       help="Number of trials (default: 100)")
    p_exp.add_argument("--bound", type=int, default=1000,
                       help="Smoothness bound (default: 1000)")
    p_exp.add_argument("--seed", type=int, default=None,
                       help="Random seed for reproducibility")
    p_exp.add_argument("--format", choices=["text", "json"], default="text",
                       help="Output format (default: text)")

    # paper
    p_paper = subparsers.add_parser("paper", help="Generate LaTeX paper from experiments")
    p_paper.add_argument("--bit-sizes", default="32,48",
                         help="Comma-separated bit sizes for scaling (default: 32,48)")
    p_paper.add_argument("--trials", type=int, default=3,
                         help="Semiprimes per bit size (default: 3)")
    p_paper.add_argument("--sieve-range", type=int, default=1000,
                         help="Sieve window width (default: 1000)")
    p_paper.add_argument("--smooth-bits", type=int, default=32,
                         help="Bit size for smooth density experiment (default: 32)")
    p_paper.add_argument("--smooth-trials", type=int, default=50,
                         help="Trials for smooth density (default: 50)")
    p_paper.add_argument("--seed", type=int, default=42,
                         help="Random seed (default: 42)")
    p_paper.add_argument("--format", choices=["latex", "summary"], default="latex",
                         help="Output format (default: latex)")
    p_paper.add_argument("-o", "--output", type=str, default=None,
                         help="Write LaTeX to file instead of stdout")

    # random
    p_rand = subparsers.add_parser("random", help="Generate random sexagesimal numbers")
    p_rand.add_argument("type", nargs="?", default="sexa",
                        choices=["sexa", "int", "smooth", "dice", "d60", "astragalus"],
                        help="Generator type (default: sexa)")
    p_rand.add_argument("--count", "-c", type=int, default=1,
                        help="How many values to generate (default: 1)")
    p_rand.add_argument("--seed", "-s", type=int, default=None,
                        help="Random seed for reproducibility")
    p_rand.add_argument("--format", "-f",
                        choices=["text", "cuneiform", "decimal"], default="text",
                        help="Output format (default: text)")
    p_rand.add_argument("--digits", type=int, default=4,
                        help="Fractional sexagesimal digits for sexa mode (default: 4)")
    p_rand.add_argument("--lo", type=int, default=1,
                        help="Lower bound for int mode (default: 1)")
    p_rand.add_argument("--hi", type=int, default=3600,
                        help="Upper bound for int mode (default: 3600 = 1,0,0)")
    p_rand.add_argument("--max-exp", type=int, default=6,
                        help="Max exponent for smooth mode (default: 6)")
    p_rand.add_argument("--n", type=int, default=3,
                        help="Number of dice to roll in dice mode (default: 3)")
    p_rand.add_argument("--sides", type=int, default=6,
                        help="Sides per die in dice mode (default: 6)")

    # validate
    subparsers.add_parser("validate", help="Run self-validation checks")

    # info
    subparsers.add_parser("info", help="Show library information")

    args = parser.parse_args()

    if args.command == "tabulate":
        cmd_tabulate(args)
    elif args.command == "experiment":
        cmd_experiment(args)
    elif args.command == "paper":
        cmd_paper(args)
    elif args.command == "random":
        cmd_random(args)
    elif args.command == "validate":
        cmd_validate(args)
    elif args.command == "info":
        cmd_info(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
