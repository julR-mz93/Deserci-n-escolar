#!/usr/bin/env python3
"""Portadas gráficas del informe (banda superior y pie)."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, Polygon

BASE = Path(__file__).resolve().parent.parent
FIG = BASE / "docs" / "figuras"
FIG.mkdir(parents=True, exist_ok=True)

NAVY = "#0F2A44"
BLUE = "#1F6FB2"
AQUA = "#7FD1E8"
GOLD = "#E9C46A"
WHITE = "#FFFFFF"

plt.rcParams.update({"font.family": "DejaVu Sans", "savefig.dpi": 300})


def banda() -> None:
    fig, ax = plt.subplots(figsize=(8.3, 2.5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 3)
    ax.axis("off")
    fig.patch.set_facecolor(NAVY)
    ax.set_facecolor(NAVY)

    for i in range(80):
        y = i * 3 / 80
        c = plt.cm.Blues(0.14 + 0.40 * i / 80)
        ax.axhspan(y, y + 3 / 80 + 0.01, color=c, alpha=0.6, zorder=0)

    rng = np.random.default_rng(11)
    pts = np.column_stack([rng.uniform(0.3, 9.7, 30), rng.uniform(0.25, 2.75, 30)])
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            if np.hypot(*(pts[i] - pts[j])) < 1.15:
                ax.plot([pts[i, 0], pts[j, 0]], [pts[i, 1], pts[j, 1]],
                        color=AQUA, alpha=0.16, linewidth=0.7, zorder=1)
    ax.scatter(pts[:, 0], pts[:, 1], s=9, color=AQUA, alpha=0.55,
               edgecolors="none", zorder=2)

    # Birrete estilizado
    cx, cy = 8.35, 1.65
    gorro = Polygon([(cx - 0.95, cy + 0.10), (cx, cy + 0.62), (cx + 0.95, cy + 0.10),
                     (cx, cy - 0.42)], closed=True, facecolor="none",
                    edgecolor=AQUA, linewidth=1.6, alpha=0.95, zorder=4)
    ax.add_patch(gorro)
    ax.add_patch(FancyBboxPatch((cx - 0.34, cy - 0.28), 0.68, 0.30,
                                boxstyle="round,pad=0.01,rounding_size=0.05",
                                facecolor="none", edgecolor=AQUA, linewidth=1.1,
                                alpha=0.85, zorder=4))
    ax.plot([cx + 0.88, cx + 0.88], [cy + 0.08, cy - 0.42], color=AQUA,
            linewidth=1.1, alpha=0.85, zorder=4)
    ax.add_patch(Polygon([(cx + 0.88, cy - 0.42), (cx + 0.80, cy - 0.62),
                          (cx + 0.96, cy - 0.62)], closed=True, facecolor=GOLD,
                         edgecolor="none", alpha=0.9, zorder=5))

    fig.subplots_adjust(0, 0, 1, 1)
    fig.savefig(FIG / "portada_banda.png", facecolor=NAVY)
    plt.close(fig)


def pie() -> None:
    fig, ax = plt.subplots(figsize=(8.3, 1.3))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 1.5)
    ax.axis("off")
    fig.patch.set_facecolor(WHITE)
    ax.set_facecolor(WHITE)
    x = np.linspace(0, 10, 400)
    for off, amp, alpha, lw, color in [(0.22, 0.09, 0.30, 1.2, BLUE),
                                       (0.34, 0.06, 0.20, 1.0, AQUA),
                                       (0.46, 0.04, 0.14, 0.8, BLUE)]:
        ax.plot(x, off + amp * np.sin(0.9 * x), color=color, alpha=alpha, linewidth=lw)
    ax.axhline(0.06, color=GOLD, linewidth=2.2, alpha=0.9)
    fig.subplots_adjust(0, 0, 1, 1)
    fig.savefig(FIG / "portada_pie.png", facecolor=WHITE)
    plt.close(fig)


if __name__ == "__main__":
    banda()
    pie()
    print("portadas listas")
