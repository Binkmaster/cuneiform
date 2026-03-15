"""Acceleration shim — gmpy2 when available, stdlib fallback.

gmpy2 wraps the GMP, MPFR, and MPC libraries, providing 10-100x faster
big-integer arithmetic compared to Python's built-in int type. This module
provides a single import point so the rest of the library transparently
benefits when gmpy2 is installed.

Install:  pip install gmpy2
  or:     pip install cuneiform[fast]
"""

from __future__ import annotations

import math as _math

try:
    import gmpy2 as _gmpy2

    HAS_GMPY2 = True

    # --- integer type ---
    mpz = _gmpy2.mpz

    # --- core arithmetic ---
    def gcd(a, b):
        """Greatest common divisor (GMP-accelerated)."""
        return int(_gmpy2.gcd(mpz(a), mpz(b)))

    def isqrt(n):
        """Integer square root (GMP-accelerated)."""
        return int(_gmpy2.isqrt(mpz(n)))

    def powmod(base, exp, mod):
        """Modular exponentiation: base^exp mod mod (GMP-accelerated)."""
        return int(_gmpy2.powmod(mpz(base), mpz(exp), mpz(mod)))

    def invert(a, n):
        """Modular inverse: a^(-1) mod n (GMP-accelerated).

        Raises ZeroDivisionError if inverse does not exist.
        """
        result = _gmpy2.invert(mpz(a), mpz(n))
        if result == 0:
            raise ZeroDivisionError(f"{a} has no inverse mod {n}")
        return int(result)

    def is_probable_prime(n, rounds=25):
        """Miller-Rabin primality test (GMP-accelerated).

        GMP's mpz_probab_prime_p uses trial division + Miller-Rabin.
        Returns True if n is probably prime.
        """
        return _gmpy2.is_prime(mpz(n), rounds)

    def ilog2(n):
        """Floor of log2(n) (GMP bit_length)."""
        v = mpz(n)
        return int(v.bit_length()) - 1 if v > 0 else 0

except ImportError:
    HAS_GMPY2 = False

    mpz = int

    def gcd(a, b):
        """Greatest common divisor (stdlib)."""
        return _math.gcd(a, b)

    def isqrt(n):
        """Integer square root (stdlib)."""
        return _math.isqrt(n)

    def powmod(base, exp, mod):
        """Modular exponentiation (stdlib)."""
        return pow(base, exp, mod)

    def invert(a, n):
        """Modular inverse (stdlib, Python 3.8+)."""
        return pow(a, -1, n)

    def is_probable_prime(n, rounds=25):
        """Miller-Rabin primality test (pure Python fallback)."""
        # Defer to the deterministic implementation in primes.py
        # This avoids a circular import — callers that need is_prime
        # should use number_theory.primes.is_prime directly.
        if n < 2:
            return False
        if n < 4:
            return True
        if n % 2 == 0 or n % 3 == 0:
            return False
        d = n - 1
        r = 0
        while d % 2 == 0:
            d //= 2
            r += 1
        witnesses = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]
        for a in witnesses:
            if a >= n:
                continue
            x = pow(a, d, n)
            if x == 1 or x == n - 1:
                continue
            for _ in range(r - 1):
                x = pow(x, 2, n)
                if x == n - 1:
                    break
            else:
                return False
        return True

    def ilog2(n):
        """Floor of log2(n) (stdlib)."""
        return n.bit_length() - 1 if n > 0 else 0
