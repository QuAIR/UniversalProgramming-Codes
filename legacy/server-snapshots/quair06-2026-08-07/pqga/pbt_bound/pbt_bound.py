"""
Exact finite-k standard (deterministic, PGM) port-based teleportation fidelity,
and the resulting CERTIFIED finite-k upper bound on nu_k(CPTP_d).

Formula (Studzinski-Strelchuk-Mozrzymas-Horodecki 2017):

    F_d(N) = d^{-(N+2)} * sum_{alpha |- N-1, l(alpha)<=d}
                          ( sum_{mu = alpha + box, l(mu)<=d} sqrt( m_mu * d_mu ) )^2

  d_mu = dim of S_N irrep mu            (branching recursion)
  m_mu = dim of U(d) irrep mu           (Weyl dimension formula)

Then, with F_e(D_eta) = eta + (1-eta)/d^2,

    eta_{k,d} = (d^2 F - 1) / (d^2 - 1)
    nu_k(CPTP_d) <= || D_{1/eta} ||_diamond = 1 + 2 (1 - d^{-2}) (1/eta - 1)

The norm identity is exact (arxiv.tex eq:inverse_depol_norm), so evaluating it
at the EXACT finite-k eta gives a rigorous upper bound at every k, not only an
asymptotic one.

Self-tests:
  * N=1 must give F = 1/d^2 (one port => completely depolarizing => eta=0).
  * 4N(1-F) -> d^2 - 1 as N -> infinity.
"""

import math
import sys
from functools import lru_cache


# ---------------------------------------------------------------- partitions
def partitions(n, max_parts, max_val=None):
    """All partitions of n into at most max_parts parts (weakly decreasing)."""
    if max_val is None:
        max_val = n
    if n == 0:
        yield ()
        return
    if max_parts == 0:
        return
    for first in range(min(n, max_val), 0, -1):
        for rest in partitions(n - first, max_parts - 1, first):
            yield (first,) + rest


def add_box(alpha, d):
    """All partitions mu with at most d rows obtained from alpha by adding a box."""
    out = []
    for i in range(min(len(alpha) + 1, d)):
        lam = list(alpha)
        if i == len(alpha):
            lam.append(1)
        else:
            if i > 0 and lam[i] + 1 > lam[i - 1]:
                continue
            lam[i] += 1
        out.append(tuple(lam))
    return out


def remove_box(mu):
    """All partitions obtained from mu by removing a box."""
    out = []
    for i in range(len(mu)):
        if i + 1 < len(mu) and mu[i] - 1 < mu[i + 1]:
            continue
        lam = list(mu)
        lam[i] -= 1
        if lam[i] == 0:
            if i != len(mu) - 1:
                continue
            lam.pop()
        out.append(tuple(lam))
    return out


# ------------------------------------------------------------ dim of S_n irrep
@lru_cache(maxsize=None)
def _fact(n):
    return math.factorial(n)


@lru_cache(maxsize=None)
def dim_Sn(mu):
    """Number of standard Young tableaux of shape mu (hook length formula)."""
    if not mu:
        return 1
    n = sum(mu)
    conj = [sum(1 for r in mu if r > j) for j in range(mu[0])]
    hooks = 1
    for i, row in enumerate(mu):
        for j in range(row):
            hooks *= (row - j) + (conj[j] - i) - 1
    return _fact(n) // hooks


# ------------------------------------------------------------ dim of U(d) irrep
@lru_cache(maxsize=None)
def dim_Ud(mu, d):
    """Weyl dimension formula: prod_{i<j} (mu_i - mu_j + j - i) / (j - i)."""
    lam = list(mu) + [0] * (d - len(mu))
    num, den = 1, 1
    for i in range(d):
        for j in range(i + 1, d):
            num *= lam[i] - lam[j] + (j - i)
            den *= (j - i)
    assert num % den == 0
    return num // den


# ------------------------------------------------------------------- fidelity
@lru_cache(maxsize=None)
def pbt_fidelity(N, d):
    """Exact standard-PBT entanglement fidelity F_d(N), as a float in [0,1]."""
    if N < 1:
        raise ValueError("N >= 1")
    dN = d ** N
    total = 0.0
    for alpha in partitions(N - 1, d):
        s = 0.0
        for mu in add_box(alpha, d):
            w = dim_Ud(mu, d) * dim_Sn(mu)   # exact big integer
            s += math.sqrt(w / dN)           # sqrt(m_mu d_mu / d^N)
        total += s * s
    return total / (d * d)


def eta_from_F(F, d):
    """Depolarizing parameter of the induced PBT channel."""
    return (d * d * F - 1.0) / (d * d - 1.0)


def nu_upper(N, d):
    """Certified bound nu_N(CPTP_d) <= 1 + 2(1-d^-2)(1/eta - 1); inf if eta<=0."""
    eta = eta_from_F(pbt_fidelity(N, d), d)
    if eta <= 0.0:
        return math.inf
    return 1.0 + 2.0 * (1.0 - 1.0 / (d * d)) * (1.0 / eta - 1.0)


# ----------------------------------------------------------------- self-tests
if __name__ == "__main__":
    print("=== check 1: N=1 must give F = 1/d^2, eta = 0 ===", flush=True)
    for d in (2, 3, 4, 5):
        F = pbt_fidelity(1, d)
        print(f"  d={d}: F(1)={F:.12f}   1/d^2={1/d**2:.12f}   "
              f"eta={eta_from_F(F, d):.3e}", flush=True)

    print("\n=== check 2: 4N(1-F) -> d^2-1 ===", flush=True)
    grids = {2: (10, 25, 50, 100, 200, 400, 800),
             3: (10, 25, 50, 100, 200),
             4: (10, 25, 50, 100),
             5: (10, 25, 50, 80)}
    for d in (2, 3, 4, 5):
        print(f"  d={d}  (target d^2-1 = {d*d-1})", flush=True)
        for N in grids[d]:
            F = pbt_fidelity(N, d)
            print(f"    N={N:4d}  F={F:.10f}  4N(1-F)={4*N*(1-F):.5f}", flush=True)

    print("\n=== certified finite-k upper bounds ===", flush=True)
    for d in (2, 3, 4, 5):
        parts = []
        for k in range(1, 13):
            u = nu_upper(k, d)
            parts.append(f"k={k}:" + ("inf" if math.isinf(u) else f"{u:.4f}"))
        print(f"  d={d}: " + "  ".join(parts), flush=True)
