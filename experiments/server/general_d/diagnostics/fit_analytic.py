"""Hunt for closed forms of computed gamma_k(CPTP,d) values.

Data: certified/cross-validated SDP optima from server runs (see README.md).
Method: continued fractions for rationals; mpmath PSLQ for algebraic numbers
of degree 2..4; structured-denominator scans for rationals of the form
N / (d^a (d^2-1)^b (d^2+1)^c).

Anti-overfit rule: a candidate relation is only reported if the total
coefficient "information" (sum of log10 |coeff|) stays well below the
number of trusted digits of the input value.
"""
from mpmath import mp, mpf, pslq, polyroots
from fractions import Fraction

mp.dps = 30

# value, trusted_digits, (d, k)
DATA = [
    ("2.7133302610598777", 8,  (2, 2)),   # 3 runs agree to ~5e-8
    ("7.4564496301614245", 9,  (3, 2)),   # 3 runs agree to ~4e-9
    ("1.8882914417",       10, (2, 3)),   # 2 runs agree to ~9e-10
    ("1.5294231841",       11, (2, 4)),   # 2 runs agree to ~3e-11
]

def cf_rational(x, digits):
    """Best rational approximations; report if denominator is small enough
    to be information-theoretically meaningful."""
    frac = Fraction(x).limit_denominator(10**6)
    err = abs(float(frac) - x)
    info = len(str(frac.numerator)) + len(str(frac.denominator))
    ok = err < 10 ** (-digits + 1) and info <= digits - 2
    return frac, err, ok

def pslq_degree(xs, deg, digits):
    v = [mpf(1)]
    for i in range(1, deg + 1):
        v.append(xs ** i)
    tol = mpf(10) ** (-(digits - 1))
    rel = pslq(v, tol=tol, maxcoeff=10**6, maxsteps=10000)
    if rel is None:
        return None
    # info budget: sum of digit-lengths of coefficients must fit in precision
    info = sum(len(str(abs(c))) for c in rel if c != 0)
    if info > digits - 2:
        return ("OVERFIT", rel, info)
    # verify the root is genuinely close
    poly = list(reversed(rel))
    try:
        roots = polyroots([mpf(c) for c in poly], maxsteps=200, extraprec=60)
    except Exception:
        return ("NOROOT", rel, info)
    best = min(abs(r - xs) for r in roots)
    return (rel, info, best)

def structured_rationals(x, d, digits):
    """Test r = (x-1)/2 and x itself against denominators
    d^a (d^2-1)^b (d^2+1)^c."""
    hits = []
    for target, label in [((x - 1) / 2.0, "(g-1)/2"), (x, "g")]:
        for a in range(0, 9):
            for b in range(0, 4):
                for c in range(0, 4):
                    D = (d ** a) * ((d * d - 1) ** b) * ((d * d + 1) ** c)
                    if D > 10**7 or D < 2:
                        continue
                    N = target * D
                    Nr = round(N)
                    if Nr == 0:
                        continue
                    err = abs(N - Nr) / D
                    info = len(str(abs(Nr))) + len(str(D))
                    if err < 10 ** (-digits + 1) and info <= digits - 2:
                        hits.append((label, Nr, f"d^{a}(d2-1)^{b}(d2+1)^{c}={D}", err))
    return hits

print("=" * 78)
print("known k=1: gamma_1 = 2d^2 - 3 + 2/d^2  (proven; d=2: 5.5, d=3: 137/9)")
print("old k=2 conjecture at d=2: 407/150 = 2.713333... vs computed 2.71333026")
print(f"  -> mismatch 3.07e-6 >> 5e-8 run-to-run spread: conjecture value REJECTED even at d=2")
print("=" * 78)

for s, digits, (d, k) in DATA:
    x = float(s)
    xs = mpf(s)
    print(f"\n--- gamma_{k}(CPTP, d={d}) = {s}  [{digits} trusted digits] ---")
    frac, err, ok = cf_rational(x, digits)
    print(f"  rational CF: {frac} (err {err:.2e}) {'<= PLAUSIBLE' if ok else '(rejected: too much info / too far)'}")
    for hit in structured_rationals(x, d, digits):
        print(f"  structured rational HIT: {hit[0]} = {hit[1]} / {hit[2]}  err {hit[3]:.2e}")
    for deg in (2, 3, 4):
        r = pslq_degree(xs, deg, digits)
        if r is None:
            print(f"  degree {deg}: no relation (maxcoeff 1e6)")
        elif r[0] == "OVERFIT":
            print(f"  degree {deg}: relation {r[1]} but info {r[2]} > budget -> overfit, ignored")
        elif r[0] == "NOROOT":
            print(f"  degree {deg}: relation {r[1]} failed root check")
        else:
            rel, info, best = r
            print(f"  degree {deg}: PLAUSIBLE relation {rel} (info {info}, root err {float(best):.2e})")
