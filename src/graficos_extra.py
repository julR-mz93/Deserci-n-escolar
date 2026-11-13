#!/usr/bin/env python3
"""
Recursos gráficos adicionales para la Actividad 3.2.1.

Genera:
  docs/figuras/portada_hero.png    · banda principal de portada
  docs/figuras/hero_portada_slide.png · fondo de la portada de la presentación
  docs/figuras/hero_fase1.png      · banda compacta para el reporte de una página
  docs/figuras/qr_repo.png         · código QR del repositorio
  docs/figuras/demo_app.gif        · demostración animada de la aplicación
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle
from PIL import Image

BASE = Path(__file__).resolve().parent.parent
FIG = BASE / "docs" / "figuras"
FIG.mkdir(parents=True, exist_ok=True)

NAVY = "#071A2F"
NAVY_2 = "#0F2A44"
BLUE = "#1F6FB2"
AQUA = "#7FD1E8"
GOLD = "#E9C46A"
WHITE = "#FFFFFF"
REPO = "https://github.com/julR-mz93/Fundamentos-de-Inteligencia-Artificial"


def _gradiente(ax, xlim=(0, 10), ylim=(0, 5), c1=NAVY, c2=BLUE) -> None:
    """Fondo con degradado diagonal suave."""
    n = 700
    x = np.linspace(0, 1, n)
    y = np.linspace(0, 1, n)
    xx, yy = np.meshgrid(x, y)
    z = np.clip(0.72 * xx + 0.35 * yy, 0, 1)
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("hero", [c1, c2])
    ax.imshow(z, extent=(*xlim, *ylim), origin="lower", aspect="auto",
              cmap=cmap, alpha=1.0, zorder=0)


def _constelacion(ax, n=46, seed=7, xlim=(0, 10), ylim=(0, 5)) -> None:
    rng = np.random.default_rng(seed)
    pts = np.column_stack([
        rng.uniform(xlim[0] + 0.2, xlim[1] - 0.2, n),
        rng.uniform(ylim[0] + 0.15, ylim[1] - 0.15, n),
    ])
    for i in range(n):
        for j in range(i + 1, n):
            d = float(np.hypot(*(pts[i] - pts[j])))
            if d < 0.95:
                ax.plot([pts[i, 0], pts[j, 0]], [pts[i, 1], pts[j, 1]],
                        color=AQUA, alpha=0.13, lw=0.6, zorder=1)
    ax.scatter(pts[:, 0], pts[:, 1], s=7, color=AQUA, alpha=0.42,
               edgecolors="none", zorder=2)


def _curva_roc(ax, x0=5.55, y0=0.55, w=3.55, h=3.05) -> None:
    x = np.linspace(0.02, 0.98, 300)
    y = 1 - (1 - x) ** 2.15
    xs = x0 + x * w
    ys = y0 + y * h
    for lw, alpha in ((7.5, 0.06), (5.0, 0.10), (3.0, 0.18)):
        ax.plot(xs, ys, color=GOLD, lw=lw, alpha=alpha, solid_capstyle="round", zorder=3)
    ax.plot(xs, ys, color=GOLD, lw=2.0, alpha=0.98, solid_capstyle="round", zorder=4)
    ax.plot([x0, x0 + w], [y0, y0], color=WHITE, lw=0.9, alpha=0.28, ls="--", zorder=3)
    ax.plot([x0 + w, x0 + w], [y0, y0 + h], color=WHITE, lw=0.9, alpha=0.28,
            ls="--", zorder=3)
    ax.scatter([x0 + w * 0.595], [y0 + (1 - (1 - 0.595) ** 2.15) * h],
               s=42, color=WHITE, edgecolors=GOLD, linewidths=2.2, zorder=5)


def hero() -> None:
    """Banda principal de la portada del informe (formato más alto y aireado)."""
    fig, ax = plt.subplots(figsize=(6.5, 4.3))
    fig.subplots_adjust(0, 0, 1, 1)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.6)
    ax.axis("off")
    _gradiente(ax, ylim=(0, 6.6))

    # Halo y anillos concéntricos
    ax.add_patch(Circle((8.35, 2.95), 3.7, color=AQUA, alpha=0.035, lw=0, zorder=0))
    for r, a in ((3.05, 0.06), (2.35, 0.08), (1.7, 0.10), (1.05, 0.13)):
        ax.add_patch(Circle((8.35, 2.95), r, fill=False, edgecolor=AQUA,
                            lw=1.0, alpha=a, zorder=1))
    _constelacion(ax, n=56, seed=13, ylim=(0, 6.6))

    # Retícula de datos tenue en la zona izquierda
    gx, gy = np.meshgrid(np.linspace(0.55, 4.55, 17),
                         np.linspace(2.05, 6.05, 11))
    ax.scatter(gx.ravel(), gy.ravel(), s=3.2, color=WHITE, alpha=0.10,
               edgecolors="none", zorder=1)

    _curva_roc(ax, x0=5.35, y0=0.85, w=3.95, h=3.9)

    # Puntos de la curva con brillo
    x = np.linspace(0.08, 0.92, 9)
    y = 1 - (1 - x) ** 2.15
    ax.scatter(5.35 + x * 3.95, 0.85 + y * 3.9, s=13, color=WHITE,
               alpha=0.70, edgecolors="none", zorder=4)

    # Línea inferior dorada
    ax.axhline(0.07, color=GOLD, lw=2.4, alpha=0.95, zorder=6)
    ax.axhline(0.15, color=WHITE, lw=0.6, alpha=0.10, zorder=6)

    # Barras decorativas (izquierda)
    for i, h in enumerate([0.48, 0.70, 0.55, 0.94, 0.80, 1.16]):
        ax.add_patch(plt.Rectangle((0.46 + i * 0.19, 0.74), 0.10, h,
                                   facecolor=WHITE, alpha=0.10 + i * 0.025,
                                   edgecolor="none", zorder=3))

    fig.savefig(FIG / "portada_hero.png", dpi=300, facecolor=NAVY)
    plt.close(fig)


def hero_fase1() -> None:
    fig, ax = plt.subplots(figsize=(6.5, 1.5))
    fig.subplots_adjust(0, 0, 1, 1)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 2.35)
    ax.axis("off")
    _gradiente(ax, ylim=(0, 2.75))

    for r, a in ((1.30, 0.06), (0.96, 0.08), (0.62, 0.10)):
        ax.add_patch(Circle((8.75, 1.05), r, fill=False, edgecolor=AQUA,
                            lw=1.0, alpha=a, zorder=1))
    _constelacion(ax, n=30, seed=5, ylim=(0, 2.35))
    _curva_roc(ax, x0=6.05, y0=0.26, w=2.85, h=1.35)

    ax.axhline(0.055, color=GOLD, lw=2.0, alpha=0.95, zorder=6)
    fig.savefig(FIG / "hero_fase1.png", dpi=300, facecolor=NAVY)
    plt.close(fig)


def hero_slide() -> None:
    """Banda panorámica para las diapositivas de apertura y cierre."""
    fig, ax = plt.subplots(figsize=(13.333, 2.45))
    fig.subplots_adjust(0, 0, 1, 1)
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 3.68)
    ax.axis("off")
    _gradiente(ax, xlim=(0, 20), ylim=(0, 3.68))

    for r, a in ((2.15, 0.05), (1.6, 0.07), (1.05, 0.09)):
        ax.add_patch(Circle((17.2, 1.7), r, fill=False, edgecolor=AQUA,
                            lw=1.0, alpha=a, zorder=1))
    _constelacion(ax, n=54, seed=9, xlim=(0, 20), ylim=(0, 3.68))
    _curva_roc(ax, x0=12.1, y0=0.32, w=6.2, h=2.55)
    ax.axhline(0.055, color=GOLD, lw=2.1, alpha=0.95, zorder=6)
    fig.savefig(FIG / "hero_slide.png", dpi=220, facecolor=NAVY)
    plt.close(fig)


def hero_portada_slide() -> None:
    """Fondo completo de la portada de la presentación (16:9)."""
    fig, ax = plt.subplots(figsize=(13.333, 7.5))
    fig.subplots_adjust(0, 0, 1, 1)
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 11.25)
    ax.axis("off")
    _gradiente(ax, xlim=(0, 20), ylim=(0, 11.25), c1=NAVY, c2="#17466F")

    # Halo y anillos en el tercio derecho
    ax.add_patch(Circle((16.3, 5.3), 5.1, color=AQUA, alpha=0.035, lw=0, zorder=0))
    for r, a in ((4.45, 0.05), (3.45, 0.07), (2.45, 0.09), (1.5, 0.12)):
        ax.add_patch(Circle((16.3, 5.3), r, fill=False, edgecolor=AQUA,
                            lw=1.0, alpha=a, zorder=1))
    _constelacion(ax, n=62, seed=9, xlim=(0, 20), ylim=(0, 11.25))

    # Retícula tenue al pie de la zona gráfica
    gx, gy = np.meshgrid(np.linspace(10.4, 19.4, 22),
                         np.linspace(0.55, 2.7, 7))
    ax.scatter(gx.ravel(), gy.ravel(), s=3.4, color=WHITE, alpha=0.08,
               edgecolors="none", zorder=1)

    _curva_roc(ax, x0=11.25, y0=1.35, w=7.95, h=5.55)

    # Puntos de la curva con brillo
    x = np.linspace(0.08, 0.92, 11)
    y = 1 - (1 - x) ** 2.15
    ax.scatter(11.25 + x * 7.95, 1.35 + y * 5.55, s=15, color=WHITE,
               alpha=0.70, edgecolors="none", zorder=4)

    ax.axhline(0.10, color=GOLD, lw=2.6, alpha=0.95, zorder=6)
    fig.savefig(FIG / "hero_portada_slide.png", dpi=220, facecolor=NAVY)
    plt.close(fig)


def qr() -> None:
    import qrcode
    from qrcode.constants import ERROR_CORRECT_M

    q = qrcode.QRCode(version=None, error_correction=ERROR_CORRECT_M,
                      box_size=12, border=2)
    q.add_data(REPO)
    q.make(fit=True)
    img = q.make_image(fill_color=NAVY_2, back_color=WHITE).convert("RGB")
    img.save(FIG / "qr_repo.png")
    print("QR:", img.size)


def demo() -> None:
    """GIF con transiciones suaves entre las tres pantallas de la app."""
    rutas = [FIG / "fig_app_prediccion.png",
             FIG / "fig_app_evaluacion.png",
             FIG / "fig_app_inicio.png"]
    if not all(p.exists() for p in rutas):
        print("Faltan capturas de la app; se omite el GIF.")
        return

    ancho, alto = 1200, 760
    base = []
    for p in rutas:
        im = Image.open(p).convert("RGB")
        # recorte central con la proporción deseada
        rel = im.width / im.height
        objetivo = ancho / alto
        if rel > objetivo:
            nuevo = (int(im.height * objetivo), im.height)
            x0 = (im.width - nuevo[0]) // 2
            im = im.crop((x0, 0, x0 + nuevo[0], im.height))
        else:
            nuevo = (im.width, int(im.width / objetivo))
            y0 = (im.height - nuevo[1]) // 2
            im = im.crop((0, y0, im.width, y0 + nuevo[1]))
        base.append(im.resize((ancho, alto), Image.LANCZOS))

    marcos, duraciones = [], []

    def marco(img: Image.Image, etiqueta: int) -> Image.Image:
        # barra dorada inferior que avanza según la pantalla
        out = img.copy()
        from PIL import ImageDraw
        d = ImageDraw.Draw(out)
        d.rectangle([0, alto - 7, ancho, alto], fill="#0F2A44")
        d.rectangle([0, alto - 7, int(ancho * (etiqueta + 1) / 3), alto], fill="#E9C46A")
        return out

    for i, img in enumerate(base):
        f = marco(img, i)
        for _ in range(6):
            marcos.append(f)
            duraciones.append(130)

        if i < len(base) - 1:
            for k in range(1, 6):
                mezcla = Image.blend(img, base[i + 1], k / 6)
                marcos.append(marco(mezcla, i))
                duraciones.append(80)

    marcos[0].save(FIG / "demo_app.gif", save_all=True, append_images=marcos[1:],
                   duration=duraciones, loop=0, optimize=True, disposal=2)
    print("GIF:", (FIG / "demo_app.gif").stat().st_size // 1024, "KB")


if __name__ == "__main__":
    hero()
    hero_fase1()
    hero_slide()
    hero_portada_slide()
    qr()
    demo()
    print("Recursos gráficos listos en", FIG)
