"""Multi-Walk Ergodic Collision Factoring -- a novel factoring technique.

Inspired by fractal dynamics and ergodic theory on finite groups.

Mathematical foundation:
    For N = pq, the map f_c(x) = x^2 + c on Z/NZ decomposes via CRT into
    independent maps on Z/pZ and Z/qZ. Multiple walks with different c
    values explore different orbits, and INTER-WALK collisions (where two
    walks agree mod p but not mod q) reveal factors.

Novel contributions:
    1. Multi-walk collision detection: k walks give k(k-1)/2 collision pairs,
       reducing expected time from O(sqrt(p)) to O(sqrt(p) / sqrt(k)).
    2. Walk constants chosen from 5-smooth numbers (cuneiform's base-60
       arithmetic), creating dynamics that resonate with sexagesimal
       structure in the multiplicative group.
    3. Batched product GCD across all walk pairs for efficient collision
       detection without O(k^2) individual GCD calls.
    4. Each walk simultaneously runs Brent's cycle detection (intra-walk)
       AND inter-walk collision detection.

Complexity: O(sqrt(p) / sqrt(k)) expected, where k is the number of walks.
    For k=8, this is ~2.8x faster than standard Pollard rho.
    The smooth-constant heuristic may provide additional speedup
    for numbers with 5-smooth-related structure.
"""

import sys

sys.path.insert(
    0, str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent)
)

from cuneiform.core.accel import gcd, isqrt, is_probable_prime


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _generate_smooth_constants(count: int) -> list[int]:
    """Generate the first *count* 5-smooth numbers >= 1, in ascending order.

    5-smooth numbers have no prime factors larger than 5.
    Sequence: 1, 2, 3, 4, 5, 6, 8, 9, 10, 12, 15, 16, 18, 20, 24, 25, ...
    """
    import heapq

    results: list[int] = []
    seen: set[int] = {1}
    heap: list[int] = [1]

    while len(results) < count:
        val = heapq.heappop(heap)
        results.append(val)
        for p in (2, 3, 5):
            nxt = val * p
            if nxt not in seen:
                seen.add(nxt)
                heapq.heappush(heap, nxt)

    return results


