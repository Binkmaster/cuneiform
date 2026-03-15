A useful way to think about “missing methods” is by target. Some attack factoring/RSA, some attack discrete logs/ECC, some attack symmetric ciphers, and some attack implementations rather than the math.

Methods not on your list
Integer factorization / RSA-family

General Number Field Sieve (GNFS)
The main classical method for factoring very large general integers, and the fastest known classical algorithm for large generic semiprimes.

Special Number Field Sieve (SNFS)
Faster than GNFS for numbers with special algebraic form, like 
re±s
r
e
±s.

Multiple Polynomial Quadratic Sieve (MPQS)
A major practical refinement of QS; ECM is often used to strip small factors first, then MPQS/GNFS takes over. ECM is widely viewed as best for roughly 50–60 digit factors, while MPQS/GNFS handle the rest.

Self-Initializing Quadratic Sieve (SIQS)
Another practical QS variant used in real implementations.

Rational Sieve
Historically important predecessor to NFS/QS; not usually best today, but part of the factoring family tree.

Continued-Fraction Factorization (CFRAC)
Older pre-QS method; largely obsolete in practice, but definitely part of the canon.

Dixon’s Factorization Method
Foundational random-squares method that influenced later sieve techniques.

Hart’s One-Line Factorization / Lehman-style methods
Niche practical methods for medium-size integers.

SQUFOF (Square Forms Factorization)
Very practical for small-to-medium factors; often used in software toolchains as a front-end step.

Aurifeuillean / algebraic factorization tricks
Special-form decompositions before heavy machinery.

RSA-specific cryptanalytic methods beyond Wiener / basic LLL

Coppersmith’s Method
A big missing one. It finds small roots of polynomial equations mod 
N
N, and is the backbone of many RSA attacks involving small 
e
e, partial key exposure, partial factor leakage, and related-message structure.

Boneh–Durfee Attack
Extends Wiener-style small-
d
d attacks using lattices; classically the next thing people mention after Wiener.

Partial Key Exposure Attacks
Recover RSA secrets when enough MSBs/LSBs of 
d
d, 
p
p, or 
q
q leak.

Håstad’s Broadcast Attack
Breaks low-exponent RSA when the same message is sent to multiple recipients without proper padding.

Franklin–Reiter Related-Message Attack
Breaks low-exponent RSA when plaintexts are algebraically related.

Bleichenbacher ’98 Padding Oracle
Not a factoring method; breaks RSA in practice via oracle behavior around PKCS#1 v1.5 padding. Boneh’s RSA survey still treats this as one of the classic practical RSA failures.

Manger’s Attack
Similar family: chosen-ciphertext attack against RSA padding/oracle behavior.

Common Modulus Attack
When the same modulus is reused badly with different exponents.

Batch GCD / Shared Prime Detection
Extremely practical: scan many public keys and find reused primes by gcd collisions. “RSA, DH and DSA in the Wild” is in this direction.

Approximate Common Divisor (ACD) attacks
More niche, but important in some cryptosystems and “integer-noise” constructions.

Hidden Number Problem (HNP) attacks
The lattice framework behind many partial nonce / biased nonce attacks, especially in DSA/ECDSA/Schnorr-type settings.

Discrete log / finite-field methods

Baby-Step Giant-Step (BSGS)
Classic meet-in-the-middle discrete log algorithm.

Index Calculus
Big missing family for finite-field discrete logs.

Number Field Sieve for Discrete Log (NFS-DL)
The discrete-log analogue of NFS; central for large finite fields.

Function Field Sieve (FFS)
Efficient for some finite fields, especially certain characteristics.

Pollard’s Kangaroo / Lambda
Especially useful when the discrete log lies in a known interval.

Cheon’s Algorithm
A specialized speedup for some discrete-log settings with extra order structure.

van Oorschot–Wiener Parallel Collision Search
Important practical framework for parallelizing rho-style discrete-log searches.

Coppersmith methods for small-characteristic finite fields
Historically important stepping stones toward later quasi-polynomial advances.

Quasi-polynomial DLP in small-characteristic fields
One of the more “weird/new” advances in the last decade-plus; important because it changed the picture for some finite fields.

ECC-specific methods not on your list

MOV Attack
Transfers ECDLP on certain weak curves into finite-field DLP using pairings.

Frey–Rück Attack
Same general idea: embedding into a field where DLP is easier.

Invalid-Curve Attack
Targets implementations that fail to validate points.

Twist Attack / Small-Subgroup Confinement
Exploits bad point validation or cofactor handling.

Cheon-style / auxiliary-input ECDLP variants
Specialized, structure-sensitive attacks.

Summation-polynomial / Gröbner-basis approaches to ECDLP
Usually not better than Pollard rho on standard prime curves, but definitely part of the “weird” literature.

Lattice / algebraic methods broader than “LLL”

BKZ-based lattice attacks
LLL is only the entry point; BKZ and its descendants matter for serious lattice cryptanalysis.

