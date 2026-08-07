#!/usr/bin/env python3
"""
Exact S_k-invariance complexity reduction for k-copy quantum programming SDP.

Mathematical framework:
- SDP variables live in commutant algebra B_{1,k}(d) x B_{k,1}(d)
- B_{1,k}(d) is the walled Brauer algebra, semisimple iff d >= k+1
- Artin-Wedderburn decomposition gives PSD blocks of size w_lam * w_mu
- S_k symmetry (permuting k program copies) refines blocks via Kronecker coefficients
- Irreps labeled by bi-partitions (alpha, beta) with f=0 or f=1 contractions

Key formulas:
  f=0: alpha=(1,), beta |- k, l(beta) <= d-1, w = dim(S^beta)  [S_k Specht module]
  f=1: alpha=(),  beta |- (k-1), l(beta) <= d, w = k * dim(S^beta)

  Branching to S_k:
    f=0: restricts to single S_k-irrep S^beta
    f=1: restricts to Ind_{S_{k-1}}^{S_k}(S^beta) = oplus_gamma S^gamma
         (gamma from adding one box to beta)

  Refined block sizes:
    n_gamma^{lam,mu} = sum_{alpha,beta} m_alpha^lam * m_beta^mu * g(alpha,beta,gamma)
    where g = Kronecker coefficient of S_k
"""

from math import factorial, prod
from collections import Counter
from functools import lru_cache
import sys

# ======================================================================
# Partitions
# ======================================================================
def partitions_of(n):
    if n == 0: yield (); return
    def _gen(n, mx):
        if n == 0: yield (); return
        for i in range(min(n,mx),0,-1):
            for r in _gen(n-i,i): yield (i,)+r
    yield from _gen(n,n)

def conjugate_partition(lam):
    if not lam: return ()
    return tuple(sum(1 for p in lam if p >= i) for i in range(1, lam[0]+1))

def hook_lengths(lam):
    conj = conjugate_partition(lam)
    return [(lam[i]-j-1)+(conj[j]-i-1)+1 for i in range(len(lam)) for j in range(lam[i])]

def dim_specht(lam):
    n = sum(lam)
    if n == 0: return 1
    return factorial(n) // prod(hook_lengths(lam))

def addable_boxes(beta):
    """Partitions of |beta|+1 obtained by adding one box to beta."""
    result = []
    bl = list(beta) if beta else []
    n = len(bl)
    for i in range(n+1):
        if i == 0:
            new = list(bl)
            new[0] = new[0]+1 if new else 1
            if not bl: new = [1]
            result.append(tuple(new))
        elif i < n:
            if bl[i] < bl[i-1]:
                new = list(bl); new[i] += 1; result.append(tuple(new))
        else:
            result.append(tuple(bl + [1]))
    return result

# ======================================================================
# Character table via Murnaghan-Nakayama rule (verified S_2..S_6)
# ======================================================================
@lru_cache(maxsize=None)
def char_val(lam, mu):
    n = sum(lam)
    if n == 0: return 1
    if not lam or not mu: return 0
    r = mu[0]; mu_rest = mu[1:]
    return sum((-1)**ht * char_val(nl, mu_rest) for nl, ht in border_strips(lam, r))

def border_strips(lam, r):
    """Rim hooks of size r in partition lam. Returns (new_partition, height)."""
    if r == 0: yield (lam, 0); return
    if not lam: return
    ll = list(lam); n = len(ll)
    rim = [(i,j) for i in range(n) for j in range(ll[i])
           if i+1 >= n or j+1 >= ll[i+1]]
    if not rim: return
    rim_set = set(rim)
    start = min(rim, key=lambda x: (x[0], -x[1]))
    path = [start]; vis = {start}; cur = start
    while True:
        i, j = cur; nxt = None
        for ni, nj in [(i+1,j),(i,j-1),(i-1,j),(i,j+1)]:
            if (ni,nj) in rim_set and (ni,nj) not in vis:
                nxt = (ni,nj); break
        if nxt is None: break
        path.append(nxt); vis.add(nxt); cur = nxt
    for s in range(len(path)-r+1):
        strip = path[s:s+r]
        rows = set(b[0] for b in strip)
        ht = max(rows) - min(rows)
        rem = Counter(b[0] for b in strip)
        nl = list(ll); ok = True
        for row, cnt in rem.items():
            cols = sorted(b[1] for b in strip if b[0]==row)
            if cols != list(range(nl[row]-cnt, nl[row])): ok = False; break
            nl[row] -= cnt
        if not ok: continue
        while nl and nl[-1]==0: nl.pop()
        if all(nl[i]>=nl[i+1] for i in range(len(nl)-1)):
            yield (tuple(nl), ht)

