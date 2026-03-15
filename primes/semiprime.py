#!/usr/bin/env python3
"""Generate a semiprime of a given bit size.

Usage:
    python semiprime.py <bits>

Example:
    python semiprime.py 100

    Generates a 100-bit semiprime (product of two ~50-bit primes)
    and prints the semiprime and its two prime factors.
"""

import sys
import random

# Add parent to path
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from cuneiform.core.accel import isqrt, powmod


def is_prime_miller_rabin(n, rounds=20):
    """Miller-Rabin primality test."""
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0:
        return False

    # Write n-1 as 2^r * d
    r, d = 0, n - 1
    while d % 2 == 0:
        r += 1
        d //= 2

    rng = random.Random(n)  # deterministic per candidate
    for _ in range(rounds):
        a = rng.randrange(2, n - 1)
        x = powmod(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = powmod(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def random_prime(bits, rng):
    """Generate a random prime of exactly the given bit length."""
    while True:
        # Set the top bit to guarantee bit length, set bottom bit to guarantee odd
        n = rng.getrandbits(bits) | (1 << (bits - 1)) | 1
        if is_prime_miller_rabin(n):
            return n


def generate_semiprime(bits):
    """Generate a semiprime of exactly the given bit length.

    Returns (n, p, q) where n = p * q and p <= q.
    """
    rng = random.SystemRandom()

    # Each prime is roughly half the bits.
    # To hit the target bit length exactly, p gets floor(bits/2)
    # and q gets ceil(bits/2). Then n = p*q is bits or bits-1 bits.
    p_bits = bits // 2
    q_bits = bits - p_bits

    while True:
        p = random_prime(p_bits, rng)
        q = random_prime(q_bits, rng)

        if p == q:
            continue

        n = p * q
        if n.bit_length() == bits:
            if p > q:
                p, q = q, p
            return n, p, q


def main():
    if len(sys.argv) != 2:
        print("Usage: python semiprime.py <bits>")
        print("  e.g. python semiprime.py 100")
        sys.exit(1)

    try:
        bits = int(sys.argv[1])
    except ValueError:
        print(f"Error: '{sys.argv[1]}' is not a valid integer")
        sys.exit(1)

    if bits < 6:
        print("Error: need at least 6 bits (smallest semiprime with two distinct primes)")
        sys.exit(1)

    n, p, q = generate_semiprime(bits)
    digits = len(str(n))

    print(f"")
    print(f"  Semiprime ({bits} bits, {digits} digits):")
    print(f"  n = {n}")
    print(f"")
    print(f"  Factors:")
    print(f"  p = {p}  ({p.bit_length()} bits, {len(str(p))} digits)")
    print(f"  q = {q}  ({q.bit_length()} bits, {len(str(q))} digits)")
    print(f"")
    print(f"  Verify: p × q == n: {p * q == n}")


if __name__ == "__main__":
    main()