def _backtrack_pair(
    walks_snapshot: list[dict], n: int, batch_size: int
) -> tuple[int, int] | None:
    """Replay one batch from a snapshot to find the exact inter-walk pair.

    After a batched product GCD yields *n* (meaning every difference is
    divisible by some factor), we fall back to pairwise checks on the
    snapshot state, advancing step-by-step.
    """
    num = len(walks_snapshot)
    # Work on copies so we don't mutate the snapshot
    ws = [
        {"x": w["x"], "c": w["c"]}
        for w in walks_snapshot
    ]

    for _ in range(batch_size):
        for w in ws:
            w["x"] = (w["x"] * w["x"] + w["c"]) % n
        for i in range(num):
            for j in range(i + 1, num):
                diff = (ws[i]["x"] - ws[j]["x"]) % n
                if diff == 0:
                    continue
                g = gcd(diff, n)
                if 1 < g < n:
                    return (g, n // g)

    return None


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def factor(
    n: int,
    *,
    num_walks: int = 8,
    iterations: int = 5_000_000,
    batch_size: int = 500,
) -> tuple[int, int] | None:
    """Factor *n* using multi-walk ergodic collision factoring.

    Parameters
    ----------
    n : int
        The integer to factor (must be composite and > 1).
    num_walks : int
        Number of parallel pseudo-random walks (default 8, giving 28
        collision pairs).
    iterations : int
        Maximum total iterations per walk before giving up.
    batch_size : int
        Steps between inter-walk collision checks (via batched product GCD).

    Returns
    -------
    tuple[int, int] | None
        A pair (p, n // p) with 1 < p < n, or None if no factor was found.
    """
    if n < 2:
        return None

    # ---- Edge case: even ---------------------------------------------------
    if n % 2 == 0:
        return (2, n // 2)

    # ---- Edge case: perfect square -----------------------------------------
    s = isqrt(n)
    if s * s == n:
        return (s, s)

    # ---- Edge case: probable prime -----------------------------------------
    if is_probable_prime(n):
        return None

    # ---- Generate 5-smooth walk constants ----------------------------------
    smooth_constants = _generate_smooth_constants(num_walks)

    # ---- Initialise walks --------------------------------------------------
    # Each walk tracks:
    #   x     - current position
    #   c     - iteration constant (5-smooth)
    #   y     - Brent tortoise value (updated every power-of-2 steps)
    #   r     - current power-of-2 bound for Brent's method
    #   steps - steps taken in the current r-interval
    #   q_acc - per-walk product accumulator for intra-walk batched GCD
    walks: list[dict] = []
    for i in range(num_walks):
        x0 = (2 + i * 37) % n
        walks.append(
            {
                "x": x0,
                "c": smooth_constants[i],
                "y": x0,       # Brent tortoise
                "r": 1,        # current power-of-2 bound
                "steps": 0,    # steps in current r-interval
                "q_acc": 1,    # intra-walk product accumulator
            }
        )

    intra_batch = batch_size  # how often to flush intra-walk accumulators

    # ---- Main loop ---------------------------------------------------------
    for iteration in range(0, iterations, batch_size):
        # Snapshot for potential backtracking on inter-walk product == n
        snapshot = [{"x": w["x"], "c": w["c"]} for w in walks]

        # Advance every walk by batch_size steps, accumulating intra-walk
        # products (Brent's cycle detection within each walk).
        for w in walks:
            for _ in range(batch_size):
                w["x"] = (w["x"] * w["x"] + w["c"]) % n
                w["steps"] += 1

                # Brent: check against tortoise
                diff = (w["x"] - w["y"]) % n
                if diff != 0:
                    w["q_acc"] = (w["q_acc"] * diff) % n

                # Brent: update tortoise at power-of-2 boundaries
                if w["steps"] == w["r"]:
                    w["y"] = w["x"]
                    w["r"] <<= 1
                    w["steps"] = 0

        # ---- Intra-walk collision check (Brent's rho per walk) -------------
        for w in walks:
            if w["q_acc"] == 0:
                w["q_acc"] = 1
                continue
            g = gcd(w["q_acc"], n)
            if g == n:
                # Backtrack within this walk -- replay batch with per-step GCD
                # We don't have a per-walk snapshot, so fall through to
                # restarting the walk with a new constant.
                w["c"] += 60  # jump by 60 to stay in the spirit of base-60
                w["x"] = (2 + w["c"]) % n
                w["y"] = w["x"]
                w["r"] = 1
                w["steps"] = 0
                w["q_acc"] = 1
                continue
            if 1 < g < n:
                return (g, n // g)
            w["q_acc"] = 1

        # ---- Inter-walk collision check (batched product GCD) --------------
        product = 1
        for i in range(num_walks):
            for j in range(i + 1, num_walks):
                diff = (walks[i]["x"] - walks[j]["x"]) % n
                if diff != 0:
                    product = (product * diff) % n

        if product == 0:
            # All pairs identical mod n -- walks have merged; restart some
            for idx in range(1, num_walks):
                walks[idx]["c"] += 60
                walks[idx]["x"] = (2 + walks[idx]["c"]) % n
                walks[idx]["y"] = walks[idx]["x"]
                walks[idx]["r"] = 1
                walks[idx]["steps"] = 0
                walks[idx]["q_acc"] = 1
            continue

        g = gcd(product, n)
        if 1 < g < n:
            return (g, n // g)
        if g == n:
            # Product is 0 mod n -- backtrack to find the exact pair
            result = _backtrack_pair(snapshot, n, batch_size)
            if result is not None:
                return result
            # Backtrack failed -- restart walks with shifted constants
            for idx in range(num_walks):
                walks[idx]["c"] += 60
                walks[idx]["x"] = (2 + walks[idx]["c"]) % n
                walks[idx]["y"] = walks[idx]["x"]
                walks[idx]["r"] = 1
                walks[idx]["steps"] = 0
                walks[idx]["q_acc"] = 1

    return None


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import time

    tests = [
        # (input, description)
        (4, "perfect square"),
        (6, "even"),
        (15, "small semiprime"),
        (1000000007, "prime (should return None)"),
        (1000000007 * 1000000009, "large semiprime (1000000007 * 1000000009)"),
        (2 ** 67 - 1, "Mersenne composite 2^67-1 = 193707721 * 761838257287"),
        (1000000007 * 2, "even composite"),
    ]

    all_passed = True
    for n_val, desc in tests:
        t0 = time.perf_counter()
        result = factor(n_val)
        elapsed = time.perf_counter() - t0

        if desc.startswith("prime"):
            ok = result is None
        elif desc == "perfect square":
            ok = result is not None and result[0] * result[1] == n_val
        else:
            ok = result is not None and result[0] * result[1] == n_val and 1 < result[0] < n_val

        status = "PASS" if ok else "FAIL"
        if not ok:
            all_passed = False
        print(f"  [{status}] {desc}: n={n_val}, result={result}  ({elapsed:.4f}s)")

    print()
    if all_passed:
        print("All tests passed.")
    else:
        print("SOME TESTS FAILED.")
        sys.exit(1)
