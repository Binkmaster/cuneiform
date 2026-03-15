#!/usr/bin/env python3
"""Interactive semiprime factoring tool.

Presents a menu of all available factoring techniques from the techniques/
library, lets you pick one, set parameters, enter a semiprime, and attack.

Usage:
    python factor.py
    python factor.py 1522605027922533360535618378132637429718068114961380688657908494580122963258952897654000350692006139
"""

import sys
import time
import inspect
import signal
import logging

logging.basicConfig(
    level=logging.INFO,
    format="  %(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("factor")

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from cuneiform.core.accel import HAS_GMPY2

# Technique registry: (name, module, description)
TECHNIQUES = []

def _load_techniques():
    """Load all technique modules and build the registry."""
    from techniques import (
        trial_division, fermat, squfof, hart_lehman,
        pollard_rho, pollard_pm1, williams_pp1,
        dixon, cfrac, rational_sieve, quadratic_sieve, mpqs, siqs,
        ecm,
        wiener, boneh_durfee, coppersmith, batch_gcd,
        reciprocal_pairs, gcd_bombardment, random_congruences,
        claude_resonance, claude_fractal, claude_quantum,
        claude_sexagesimal_cfrac, claude_regularity_sieve, claude_babylon_gcd,
        claude_polar, claude_gaussian,
    )

    techniques = [
        ("Classical", [
            (trial_division,    "Trial Division",              "Divide by primes up to a bound"),
            (fermat,            "Fermat's Method",             "Difference of squares (close factors)"),
            (squfof,            "SQUFOF",                      "Square form factorization (<60 digits)"),
            (hart_lehman,       "Hart / Lehman",               "One-line + O(n^1/3) deterministic"),
        ]),
        ("Group-Order", [
            (pollard_rho,       "Pollard's Rho",               "Birthday paradox (Brent's improvement)"),
            (pollard_pm1,       "Pollard p-1",                 "Exploits smooth p-1"),
            (williams_pp1,      "Williams p+1",                "Exploits smooth p+1 (Lucas sequences)"),
        ]),
        ("Sieve-Based", [
            (dixon,             "Dixon's Method",              "Random squares (foundational sieve)"),
            (cfrac,             "CFRAC",                       "Continued fraction factoring"),
            (rational_sieve,    "Rational Sieve",              "Historical predecessor to NFS"),
            (quadratic_sieve,   "Quadratic Sieve",             "Standard/Sexagesimal QS"),
            (mpqs,              "MPQS",                        "Multiple Polynomial Quadratic Sieve"),
            (siqs,              "SIQS",                        "Self-Initializing QS (fastest QS)"),
        ]),
        ("Elliptic Curve", [
            (ecm,               "ECM",                         "Standard + Plimpton-322 curves"),
        ]),
        ("RSA Structural", [
            (wiener,            "Wiener Attack",               "CF attack on small d"),
            (boneh_durfee,      "Boneh-Durfee",                "Extended Wiener (d < N^0.292)"),
            (coppersmith,       "Coppersmith",                 "Small roots (partial factor knowledge)"),
            (batch_gcd,         "Batch GCD",                   "Shared prime detection"),
        ]),
        ("Cuneiform-Specific", [
            (reciprocal_pairs,  "Reciprocal Pairs",            "Babylonian reciprocal pair analysis"),
            (gcd_bombardment,   "GCD Bombardment",             "Heuristic GCD with special sequences"),
            (random_congruences,"Random Congruences",           "Random square-root witnesses"),
        ]),
        ("Novel (Claude Originals)", [
            (claude_resonance,  "Claude Resonance",            "Multi-discriminant Lucas cascade"),
            (claude_fractal,    "Claude Fractal",              "Multi-walk ergodic collisions"),
            (claude_quantum,    "Claude Quantum",              "Classical FFT period detection"),
        ]),
        ("Novel (Claude × Cuneiform)", [
            (claude_sexagesimal_cfrac,  "Claude Sexa-CFRAC",   "Sexagesimal CF with 5-smooth quotients"),
            (claude_regularity_sieve,   "Claude Reg-Sieve",    "Regularity-guided QS + partial relations"),
            (claude_babylon_gcd,        "Claude Babylon-GCD",  "5-smooth exponent cascade ({2,3,5} only)"),
        ]),
        ("Novel (Claude × Gaussian/Polar)", [
            (claude_gaussian,           "Claude Gaussian",     "Gaussian integers via Plimpton-322"),
            (claude_polar,              "Claude Polar",        "Gaussian Pollard rho in ℤ[i]/(N)"),
        ]),
    ]

    idx = 1
    for category, items in techniques:
        for mod, title, desc in items:
            TECHNIQUES.append((idx, mod, title, desc, category))
            idx += 1


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║     𒀭  CUNEIFORM FACTOR — Interactive Semiprime Cracker  𒀭        ║
║          29 techniques • gmpy2 accelerated • base-60 math          ║
╚══════════════════════════════════════════════════════════════════════╝""")
    accel = "gmpy2/GMP" if HAS_GMPY2 else "stdlib (install gmpy2 for 5-50x speedup)"
    print(f"  Acceleration: {accel}\n")


def print_menu():
    current_cat = None
    for idx, mod, title, desc, category in TECHNIQUES:
        if category != current_cat:
            current_cat = category
            print(f"\n  ── {category} ──")
        print(f"    [{idx:2d}] {title:25s} {desc}")
    print(f"\n    [ 0] Run ALL techniques sequentially")
    print(f"    [ q] Quit\n")


def get_params(mod):
    """Inspect the factor function and prompt for non-default parameters."""
    sig = inspect.signature(mod.factor)
    params = {}

    for name, param in sig.parameters.items():
        if name in ('n', 'kwargs'):
            continue

        default = param.default
        if default is inspect.Parameter.empty:
            # Required parameter
            val = input(f"    {name} (required): ").strip()
            if not val:
                print(f"    Skipping (required param missing — using technique default)")
                continue
            params[name] = _parse_value(val)
        else:
            if default is None:
                hint = "auto"
            else:
                hint = str(default)
            val = input(f"    {name} [{hint}]: ").strip()
            if val:
                params[name] = _parse_value(val)

    return params


def _parse_value(val):
    """Parse user input to int, float, bool, or string."""
    if val.lower() in ('true', 'yes'):
        return True
    if val.lower() in ('false', 'no'):
        return False
    try:
        return int(val)
    except ValueError:
        pass
    try:
        return float(val)
    except ValueError:
        pass
    return val


def get_semiprime(argv_n=None):
    """Get the semiprime from user or command line."""
    if argv_n:
        return int(argv_n)

    while True:
        val = input("  Enter semiprime N: ").strip()
        if not val:
            continue
        try:
            n = int(val)
            if n < 4:
                print("    N must be >= 4")
                continue
            return n
        except ValueError:
            print("    Invalid number, try again")


class _Timeout(Exception):
    """Raised when a technique exceeds its time limit."""


def _timeout_handler(signum, frame):
    raise _Timeout()


def run_technique(mod, title, n, params, *, timeout=None):
    """Run a single technique and report results.

    Parameters
    ----------
    timeout : int | None
        Maximum seconds to allow.  ``None`` means no limit.
    """
    mod_name = mod.__name__.split('.')[-1]
    print(f"\n{'─'*70}")
    print(f"  Running: {title} ({mod_name})")
    print(f"  Target:  {n}")
    print(f"           {n.bit_length()} bits, {len(str(n))} digits")
    if params:
        print(f"  Params:  {params}")
    if timeout:
        print(f"  Timeout: {timeout}s")
    print(f"{'─'*70}")

    log.info("START  %s", mod_name)

    # Set alarm-based timeout (Unix only)
    old_handler = None
    if timeout and hasattr(signal, 'SIGALRM'):
        old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(timeout)

    t = time.time()
    try:
        result = mod.factor(n, **params)
    except _Timeout:
        elapsed = time.time() - t
        log.warning("TIMEOUT  %s after %.2fs (limit %ss)", mod_name, elapsed, timeout)
        print(f"\n  Timed out after {elapsed:.2f}s (limit {timeout}s)")
        return None
    except KeyboardInterrupt:
        elapsed = time.time() - t
        log.info("INTERRUPTED  %s after %.2fs", mod_name, elapsed)
        print(f"\n  Interrupted after {elapsed:.2f}s")
        return None
    except Exception as e:
        elapsed = time.time() - t
        log.error("ERROR  %s: %s: %s  [%.2fs]", mod_name, type(e).__name__, e, elapsed)
        print(f"\n  Error: {type(e).__name__}: {e}  [{elapsed:.2f}s]")
        return None
    finally:
        # Cancel any pending alarm
        if old_handler is not None:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

    elapsed = time.time() - t

    if result:
        p, q = sorted(result)
        valid = p * q == n
        log.info("FACTORED  %s in %.2fs  p=%d q=%d valid=%s", mod_name, elapsed, p, q, valid)
        print(f"\n  FACTORED in {elapsed:.2f}s")
        print(f"    p = {p}")
        print(f"    q = {q}")
        print(f"    p × q == N: {valid}")
        if not valid:
            print(f"    WARNING: product mismatch!")
        return result
    else:
        log.info("NO_FACTOR  %s  [%.2fs]", mod_name, elapsed)
        print(f"\n  No factor found  [{elapsed:.2f}s]")
        return None


def run_all(n, *, per_technique_timeout: int = 120):
    """Run all techniques sequentially until one succeeds.

    Parameters
    ----------
    per_technique_timeout : int
        Max seconds per technique (default 120).  Set to 0 to disable.
    """
    print(f"\n{'═'*70}")
    print(f"  Running ALL techniques on N = {n}")
    print(f"  {n.bit_length()} bits, {len(str(n))} digits")
    print(f"  Per-technique timeout: {per_technique_timeout}s")
    print(f"{'═'*70}")

    total_start = time.time()
    timeout = per_technique_timeout or None

    for idx, mod, title, desc, category in TECHNIQUES:
        # Skip techniques that need extra required params
        sig = inspect.signature(mod.factor)
        has_required = any(
            p.default is inspect.Parameter.empty
            for name, p in sig.parameters.items()
            if name not in ('n', 'kwargs')
        )
        if has_required:
            log.info("SKIP  %s (requires additional parameters)", title)
            print(f"\n  Skipping {title} (requires additional parameters)")
            continue

        result = run_technique(mod, title, n, {}, timeout=timeout)
        if result:
            total = time.time() - total_start
            print(f"\n{'═'*70}")
            print(f"  SUCCESS — {title} cracked it in {total:.2f}s total")
            print(f"{'═'*70}")
            return result

    total = time.time() - total_start
    print(f"\n{'═'*70}")
    print(f"  No technique succeeded  [{total:.2f}s total]")
    print(f"{'═'*70}")
    return None


def main():
    _load_techniques()
    print_banner()

    # If N provided on command line, use it
    argv_n = None
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        argv_n = sys.argv[1]

    while True:
        print_menu()

        choice = input("  Select technique: ").strip().lower()

        if choice == 'q':
            print("  Goodbye.")
            break

        try:
            choice_num = int(choice)
        except ValueError:
            print("  Invalid selection")
            continue

        if choice_num == 0:
            # Run all
            n = get_semiprime(argv_n)
            argv_n = None  # only use CLI arg once
            run_all(n)
            print()
            continue

        # Find the technique
        match = None
        for entry in TECHNIQUES:
            if entry[0] == choice_num:
                match = entry
                break

        if not match:
            print(f"  Invalid selection: {choice_num}")
            continue

        idx, mod, title, desc, category = match

        # Get parameters
        sig = inspect.signature(mod.factor)
        has_params = any(
            name not in ('n', 'kwargs')
            for name in sig.parameters
        )

        params = {}
        if has_params:
            print(f"\n  Parameters for {title} (press Enter for defaults):")
            params = get_params(mod)

        # Get semiprime
        n = get_semiprime(argv_n)
        argv_n = None

        run_technique(mod, title, n, params)
        print()


if __name__ == "__main__":
    main()
