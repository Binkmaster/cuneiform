"""Prime number utilities used across the number theory layer."""

from __future__ import annotations

from math import isqrt, log, exp, sqrt


def sieve_of_eratosthenes(limit: int) -> list[int]:
    """Return all primes up to limit."""
    if limit < 2:
        return []
    is_prime = [True] * (limit + 1)
    is_prime[0] = is_prime[1] = False
    for i in range(2, isqrt(limit) + 1):
        if is_prime[i]:
            for j in range(i * i, limit + 1, i):
                is_prime[j] = False
    return [i for i, v in enumerate(is_prime) if v]


def is_prime(n: int) -> bool:
    """Miller-Rabin primality test, deterministic for n < 3.3e24."""
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    # Write n-1 = 2^r * d
    d = n - 1
    r = 0
    while d % 2 == 0:
        d //= 2
        r += 1
    # Deterministic witnesses for n < 3.3e24
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


def largest_prime_factor(n: int) -> int:
    """Find the largest prime factor of n."""
    if n <= 1:
        return 1
    largest = 1
    d = 2
    while d * d <= n:
        while n % d == 0:
            largest = d
            n //= d
        d += 1
    if n > 1:
        largest = n
    return largest


def count_prime_factors(n: int) -> int:
    """Count prime factors of n with multiplicity (big omega)."""
    if n <= 1:
        return 0
    count = 0
    d = 2
    while d * d <= n:
        while n % d == 0:
            count += 1
            n //= d
        d += 1
    if n > 1:
        count += 1
    return count


def legendre_symbol(a: int, p: int) -> int:
    """Compute the Legendre symbol (a/p) for odd prime p."""
    if p == 2:
        return 1
    a = a % p
    if a == 0:
        return 0
    result = pow(a, (p - 1) // 2, p)
    if result == p - 1:
        return -1
    return result


def tonelli_shanks(n: int, p: int) -> list[int]:
    """Find square roots of n mod p (where p is prime).

    Returns list of roots (0, 1, or 2 values).
    """
    if p == 2:
        return [n % 2]
    ls = legendre_symbol(n, p)
    if ls == 0:
        return [0]
    if ls == -1:
        return []

    # Factor out powers of 2 from p-1
    q = p - 1
    s = 0
    while q % 2 == 0:
        q //= 2
        s += 1

    if s == 1:
        # p ≡ 3 mod 4
        r = pow(n, (p + 1) // 4, p)
        return sorted({r, p - r})

    # Find a non-residue
    z = 2
    while legendre_symbol(z, p) != -1:
        z += 1

    m = s
    c = pow(z, q, p)
    t = pow(n, q, p)
    r = pow(n, (q + 1) // 2, p)

    while True:
        if t == 1:
            return sorted({r % p, (p - r) % p})
        # Find least i such that t^(2^i) ≡ 1 mod p
        i = 1
        temp = (t * t) % p
        while temp != 1:
            temp = (temp * temp) % p
            i += 1
        b = pow(c, 1 << (m - i - 1), p)
        m = i
        c = (b * b) % p
        t = (t * c) % p
        r = (r * b) % p


def optimal_smoothness_bound(n: int) -> int:
    """Compute L(n)^(1/sqrt(2)) — optimal smoothness bound for QS/NFS."""
    ln_n = log(max(n, 3))
    ln_ln_n = log(max(ln_n, 1.01))
    L = exp(sqrt(ln_n * ln_ln_n))
    return max(int(L ** (1 / sqrt(2))), 20)
