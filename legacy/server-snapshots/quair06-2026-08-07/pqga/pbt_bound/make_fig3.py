"""
Rebuild Fig. 3 of arxiv.tex as a CERTIFIED two-sided figure.

Panel (a): certified sandwich.  For every (d,k),
      nu_k^SDP  <=  nu_k(CPTP_d)  <=  ||D_{1/eta_{k,d}}||_diamond
   - lower: sampled-constraint reduced SDP is a RELAXATION (fewer equality
     constraints => larger feasible set => smaller minimum), hence a rigorous
     lower bound on nu_k.
   - upper: exact finite-k standard-PBT fidelity fed into the exact identity
     ||D_t||_diamond = 1 + 2(1-d^-2)(t-1).  No asymptotics used.
   - k=1 lower bounds are the closed-form optima 2d^2-3+2/d^2 (Thm 1), which
     are exact; the PBT upper bound is +infinity there (one port = completely
     depolarizing), so the k=1 column is where the construction of Thm 4 gives
     nothing while exact programming is already finite.

Panel (b): pre-asymptotic collapse.  R := k(nu_k-1)/(d^2-1) plotted against
   the PBT scaling variable x = k/d^2.  Theorem 4 predicts R -> 1/2.
"""

import math
import os
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pbt_bound import nu_upper  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fig3_kcopy_certified.png")

# ----------------------------------------------------------------- input data
# Sampled reduced-SDP optima = rigorous LOWER bounds on nu_k(CPTP_d).
# k=1 entries are the closed-form exact optima 2d^2-3+2/d^2.
NU_LOWER = {
    # d=2, k<=3 additionally reproduced by an exact-span (unsampled) SDP to 3e-8
    2: {1: 5.500000000000, 2: 2.713330261060, 3: 1.888291441276,
        4: 1.529423184103, 5: 1.350907061612},
    # d=3, k=4: two independent runs give 3.619643 and 3.619724; the smaller
    # (more conservative) value is used.
    3: {1: 15.222222222222, 2: 7.456449630161, 3: 4.882170484565,
        4: 3.619643423467},
    4: {1: 29.125000000000, 2: 14.366215273519, 3: 9.453845038152,
        4: 7.003852837190},
    5: {1: 47.080000000000, 2: 23.324401999823, 3: 15.410364254085},
}
DIMS = [2, 3, 4, 5]
COLORS = {2: "#3b75af", 3: "#12a08c", 4: "#7e62a3", 5: "#d9902a"}

# k=1 closed form check
for d in DIMS:
    assert abs(NU_LOWER[d][1] - (2 * d**2 - 3 + 2 / d**2)) < 5e-4, d


def nu_upper_eff(k, d):
    """Effective certified upper bound: min over j<=k of the PBT bound,
    using copy monotonicity nu_k <= nu_j for k >= j."""
    return min(nu_upper(j, d) for j in range(1, k + 1))


# ------------------------------------------------------------------- plotting
mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans"],
    "font.size": 8,
    "axes.labelsize": 9,
    "axes.linewidth": 0.8,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 7,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.top": True,
    "ytick.right": True,
    "savefig.dpi": 600,
})

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(3.4, 4.35))

# ---------------------------------------------------------------- panel (a)
for d in DIMS:
    ks = sorted(NU_LOWER[d])
    lo = np.array([NU_LOWER[d][k] - 1.0 for k in ks])
    up = np.array([nu_upper_eff(k, d) - 1.0 for k in ks])
    c = COLORS[d]

    fin = np.isfinite(up)
    if fin.any():
        ax1.fill_between(np.array(ks)[fin], lo[fin], up[fin],
                         color=c, alpha=0.20, linewidth=0)
        ax1.plot(np.array(ks)[fin], up[fin], ls="--", lw=1.0, color=c,
                 marker="s", ms=3.4, mfc="white", mew=0.9, zorder=3)
    ax1.plot(ks, lo, ls="-", lw=1.2, color=c, marker="o", ms=4.0,
             zorder=4, label=rf"$d={d}$")
    # k=1 is the closed-form exact optimum of Thm 1
    ax1.plot([1], [lo[0]], marker="*", ms=8.5, color=c, mec="k", mew=0.5,
             zorder=5, ls="none")

ax1.text(1.35, 100.0, r"upper bound $=\infty$ at $k=1$",
         fontsize=6.8, color="0.25", va="center", ha="left")

# neutral slope reference in the empty upper-right corner
kk = np.array([3.8, 6.6])
ax1.plot(kk, 132.0 / kk, ls=":", lw=1.0, color="0.35", zorder=1)
ax1.text(5.0, 21.0, r"$\propto k^{-1}$", fontsize=7.2, color="0.35",
         ha="center", va="top")