Gröbner Basis Attacks (F4/F5, XL)
Used against multivariate schemes, algebraic representations of ciphers, and some structured crypto problems.

SAT/SMT-based cryptanalysis
Translate cipher/key-recovery conditions into satisfiability problems.

MILP-based automated cryptanalysis
Very active area for finding differential, linear, impossible, and integral distinguishers automatically. Recent work continues pushing this.

Cube Attacks
Especially associated with stream ciphers and algebraic normal form structure.

Division-property attacks
Modern extension of integral/cube-style reasoning, often automated.

Linearization / relinearization attacks
More niche algebraic families.

Symmetric-key cryptanalysis families missing from your list

Linear Cryptanalysis
The other giant classic besides differential.

Differential-Linear Cryptanalysis
Hybrid of differential and linear.

Boomerang Attack
Combines short differentials into larger distinguishers; still an active line of work.

Rectangle Attack
Variant/generalization in the boomerang family.

Impossible Differential Cryptanalysis
Very active; still producing new results.

Zero-Correlation Linear Cryptanalysis
Closely related modern distinguisher family.

Integral / Square Attacks
Useful on SPN-style ciphers.

Interpolation Attacks
Algebraic attacks on ciphers with low-degree structure.

Meet-in-the-Middle (MITM) Attacks
Big family, especially for reduced-round or composed constructions.

Biclique Attacks
Famous for shaving a bit off full AES complexity without breaking AES in practice.

Slide Attacks
Exploit self-similar round structure.

Related-Key Attacks
Huge family against weak schedules.

Rotational / ARX-specific attacks
Important for ARX ciphers and hashes.

Invariant Subspace Attacks
More exotic, but real.

Statistical Saturation / Correlation Attacks
Especially stream ciphers.

Guess-and-Determine Attacks
Classic for stream ciphers and internal-state recovery.

Fast Algebraic Attacks
Stream cipher territory.

Hash / MAC / protocol attack families

Meet-in-the-middle preimage attacks on hashes

Differential path attacks on hashes

Chosen-prefix collision attacks

Length-extension attacks

Forgery via universal-hash structure

Bleichenbacher / ROBOT / DROWN-style protocol attacks

Nonce reuse / biased nonce attacks on DSA/ECDSA/Schnorr
Usually HNP/lattice underneath.

Implementation / side-channel / fault methods

These are often far more practical than pure math attacks:

Timing Attacks
Classic example: remote timing attacks on RSA/OpenSSL.

Power Analysis (SPA/DPA/CPA)

Electromagnetic Analysis

Cache Attacks

Branch-predictor / transient-execution side channels

Fault Injection (DFA, SIFA, voltage/clock/laser glitches)

Bellcore RSA fault attack

Rowhammer-assisted key extraction

Cold-boot attacks

Template attacks

Microarchitectural leakage attacks

Quantum, for completeness

Shor’s Algorithm
The headline quantum attack on factoring and discrete logs.

Grover-based key search
Not a break of modern symmetric crypto, but effectively weakens brute-force exponents.

“Weird / newer / deeper-cut” buckets

If you want the more unusual or modern-sounding ones specifically, these are good rabbit holes:

Summation-polynomial ECDLP methods

Hidden Number Problem variants

Approximate Common Divisor attacks

MILP/SAT/SMT automated distinguisher search

Division property

Boomerang / impossible-boomerang hybrids

Invariant subspace attacks

Rotational-XOR attacks

Quasi-polynomial discrete log in small-characteristic fields

Batch GCD at Internet scale

Invalid-curve / twist / subgroup confinement attacks

Fault + impossible differential hybrids — still actively appearing in recent papers.

One important note

Your current list mixes:

factoring methods

RSA structural attacks

ECDLP methods

lattice tools

implementation shortcuts

So if you want a really clean master taxonomy, the next step is to reorganize everything into:

Factoring

RSA structural/oracle attacks

Finite-field DLP

ECDLP

Lattice/algebraic frameworks

Symmetric cryptanalysis

Hash/protocol attacks

Side-channel/fault attacks

Quantum

I can turn your original list plus all of the above into a single normalized master list with columns like:
method | target | era | practical today? | asymptotic class | weirdness score

how long for a desktop computer to factor a 64bit semiprime

Usually well under a second on a normal desktop.

A 64-bit semiprime is tiny by modern factoring standards. With a decent implementation of Pollard rho, ECM, or even general-purpose libraries, it is typically factored in:

milliseconds to a fraction of a second for many cases

maybe a few seconds in a lousy or unoptimized setup

only longer if you deliberately use something dumb like naive trial division

For perspective:

a worst-case naive approach might check up to about 4.3 billion candidates

but real factoring code would not do that

64-bit integers are basically toy-sized for modern number factoring

So the practical answer is: instant, or close to it.

If you want, I can also give you a rough table for 64-bit vs 128-bit vs 256-bit vs RSA-512 vs RSA-1024 on a desktop.
