# primes/

Experimental scripts that run the full CUNEIFORM toolkit against RSA challenge numbers. Not serious factoring attempts — just exploring how regularity classification and sexagesimal analysis interact with real cryptographic targets.

- `factor_rsa2048.py` — 14-phase analysis of RSA-2048 (trial division, Pollard p-1/rho, ECM, Wiener, lattice reduction, QS demo, and more)
- `factor_rsa260.py` — same approach applied to RSA-260

```bash
python factor_rsa2048.py
```

RSA-2048 remains unfactored.