ax1.set_xscale("log")
ax1.set_yscale("log")
ax1.set_xticks([1, 2, 3, 4, 5])
ax1.set_xticklabels(["1", "2", "3", "4", "5"])
ax1.set_xticks([], minor=True)
ax1.set_xlim(0.90, 7.0)
ax1.set_ylim(0.26, 150)
ax1.set_xlabel(r"copy number $k$")
ax1.set_ylabel(r"excess overhead $\nu_k-1$")
ax1.legend(loc="lower left", ncol=2, frameon=False, handlelength=1.6,
           columnspacing=1.0, borderpad=0.2, labelspacing=0.25)
ax1.text(0.02, 0.965, "(a)", transform=ax1.transAxes, fontsize=9,
         fontweight="bold", va="top")

# ---------------------------------------------------------------- panel (b)
for d in DIMS:
    ks = np.array(sorted(NU_LOWER[d]), dtype=float)
    R = np.array([k * (NU_LOWER[d][int(k)] - 1.0) / (d**2 - 1) for k in ks])
    ax2.plot(ks / d**2, R, ls="-", lw=1.2, color=COLORS[d], marker="o",
             ms=4.0, label=rf"$d={d}$", zorder=4)

ax2.axhline(0.5, ls="--", lw=1.0, color="0.3", zorder=1)
ax2.text(0.042, 0.545, r"asymptotic value $1/2$", fontsize=7, color="0.3",
         va="bottom")
ax2.text(0.037, 1.05, "SDP lower bounds", fontsize=6.8, color="0.35",
         ha="left", va="center")

ax2.set_xscale("log")
ax2.set_xlim(0.032, 1.7)
ax2.set_ylim(0.40, 2.08)
ax2.set_xticks([0.05, 0.1, 0.2, 0.5, 1.0])
ax2.set_xticklabels(["0.05", "0.1", "0.2", "0.5", "1"])
ax2.set_xticks([], minor=True)
ax2.set_xlabel(r"rescaled copy number $k/d^{2}$")
ax2.set_ylabel(r"$k\,(\nu_k-1)/(d^{2}-1)$")
ax2.legend(loc="upper right", ncol=2, frameon=False, handlelength=1.6,
           columnspacing=1.0, borderpad=0.2, labelspacing=0.25)
ax2.text(0.02, 0.965, "(b)", transform=ax2.transAxes, fontsize=9,
         fontweight="bold", va="top")

fig.tight_layout(pad=0.35, h_pad=1.1)
fig.savefig(OUT)
print("wrote", OUT)

# ------------------------------------------------------------ printed summary
print("\n{:>3} {:>3} {:>12} {:>12} {:>8} {:>8} {:>8}".format(
    "d", "k", "lower", "upper", "UB/LB", "x=k/d^2", "R_low"))
for d in DIMS:
    for k in sorted(NU_LOWER[d]):
        lo = NU_LOWER[d][k]
        up = nu_upper_eff(k, d)
        R = k * (lo - 1) / (d**2 - 1)
        ustr = "inf" if math.isinf(up) else f"{up:12.6f}"
        rat = "--" if math.isinf(up) else f"{(up - 1) / (lo - 1):8.3f}"
        print(f"{d:>3} {k:>3} {lo:>12.6f} {ustr:>12} {rat:>8} "
              f"{k / d**2:>8.3f} {R:>8.3f}")

# --------------------------------------------- collapse diagnostic (panel b)
# Pool all (x, R) points with d >= 3, sort by x, and measure how far each point
# sits from the curve interpolated through the *other* dimensions.  Then do the
# same for d = 2 against the pooled d >= 3 curve.
pts = []
for d in DIMS:
    for k in sorted(NU_LOWER[d]):
        pts.append((k / d**2, k * (NU_LOWER[d][k] - 1) / (d**2 - 1), d, k))

print("\ncollapse diagnostic: deviation from the curve through OTHER dimensions")
worst3 = 0.0
for x, R, d, k in sorted(pts):
    others = sorted((xx, RR) for xx, RR, dd, _ in pts if dd != d and dd >= 3)
    xs = [p[0] for p in others]
    if not (xs[0] <= x <= xs[-1]):
        continue                       # no interpolation available
    Ri = np.interp(np.log(x), np.log(xs), [p[1] for p in others])
    dev = (R - Ri) / Ri
    tag = "  <- d=2" if d == 2 else ""
    if d >= 3:
        worst3 = max(worst3, abs(dev))
    print(f"  d={d} k={k}  x={x:.3f}  R={R:.3f}  interp={Ri:.3f}  "
          f"dev={100*dev:+.1f}%{tag}")
print(f"  worst deviation among d>=3: {100*worst3:.1f}%")