def cycle_types(n):
    result = []
    for p in partitions_of(n):
        cnt = Counter(p)
        denom = prod(v**c * factorial(c) for v, c in cnt.items())
        result.append((p, factorial(n)//denom))
    return result

def centralizer_size(ct):
    cnt = Counter(ct)
    return prod(v**c * factorial(c) for v, c in cnt.items())

def kronecker_coeff(a, b, g, k, classes):
    total = sum(sz * char_val(a, mu) * char_val(b, mu) * char_val(g, mu)
                for mu, sz in classes)
    assert total % factorial(k) == 0, f"g({a},{b},{g}): {total}/{factorial(k)} not int"
    return total // factorial(k)

# ======================================================================
# GL(d) dimension via Weyl formula
# ======================================================================
def gl_dim(alpha, beta, d):
    la, lb = len(alpha), len(beta)
    if la+lb > d: return 0
    w = list(alpha) + [0]*(d-la-lb) + [-beta[lb-1-i] for i in range(lb)]
    num = den = 1
    for i in range(d):
        for j in range(i+1, d):
            num *= (w[i]-w[j]+j-i); den *= (j-i)
    return num // den

# ======================================================================
# Burnside orbit counts (d-independent, valid for d >= k+1)
# ======================================================================
def burnside_generic(k):
    classes = cycle_types(k)
    ell = m = 0
    for tau, csz in classes:
        tau_t = tuple(sorted(tau+(1,), reverse=True))
        z = centralizer_size(tau_t)
        ell += csz * z
        m += csz * z * z
    return ell//factorial(k), m//factorial(k)

# ======================================================================
# Walled Brauer algebra irreps
# ======================================================================
def wba_irreps(d, k):
    """Returns list of ((alpha,beta), w, s) for irreps in W (x) (W*)^{(x)k}."""
    irreps = []
    # f=0 sector: alpha=(1,), beta |- k, l(beta) <= d-1
    for beta in partitions_of(k):
        if len(beta) <= d-1:
            irreps.append(((1,), beta, dim_specht(beta), gl_dim((1,), beta, d)))
    # f=1 sector: alpha=(), beta |- (k-1), l(beta) <= d
    if k >= 1:
        for beta in partitions_of(k-1):
            lb = len(beta) if beta else 0
            if lb <= d:
                wb = dim_specht(beta) if beta else 1
                irreps.append(((), beta, k*wb, gl_dim((), beta, d)))
    return irreps

# ======================================================================
# Branching to S_k
# ======================================================================
def branch(alpha, beta, k):
    if alpha == (1,):
        return [(beta, 1)]
    else:  # alpha = ()
        if k == 1: return [((1,), 1)]
        return [(g, 1) for g in addable_boxes(beta)]

# ======================================================================
# Main computation for one (d,k)
# ======================================================================
def compute(d, k):
    R = {'d': d, 'k': k}
    R['semisimple'] = (d >= k+1)
    R['D'] = d**(2*(k+1))

    ell_gen, m_gen = burnside_generic(k)
    R['ell_gen'] = ell_gen
    R['m_gen'] = m_gen

    raw = wba_irreps(d, k)
    irreps = [(a, b, w, s) for a, b, w, s in raw]
    R['irreps'] = irreps

    ell = sum(w**2 for _, _, w, _ in irreps)
    R['ell'] = ell
    R['ws_sum'] = sum(w*s for _, _, w, s in irreps)
    R['dk1'] = d**(k+1)
    R['n_irr'] = len(irreps)
    R['m_old'] = ell**2
    R['max_w'] = max(w for _, _, w, _ in irreps)
    R['mx_old'] = R['max_w']**2

    R['psd_e_old'] = sum((w1*w2)**2 for _,_,w1,_ in irreps for _,_,w2,_ in irreps)
    R['psd_p_old'] = sum(w1*w2*(w1*w2+1)//2 for _,_,w1,_ in irreps for _,_,w2,_ in irreps)
    R['n_blk_old'] = len(irreps)**2

    br = {}
    for a, b, w, s in irreps:
        br[(a,b)] = branch(a, b, k)
    R['br'] = br

    parts_k = list(partitions_of(k))
    classes_k = cycle_types(k)

    refined = []
    pe = pp = mx = nb = 0
    for a1,b1,w1,s1 in irreps:
        br1 = br[(a1,b1)]
        for a2,b2,w2,s2 in irreps:
            br2 = br[(a2,b2)]
            for g in parts_k:
                ng = sum(m1*m2*kronecker_coeff(al,be,g,k,classes_k)
                         for al,m1 in br1 for be,m2 in br2)
                if ng > 0:
                    refined.append((a1,b1,a2,b2,g,ng,w1*w2))
                    pe += ng**2; pp += ng*(ng+1)//2
                    mx = max(mx, ng); nb += 1

    R['refined'] = refined
    R['psd_e_new'] = pe
    R['psd_p_new'] = pp
    R['mx_new'] = mx
    R['n_blk_new'] = nb
    R['m_actual'] = pe  # actual d-dependent S_k orbit count

    return R

# ======================================================================
# Formatting
# ======================================================================
def fpart(p):
    return str(p) if p else "()"

def fbip(a, b):
    return f"({fpart(a)},{fpart(b)})"

# ======================================================================
# Output
# ======================================================================
def detail(R):
    d, k = R['d'], R['k']
    ss = R['semisimple']
    print(f"\n{'='*78}")
    print(f"  (d, k) = ({d}, {k})    B_{{1,{k}}}({d}) semisimple: {'YES' if ss else 'NO'} (need d >= {k+1})")
    print(f"{'='*78}")

    print(f"\n  OVERVIEW")
    print(f"    Full SDP dimension D = d^{{2(k+1)}} = {R['D']:,}")
    print(f"    AW algebra dimension ell = {R['ell']}" +
          (f" = {k+1}!" if R['ell']==factorial(k+1) else f" < {k+1}! = {factorial(k+1)}"))
    print(f"    SDP variables before S_k: m_old = ell^2 = {R['m_old']:,}")
    print(f"    SDP variables after S_k:  m_Sk  = {R['m_actual']:,}")
    ratio = R['m_old']/R['m_actual']
    print(f"    Variable reduction ratio: {ratio:.1f}x")
    if ss:
        print(f"    (matches generic Burnside: {R['m_gen']})")
    else:
        print(f"    (generic Burnside for d->inf: {R['m_gen']}, ratio: {R['m_old']/R['m_gen']:.1f}x)")

    print(f"\n  AW BLOCK STRUCTURE  ({R['n_irr']} irreps per sector)")
    print(f"    {'f':>1s}  {'(alpha, beta)':<25s} {'w_lam':>6s} {'s_lam':>8s}")
    print(f"    {'-':->1s}  {'-':->25s} {'-':->6s} {'-':->8s}")
    for a, b, w, s in R['irreps']:
        f = 0 if a==(1,) else 1
        print(f"    {f}  {fbip(a,b):<25s} {w:>6d} {s:>8d}")

    print(f"\n    Checks: sum w^2 = {R['ell']}, sum w*s = {R['ws_sum']} vs d^(k+1) = {R['dk1']}" +
          (" OK" if R['ws_sum']==R['dk1'] else " (gap due to non-semisimple kernel)"))

    print(f"\n  BRANCHING TO S_{k}")
    for a, b, w, s in R['irreps']:
        br = R['br'][(a,b)]
        bs = " + ".join(fpart(g) for g, _ in br)
        print(f"    {fbip(a,b)} (w={w}):  {bs}")

    nr = len(R['refined'])
    if nr <= 70:
        print(f"\n  REFINED SUB-BLOCKS ({nr} total)")
        print(f"    {'lambda':<22s} {'mu':<22s} {'gamma':<14s} {'n_g':>4s} {'old':>4s}")
        print(f"    {'-'*22} {'-'*22} {'-'*14} {'-'*4} {'-'*4}")
        for a1,b1,a2,b2,g,ng,old in R['refined']:
            print(f"    {fbip(a1,b1):<22s} {fbip(a2,b2):<22s} {fpart(g):<14s} {ng:>4d} {old:>4d}")
    else:
        print(f"\n  REFINED SUB-BLOCKS ({nr} total -- size distribution):")
        sizes = [ng for _,_,_,_,_,ng,_ in R['refined']]
        dist = sorted(Counter(sizes).items())
        for sz, cnt in dist:
            print(f"    size {sz}: {cnt} blocks")

    print(f"\n  SUMMARY")
    print(f"    PSD blocks:    {R['n_blk_old']:>8d} old  ->  {R['n_blk_new']:>8d} new")
    print(f"    Max block:     {R['mx_old']:>8d} old  ->  {R['mx_new']:>8d} new  "
          f"({R['max_w']}x{R['max_w']} -> {R['mx_new']}x{R['mx_new'] if R['mx_new']>0 else 0})")
    print(f"    PSD sq-entries:{R['psd_e_old']:>10d} old -> {R['psd_e_new']:>10d} new  "
          f"({R['psd_e_old']/R['psd_e_new']:.1f}x)" if R['psd_e_new'] else "")
    print(f"    PSD params:    {R['psd_p_old']:>10d} old -> {R['psd_p_new']:>10d} new  "
          f"({R['psd_p_old']/R['psd_p_new']:.1f}x)" if R['psd_p_new'] else "")


def summary_table(results):
    print(f"\n\n{'='*160}")
    print(f"  COMPREHENSIVE SUMMARY: S_k-INVARIANCE COMPLEXITY REDUCTION")
    print(f"  (walled Brauer algebra B_{{1,k}}(d), semisimple for d >= k+1)")
    print(f"{'='*160}")

    h = (f" {'d':>2s} {'k':>2s} {'ss':>2s}  "
         f"{'D':>14s}  {'ell':>8s}  {'#ir':>4s}  "
         f"{'m_old':>12s}  {'m_Sk':>12s}  {'red':>7s}  "
         f"{'#blk_o':>6s}  {'#blk_n':>6s}  "
         f"{'mx_o':>6s}  {'mx_n':>5s}  "
         f"{'PSD_o':>14s}  {'PSD_n':>12s}  {'PSDx':>7s}  "
         f"{'Par_o':>14s}  {'Par_n':>12s}  {'Parx':>7s}")
    print(h)
    print(' ' + '-'*158)

    for R in results:
        ss = 'Y' if R['semisimple'] else ' '
        rd = f"{R['m_old']/R['m_actual']:.1f}"
        pe = f"{R['psd_e_old']/R['psd_e_new']:.1f}" if R['psd_e_new'] else "inf"
        pp = f"{R['psd_p_old']/R['psd_p_new']:.1f}" if R['psd_p_new'] else "inf"
        print(f" {R['d']:>2d} {R['k']:>2d}  {ss:>1s}  "
              f"{R['D']:>14,d}  {R['ell']:>8,d}  {R['n_irr']:>4d}  "
              f"{R['m_old']:>12,d}  {R['m_actual']:>12,d}  {rd:>7s}  "
              f"{R['n_blk_old']:>6d}  {R['n_blk_new']:>6d}  "
              f"{R['mx_old']:>6d}  {R['mx_new']:>5d}  "
              f"{R['psd_e_old']:>14,d}  {R['psd_e_new']:>12,d}  {pe:>7s}  "
              f"{R['psd_p_old']:>14,d}  {R['psd_p_new']:>12,d}  {pp:>7s}")

    print(f"\n  Legend: ss = semisimple (d >= k+1)")
    print(f"         ell = dim(commutant algebra) = sum w_lam^2")
    print(f"         m_old = ell^2 = #SDP variables before S_k reduction")
    print(f"         m_Sk = sum n_gamma^2 = #SDP variables after S_k reduction")
    print(f"         red = m_old / m_Sk (variable reduction ratio)")
    print(f"         mx_o/mx_n = largest PSD block size (squared) before/after")
    print(f"         PSDx = ratio of sum of squared block sizes")
    print(f"         Parx = ratio of sum of triangular block parameters")

    # Scaling
    print(f"\n  SCALING ANALYSIS (PSD entry reduction factor by k, for each d)")
    print(f"  {'d|k':>5s}", end="")
    ks = sorted(set(R['k'] for R in results))
    for k in ks: print(f" {'k='+str(k):>10s}", end="")
    print()
    for d in sorted(set(R['d'] for R in results)):
        print(f"  {'d='+str(d):>5s}", end="")
        for k in ks:
            matches = [R for R in results if R['d']==d and R['k']==k]
            if matches:
                R = matches[0]
                r = R['psd_e_old']/R['psd_e_new'] if R['psd_e_new'] else float('inf')
                print(f" {r:>10.1f}", end="")
            else:
                print(f" {'--':>10s}", end="")
        print()

    # Max block reduction
    print(f"\n  MAX BLOCK SIZE REDUCTION (old -> new)")
    print(f"  {'d|k':>5s}", end="")
    for k in ks: print(f" {'k='+str(k):>12s}", end="")
    print()
    for d in sorted(set(R['d'] for R in results)):
        print(f"  {'d='+str(d):>5s}", end="")
        for k in ks:
            matches = [R for R in results if R['d']==d and R['k']==k]
            if matches:
                R = matches[0]
                print(f" {str(R['mx_old'])+'->'+str(R['mx_new']):>12s}", end="")
            else:
                print(f" {'--':>12s}", end="")
        print()

    # Generic vs actual
    print(f"\n  d-INDEPENDENT BURNSIDE (valid for d >= k+1) vs ACTUAL")
    for R in results:
        d, k = R['d'], R['k']
        a, g = R['m_actual'], R['m_gen']
        if a == g:
            print(f"    ({d},{k}): m_Sk = {a} = m_generic (semisimple)")
        else:
            print(f"    ({d},{k}): m_Sk = {a} < m_generic = {g} (non-semisimple, ratio {g/a:.2f})")

    # LaTeX table
    print(f"\n\n  LaTeX TABLE")
    print(r"  \begin{tabular}{cc|rrr|rrr|rr}")
    print(r"  \toprule")
    print(r"  $d$ & $k$ & $\ell$ & $m_{\text{old}}$ & $m_{S_k}$ "
          r"& \text{red.} & $b_{\max}^{\text{old}}$ & $b_{\max}^{\text{new}}$ "
          r"& \text{PSD red.} & \text{param red.} \\")
    print(r"  \midrule")
    prev_k = None
    for R in results:
        if prev_k is not None and R['k'] != prev_k:
            print(r"  \midrule")
        prev_k = R['k']
        red = R['m_old']/R['m_actual']
        pr = R['psd_e_old']/R['psd_e_new'] if R['psd_e_new'] else float('inf')
        pa = R['psd_p_old']/R['psd_p_new'] if R['psd_p_new'] else float('inf')
        ell_s = f"{R['ell']}"
        mo_s = f"{R['m_old']:,}"
        ms_s = f"{R['m_actual']:,}"
        print(f"  {R['d']} & {R['k']} & {ell_s} & {mo_s} & {ms_s} & "
              f"${red:.1f}\\times$ & {R['mx_old']} & {R['mx_new']} & "
              f"${pr:.1f}\\times$ & ${pa:.1f}\\times$ \\\\")
    print(r"  \bottomrule")
    print(r"  \end{tabular}")


# ======================================================================
if __name__ == '__main__':
    targets = [
        (2,2), (3,2),
        (2,3), (3,3),
        (2,4), (3,4), (4,4), (5,4),
        (2,5), (3,5), (4,5), (5,5),
        (3,6), (4,6), (5,6),
    ]

    print("Computing S_k-invariance reduction for all (d,k) targets...\n")
    results = []
    for d, k in targets:
        sys.stdout.write(f"  (d={d}, k={k})... "); sys.stdout.flush()
        R = compute(d, k)
        results.append(R)
        r = R['m_old']/R['m_actual']
        print(f"done  [ell={R['ell']}, m_old={R['m_old']:,}, m_Sk={R['m_actual']:,}, red={r:.1f}x]")

    for R in results:
        detail(R)

    summary_table(results)
