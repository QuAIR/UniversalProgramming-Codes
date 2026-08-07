from __future__ import annotations

import csv
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "universalpga-mplconfig"))

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D


DATA = ROOT / "fig3_kcopy_decay_data.csv"
OUT = Path(os.environ.get("FIGURES_OUTPUT_DIR", ROOT / "generated")) / "fig3_kcopy_decay"


mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "font.size": 8.8,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "axes.linewidth": 0.8,
        "axes.labelsize": 10.8,
        "xtick.labelsize": 9.4,
        "ytick.labelsize": 9.4,
        "legend.frameon": False,
        "lines.linewidth": 1.45,
        "mathtext.fontset": "dejavusans",
    }
)


PALETTE = {
    2: "#3B6FB6",
    3: "#2A9D8F",
    4: "#7E5AA6",
    5: "#D28A2E",
}


def load_rows() -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    with DATA.open(newline="") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                {
                    "d": float(row["d"]),
                    "k": float(row["k"]),
                    "nu": float(row["nu"]),
                }
            )
    return rows


def save_pub(fig, prefix: Path, dpi: int = 600) -> None:
    fig.savefig(prefix.with_suffix(".png"), dpi=dpi, bbox_inches="tight")
    fig.savefig(prefix.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(prefix.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(prefix.with_suffix(".tiff"), dpi=dpi, bbox_inches="tight")


def fit_inverse_k(ks: np.ndarray, nus: np.ndarray) -> tuple[float, float]:
    """Fit nu_k - 1 = a/k + b/k^2, fixing the physical limit at 1."""
    design = np.column_stack([1.0 / ks, 1.0 / (ks**2)])
    a, b = np.linalg.lstsq(design, nus - 1.0, rcond=None)[0]
    return float(a), float(b)


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rows = load_rows()
    dims = sorted({int(r["d"]) for r in rows})

    fig, ax = plt.subplots(figsize=(3.72, 2.56))
    legend_by_dim: dict[int, Line2D] = {}

    for d in dims:
        subset = sorted((r for r in rows if int(r["d"]) == d), key=lambda r: r["k"])
        ks = np.array([r["k"] for r in subset])
        nus = np.array([r["nu"] for r in subset])
        color = PALETTE[d]
        fit_a, fit_b = fit_inverse_k(ks, nus)

        ax.plot(
            ks,
            nus,
            marker="o",
            markersize=5.1,
            color=color,
            markerfacecolor=color,
            markeredgecolor="white",
            markeredgewidth=0.55,
            zorder=3,
        )

        if max(ks) < 5:
            fit_k = np.linspace(max(ks), 5.0, 80)
            fit_nu = 1.0 + fit_a / fit_k + fit_b / (fit_k**2)
            ax.plot(
                fit_k,
                fit_nu,
                color=color,
                linestyle=(0, (3, 2)),
                linewidth=1.3,
                alpha=0.78,
                zorder=2,
            )
            missing_ks = np.arange(int(max(ks)) + 1, 6, dtype=float)
            missing_nus = 1.0 + fit_a / missing_ks + fit_b / (missing_ks**2)
            ax.plot(
                missing_ks,
                missing_nus,
                marker="o",
                markersize=5.1,
                color=color,
                markerfacecolor="white",
                markeredgecolor=color,
                markeredgewidth=0.85,
                linestyle="None",
                zorder=4,
            )

        legend_by_dim[d] = Line2D(
            [0],
            [0],
            color=color,
            marker="o",
            markersize=4.9,
            linewidth=1.45,
            label=rf"$d={d}$",
        )

    ax.axhline(1.0, color="#4A4A4A", linestyle=(0, (2.5, 2)), linewidth=0.9, zorder=1)
    limit_handle = Line2D(
        [0],
        [0],
        color="#4A4A4A",
        linestyle=(0, (2.5, 2)),
        linewidth=1.0,
        label="physical limit",
    )

    ax.set_xlim(0.8, 5.2)
    ax.set_ylim(0.0, 51.0)
    ax.set_xticks([1, 2, 3, 4, 5])
    ax.set_yticks([0, 10, 20, 30, 40, 50])
    ax.set_xlabel(r"copy number $k$")
    ax.set_ylabel(r"$k$-copy overhead $\nu_k$")
    ax.grid(axis="y", color="#E4E4E4", linewidth=0.75)
    dim_legend = ax.legend(
        handles=[legend_by_dim[d] for d in [2, 4, 3, 5]],
        title=r"fit: $a_d/k+b_d/k^2$",
        loc="upper right",
        ncol=2,
        handlelength=1.25,
        handletextpad=0.35,
        columnspacing=0.75,
        borderaxespad=0.35,
        labelspacing=0.22,
        title_fontsize=8.4,
        fontsize=8.4,
    )
    ax.add_artist(dim_legend)
    ax.legend(
        handles=[limit_handle],
        loc="upper right",
        bbox_to_anchor=(0.992, 0.735),
        handlelength=1.45,
        handletextpad=0.42,
        borderaxespad=0.35,
        fontsize=8.1,
    )

    save_pub(fig, OUT)


if __name__ == "__main__":
    main()
