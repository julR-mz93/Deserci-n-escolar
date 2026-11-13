#!/usr/bin/env python3
"""
Genera todas las figuras del proyecto de deserción escolar.

Salida: docs/figuras/*.png (300 dpi) y resultados auxiliares en results/.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from sklearn.inspection import permutation_importance
from sklearn.metrics import (confusion_matrix, precision_recall_curve,
                             roc_curve, auc)
from sklearn.model_selection import train_test_split

import pipeline as P

FIG = P.BASE / "docs" / "figuras"
RES = P.BASE / "results"
FIG.mkdir(parents=True, exist_ok=True)

NAVY, BLUE, ORANGE = "#0F2A44", "#1F6FB2", "#D9782D"
GOLD, GREEN, RED, GRAY = "#E9C46A", "#2E8B57", "#C0392B", "#6B7A8A"
GRID = "#DDE5EC"
PALETA = [BLUE, ORANGE, GREEN, RED, GOLD, "#7B5EA7", "#2A9D8F"]

plt.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 300, "font.family": "DejaVu Sans",
    "font.size": 9, "axes.titlesize": 11, "axes.titleweight": "bold",
    "axes.titlecolor": NAVY, "axes.labelcolor": NAVY, "text.color": NAVY,
    "xtick.color": GRAY, "ytick.color": GRAY,
    "axes.edgecolor": "#B9C7D4", "axes.linewidth": 0.8,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.7,
    "axes.axisbelow": True, "legend.frameon": False,
    "figure.facecolor": "white", "savefig.facecolor": "white",
})


def guardar(fig, nombre, titulo=None):
    if titulo:
        fig.suptitle(titulo, fontsize=12.5, fontweight="bold", color=NAVY,
                     x=0.012, ha="left", y=0.985)
    fig.savefig(FIG / nombre, bbox_inches="tight", pad_inches=0.18)
    plt.close(fig)
    print("  ·", nombre)


def sin_grid(ax, ejes=("x",)):
    for e in ejes:
        ax.grid(axis=e, visible=False)


# ---------------------------------------------------------------------------
# EDA
# ---------------------------------------------------------------------------
def fig_eda(df: pd.DataFrame) -> None:
    # 1. Distribución de la variable objetivo
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.4))
    orden = ["Graduate", "Enrolled", "Dropout"]
    colores = [GREEN, GOLD, RED]
    conteo = df["Target"].value_counts().reindex(orden)
    axes[0].bar(["Graduado", "Inscrito", "Desertor"], conteo.values, color=colores,
                width=0.62, edgecolor="white")
    for i, v in enumerate(conteo.values):
        axes[0].text(i, v + 40, f"{v}\n({v/len(df)*100:.1f} %)", ha="center",
                     fontsize=8.6, color=NAVY, fontweight="bold")
    axes[0].set_ylim(0, conteo.max() * 1.22)
    axes[0].set_ylabel("Estudiantes")
    axes[0].set_title("(a) Etiqueta original (3 clases)")
    sin_grid(axes[0], ("x",))

    b = df["desertor"].value_counts().sort_index()
    axes[1].bar(["No desertor\n(graduado o inscrito)", "Desertor"],
                b.values, color=[BLUE, RED], width=0.55, edgecolor="white")
    for i, v in enumerate(b.values):
        axes[1].text(i, v + 40, f"{v}\n({v/len(df)*100:.1f} %)", ha="center",
                     fontsize=8.6, color=NAVY, fontweight="bold")
    axes[1].set_ylim(0, b.max() * 1.22)
    axes[1].set_ylabel("Estudiantes")
    axes[1].set_title("(b) Etiqueta binaria del proyecto")
    sin_grid(axes[1], ("x",))
    guardar(fig, "fig_01_distribucion_objetivo.png")

    # 2. Histogramas de variables clave
    claves = [
        ("Age at enrollment", "Edad al ingresar (años)"),
        ("Admission grade", "Nota de admisión"),
        ("tasa_aprobacion_1s", "Tasa de aprobación 1.er semestre"),
        ("promedio_notas", "Promedio de calificaciones"),
        ("Curricular units 1st sem (enrolled)", "Unidades inscritas 1.er sem."),
        ("Curricular units 2nd sem (approved)", "Unidades aprobadas 2.º sem."),
    ]
    fig, axes = plt.subplots(2, 3, figsize=(11, 5.6))
    for ax, (col, titulo) in zip(axes.ravel(), claves):
        for valor, color, etiqueta in [(0, BLUE, "No desertor"),
                                       (1, RED, "Desertor")]:
            ax.hist(df.loc[df.desertor == valor, col], bins=22, alpha=0.55,
                    color=color, label=etiqueta, density=True, edgecolor="white",
                    linewidth=0.4)
        ax.set_title(titulo, fontsize=9.5)
        ax.set_ylabel("Densidad")
        sin_grid(ax, ("x",))
    axes[0, 0].legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    guardar(fig, "fig_02_histogramas.png")

    # 3. Boxplots comparativos
    fig, axes = plt.subplots(1, 4, figsize=(11, 3.4))
    for ax, (col, titulo) in zip(axes, [
        ("Age at enrollment", "Edad al ingresar"),
        ("Admission grade", "Nota de admisión"),
        ("tasa_aprobacion_1s", "Tasa aprobación 1.er sem."),
        ("promedio_notas", "Promedio de notas"),
    ]):
        datos = [df.loc[df.desertor == v, col].dropna() for v in (0, 1)]
        bp = ax.boxplot(datos, tick_labels=["No\ndesertor", "Desertor"], patch_artist=True,
                        widths=0.55, medianprops=dict(color=NAVY, linewidth=1.4),
                        flierprops=dict(marker="o", markersize=2.2, alpha=0.35,
                                        markerfacecolor=GRAY, markeredgecolor="none"))
        for patch, color in zip(bp["boxes"], [BLUE, RED]):
            patch.set_facecolor(color)
            patch.set_alpha(0.55)
            patch.set_edgecolor(color)
        ax.set_title(titulo, fontsize=9.3)
        sin_grid(ax, ("x",))
    fig.tight_layout()
    guardar(fig, "fig_03_boxplots.png")

    # 4. Mapa de correlación
    num = ["Age at enrollment", "Admission grade", "Previous qualification (grade)",
           "tasa_aprobacion_1s", "tasa_aprobacion_2s", "promedio_notas",
           "delta_aprobacion", "Unemployment rate", "Inflation rate", "GDP",
           "desertor"]
    etiquetas = ["Edad", "Nota adm.", "Nota previa", "Tasa 1.er sem.",
                 "Tasa 2.º sem.", "Promedio", "Δ aprobación", "Desempleo",
                 "Inflación", "PIB", "Deserción"]
    corr = df[num].corr()
    fig, ax = plt.subplots(figsize=(7.4, 6.2))
    im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(num)), etiquetas, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(num)), etiquetas, fontsize=8)
    for i in range(len(num)):
        for j in range(len(num)):
            v = corr.iloc[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6.6,
                    color="white" if abs(v) > 0.55 else NAVY)
    cb = fig.colorbar(im, ax=ax, shrink=0.82, pad=0.02)
    cb.set_label("Coeficiente de Pearson", fontsize=8)
    cb.ax.tick_params(labelsize=7)
    ax.grid(False)
    guardar(fig, "fig_04_correlacion.png")

    # 5. Tasa de deserción por subgrupo
    grupos = []
    for col, mapa, nombre in [
        ("Scholarship holder", {0: "Sin beca", 1: "Con beca"}, "Beca"),
        ("Debtor", {0: "Sin deuda", 1: "Con deuda"}, "Deuda"),
        ("Gender", {0: "Hombre", 1: "Mujer"}, "Sexo"),
        ("Tuition fees up to date", {0: "Adeudo", 1: "Al corriente"}, "Colegiatura"),
    ]:
        for v, lab in mapa.items():
            grupos.append((f"{nombre}: {lab}",
                           df.loc[df[col] == v, "desertor"].mean() * 100))
    for lab, (lo, hi) in {"≤ 20 años": (0, 20), "21–25 años": (21, 25),
                          "> 25 años": (26, 99)}.items():
        g = df[(df["Age at enrollment"] >= lo) & (df["Age at enrollment"] <= hi)]
        grupos.append((f"Edad: {lab}", g["desertor"].mean() * 100))

    fig, ax = plt.subplots(figsize=(8.6, 3.9))
    etiquetas = [g[0] for g in grupos]
    vals = [g[1] for g in grupos]
    colores = [RED if v > df.desertor.mean() * 100 else BLUE for v in vals]
    barras = ax.barh(etiquetas[::-1], vals[::-1], color=colores[::-1], height=0.62,
                     edgecolor="white")
    for b, v in zip(barras, vals[::-1]):
        ax.text(v + 0.8, b.get_y() + b.get_height() / 2, f"{v:.1f} %",
                va="center", fontsize=8.2, color=NAVY, fontweight="bold")
    ax.axvline(df.desertor.mean() * 100, color=NAVY, linestyle="--", linewidth=1)
    ax.text(df.desertor.mean() * 100 + 0.6, -0.75,
            f"Promedio {df.desertor.mean()*100:.1f} %", fontsize=7.6, color=NAVY)
    ax.set_xlabel("Tasa de deserción (%)")
    ax.set_xlim(0, max(vals) * 1.18)
    sin_grid(ax, ("y",))
    guardar(fig, "fig_05_desercion_por_grupo.png")


# ---------------------------------------------------------------------------
# Modelos
# ---------------------------------------------------------------------------
def ajustar_modelos(df, escenario="temprano"):
    """Reentrena cada familia con sus mejores hiperparámetros (sin búsqueda)."""
    mejores = json.loads((RES / "mejores_parametros.json").read_text())
    Xtr, Xte, ytr, yte = P.dividir(df, escenario)
    ajustados = {}
    for nombre, spec in P.catalogo_modelos(escenario).items():
        params = mejores.get(f"{escenario}|{nombre}", {})
        modelo = P.armar_pipeline(spec["modelo"], escenario)
        modelo.set_params(**{f"modelo__{k}": v for k, v in params.items()})
        modelo.fit(Xtr, ytr)
        ajustados[nombre] = modelo
    return ajustados, Xtr, Xte, ytr, yte


def fig_modelos(df: pd.DataFrame) -> None:
    df_aj = pd.read_csv(RES / "metricas_ajustadas.csv")
    df_base = pd.read_csv(RES / "metricas_baseline.csv")
    df_cv = pd.read_csv(RES / "cv_resumen.csv")
    umbrales = json.loads((RES / "umbrales.json").read_text())
    modelos, Xtr, Xte, ytr, yte = ajustar_modelos(df, "temprano")

    # 6. Comparación de modelos (escenario temprano)
    t = df_aj[df_aj.escenario == "temprano"].sort_values("f1", ascending=True)
    fig, ax = plt.subplots(figsize=(9, 4.2))
    y = np.arange(len(t))
    alto = 0.26
    for i, (col, color, lab) in enumerate([("f1", BLUE, "F1"), ("recall", ORANGE, "Recall"),
                                           ("roc_auc", GRAY, "AUC-ROC")]):
        ax.barh(y + (i - 1) * alto, t[col], height=alto, color=color, label=lab,
                edgecolor="white")
        for yy, v in zip(y + (i - 1) * alto, t[col]):
            ax.text(v + 0.004, yy, f"{v:.3f}", va="center", fontsize=7, color=NAVY)
    ax.set_yticks(y, t.modelo)
    ax.set_xlim(0.6, 1.0)
    ax.set_xlabel("Valor de la métrica (conjunto de prueba)")
    ax.legend(ncol=3, loc="lower right", fontsize=8)
    sin_grid(ax, ("y",))
    guardar(fig, "fig_06_comparacion_modelos.png")

    # 7. Brecha train-test
    fig, ax = plt.subplots(figsize=(9, 3.9))
    t2 = df_aj[df_aj.escenario == "temprano"]
    x = np.arange(len(t2))
    ax.bar(x - 0.19, t2.f1_train, width=0.36, color=GOLD, label="F1 entrenamiento")
    ax.bar(x + 0.19, t2.f1, width=0.36, color=BLUE, label="F1 prueba")
    for i, (a, b) in enumerate(zip(t2.f1_train, t2.f1)):
        ax.text(i - 0.19, a + 0.004, f"{a:.2f}", ha="center", fontsize=7.2, color=NAVY)
        ax.text(i + 0.19, b + 0.004, f"{b:.2f}", ha="center", fontsize=7.2, color=NAVY)
    ax.set_xticks(x, t2.modelo, rotation=18, ha="right")
    ax.set_ylim(0.55, 1.02)
    ax.set_ylabel("F1-Score")
    ax.legend(fontsize=8, loc="lower right")
    sin_grid(ax, ("x",))
    guardar(fig, "fig_07_brecha_overfitting.png")

    # 8. Comparación de escenarios (temprano vs completo)
    fig, ax = plt.subplots(figsize=(8.6, 3.8))
    ancho = 0.34
    x = np.arange(2)
    esc = ["temprano", "completo"]
    med = [df_aj[(df_aj.escenario == e)].f1.max() for e in esc]
    med_r = [df_aj[(df_aj.escenario == e)].roc_auc.max() for e in esc]
    ax.bar(x - ancho / 2, med, ancho, color=BLUE, label="Mejor F1")
    ax.bar(x + ancho / 2, med_r, ancho, color=GOLD, label="Mejor AUC-ROC")
    for i in range(2):
        ax.text(i - ancho / 2, med[i] + 0.006, f"{med[i]:.3f}", ha="center",
                fontsize=8.4, color=NAVY, fontweight="bold")
        ax.text(i + ancho / 2, med_r[i] + 0.006, f"{med_r[i]:.3f}", ha="center",
                fontsize=8.4, color=NAVY, fontweight="bold")
    ax.set_xticks(x, ["Escenario A · alerta temprana\n(inscripción + 1.er semestre)",
                      "Escenario B · diagnóstico\n(añade 2.º semestre)"])
    ax.set_ylim(0.7, 1.0)
    ax.set_ylabel("Mejor valor alcanzado")
    ax.legend(fontsize=8, loc="lower right")
    sin_grid(ax, ("x",))
    guardar(fig, "fig_08_escenarios.png")

    # 9. Matrices de confusión (4 modelos)
    elegidos = ["Regresión Logística", "Random Forest", "SVM (RBF)", "Árbol de Decisión"]
    fig, axes = plt.subplots(1, 4, figsize=(11.6, 3.2))
    for ax, nombre in zip(axes, elegidos):
        prob = modelos[nombre].predict_proba(Xte)[:, 1]
        pred = (prob >= umbrales["umbral_f1_optimo"]).astype(int)
        cm = confusion_matrix(yte, pred)
        ax.imshow(cm, cmap="Blues", alpha=0.9)
        etiquetas = ["No desertor", "Desertor"]
        ax.set_xticks([0, 1], etiquetas, fontsize=7.6, rotation=12)
        ax.set_yticks([0, 1], etiquetas, fontsize=7.6)
        ax.set_title(nombre, fontsize=9)
        for i in range(2):
            for j in range(2):
                ax.text(j, i, cm[i, j], ha="center", va="center", fontsize=13,
                        fontweight="bold",
                        color="white" if cm[i, j] > cm.max() / 2 else NAVY)
        ax.set_xlabel("Predicción", fontsize=8)
        ax.grid(False)
    axes[0].set_ylabel("Realidad", fontsize=8)
    fig.tight_layout()
    guardar(fig, "fig_09_matrices_confusion.png")

    # 10. Curvas ROC
    fig, ax = plt.subplots(figsize=(5.9, 5.2))
    for (nombre, modelo), color in zip(modelos.items(), PALETA):
        prob = modelo.predict_proba(Xte)[:, 1]
        fpr, tpr, _ = roc_curve(yte, prob)
        ax.plot(fpr, tpr, color=color, linewidth=1.7,
                label=f"{nombre} (AUC={auc(fpr, tpr):.3f})")
    ax.plot([0, 1], [0, 1], "--", color=GRAY, linewidth=1, label="Azar (0.500)")
    ax.set_xlabel("Tasa de falsos positivos")
    ax.set_ylabel("Tasa de verdaderos positivos")
    ax.legend(fontsize=7.3, loc="lower right")
    guardar(fig, "fig_10_roc.png")

    # 11. Curva precision-recall del modelo final
    final = modelos[umbrales["modelo"]]
    prob = final.predict_proba(Xte)[:, 1]
    prec, rec, _ = precision_recall_curve(yte, prob)
    ap = auc(rec, prec)
    fig, ax = plt.subplots(figsize=(5.9, 4.4))
    ax.plot(rec, prec, color=BLUE, linewidth=1.9, label=f"Curva PR (AP={ap:.3f})")
    ax.axhline(yte.mean(), color=GRAY, linestyle="--", linewidth=1,
               label=f"Azar ({yte.mean():.3f})")
    pred_op = (prob >= umbrales["umbral_f1_optimo"]).astype(int)
    m_op = P.metricas(yte, pred_op, None)
    ax.scatter([m_op["recall"]], [m_op["precision"]], color=RED, zorder=5, s=34,
               label=f"Punto de operación ({umbrales['umbral_f1_optimo']})")
    ax.set_xlabel("Recall (sensibilidad)")
    ax.set_ylabel("Precision")
    ax.legend(fontsize=8, loc="lower left")
    guardar(fig, "fig_11_precision_recall.png")

    # 12. Métricas frente al umbral
    umbrales_rango = np.linspace(0.05, 0.95, 120)
    f1s, recs, precs = [], [], []
    for u in umbrales_rango:
        m = P.metricas(yte, (prob >= u).astype(int), None)
        f1s.append(m["f1"])
        recs.append(m["recall"])
        precs.append(m["precision"])
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    ax.plot(umbrales_rango, f1s, color=BLUE, linewidth=2, label="F1")
    ax.plot(umbrales_rango, recs, color=ORANGE, linewidth=1.6, label="Recall")
    ax.plot(umbrales_rango, precs, color=GREEN, linewidth=1.6, label="Precision")
    ax.axvline(umbrales["umbral_f1_optimo"], color=RED, linestyle="--", linewidth=1.1)
    ax.text(umbrales["umbral_f1_optimo"] + 0.015, 0.52,
            f"umbral = {umbrales['umbral_f1_optimo']}", fontsize=7.8, color=RED)
    ax.set_xlabel("Umbral de decisión")
    ax.set_ylabel("Métrica")
    ax.legend(fontsize=8, loc="lower left")
    guardar(fig, "fig_12_umbral.png")

    # 13. Importancia por permutación
    r = permutation_importance(final, Xte, yte, n_repeats=12, random_state=P.RANDOM_STATE,
                               scoring="roc_auc", n_jobs=-1)
    nombres = np.array(Xte.columns)
    idx = np.argsort(r.importances_mean)[-14:]
    fig, ax = plt.subplots(figsize=(7.6, 4.9))
    ax.barh(np.arange(len(idx)), r.importances_mean[idx],
            xerr=r.importances_std[idx], color=BLUE, height=0.66,
            error_kw=dict(ecolor=GRAY, lw=1, capsize=2))
    ax.set_yticks(np.arange(len(idx)), nombres[idx], fontsize=8)
    ax.set_xlabel("Caída media del AUC-ROC al permutar la variable")
    sin_grid(ax, ("y",))
    guardar(fig, "fig_13_importancia.png")

    # 14. Equidad por subgrupos
    eq = pd.read_csv(RES / "equidad.csv")
    fig, ax = plt.subplots(figsize=(8.6, 3.7))
    etiquetas = [f"{r.grupo}" for r in eq.itertuples()]
    colores = [BLUE if r.variable != "Sexo" else ORANGE for r in eq.itertuples()]
    b = ax.bar(np.arange(len(eq)), eq["recall"], color=colores, width=0.62,
               edgecolor="white")
    for i, (rec, f1) in enumerate(zip(eq["recall"], eq["f1"])):
        ax.text(i, rec + 0.012, f"{rec:.2f}", ha="center", fontsize=7.4, color=NAVY)
    ax.set_xticks(np.arange(len(eq)), etiquetas, rotation=22, ha="right", fontsize=7.6)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Recall (desertores detectados)")
    sin_grid(ax, ("x",))
    guardar(fig, "fig_14_equidad.png")

    # 15. Validación cruzada: media ± desviación
    cv = df_cv[df_cv.escenario == "temprano"].sort_values("f1_media")
    fig, ax = plt.subplots(figsize=(8.4, 3.7))
    ax.errorbar(cv.f1_media, np.arange(len(cv)), xerr=cv.f1_std, fmt="o",
                color=BLUE, ecolor=GRAY, capsize=3, markersize=5)
    for i, (m, s) in enumerate(zip(cv.f1_media, cv.f1_std)):
        ax.text(m + s + 0.006, i, f"{m:.3f} ± {s:.3f}", va="center", fontsize=7.2,
                color=NAVY)
    ax.set_yticks(np.arange(len(cv)), cv.modelo)
    ax.set_xlim(0.6, 0.9)
    ax.set_xlabel("F1-Score en validación cruzada de 5 pliegues")
    sin_grid(ax, ("y",))
    guardar(fig, "fig_15_validacion_cruzada.png")


# ---------------------------------------------------------------------------
# Diagramas de la aplicación
# ---------------------------------------------------------------------------
def fig_arquitectura() -> None:
    fig, ax = plt.subplots(figsize=(10.4, 4.6))
    ax.set_xlim(0, 10.4)
    ax.set_ylim(0, 4.4)
    ax.axis("off")

    cajas = [
        (0.15, 1.55, 2.0, 1.25, "Usuario\n(orientador escolar)", BLUE, "#EAF3FB"),
        (2.55, 1.55, 2.05, 1.25, "Interfaz web\nStreamlit", BLUE, "#EAF3FB"),
        (5.05, 1.55, 2.2, 1.25, "Pipeline serializado\npreprocesador + modelo", BLUE, "#EAF3FB"),
        (7.7, 2.15, 2.5, 0.85, "Predicción y\nprobabilidad de riesgo", GREEN, "#E8F5EE"),
        (7.7, 0.55, 2.5, 0.85, "Recomendación\nde intervención", ORANGE, "#FDF1E8"),
    ]
    for x, y, w, h, txt, color, fondo in cajas:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06,rounding_size=0.12",
                                    linewidth=1.2, edgecolor=color, facecolor=fondo))
        ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center", fontsize=8.4,
                color=NAVY, fontweight="bold")

    flechas = [((2.18, 2.17), (2.52, 2.17)), ((4.63, 2.17), (5.02, 2.17)),
               ((7.28, 2.35), (7.67, 2.45)), ((7.28, 1.95), (7.67, 1.12))]
    for ini, fin in flechas:
        ax.add_patch(FancyArrowPatch(ini, fin, arrowstyle="-|>", mutation_scale=11,
                                     color=NAVY, linewidth=1.1))

    ax.text(5.2, 3.75, "Arquitectura de la aplicación «Alerta Temprana UPA»",
            ha="center", fontsize=12, fontweight="bold", color=NAVY)
    ax.text(5.2, 0.16, "Los datos personales no se almacenan: la inferencia ocurre en memoria.",
            ha="center", fontsize=8, style="italic", color=GRAY)
    guardar(fig, "fig_16_arquitectura.png")


def fig_flujo() -> None:
    pasos = [
        ("1", "Definición\ndel problema"), ("2", "Recolección\nde datos"),
        ("3", "Análisis\nexploratorio"), ("4", "Preprocesa-\nmiento"),
        ("5", "División\ntrain/test"), ("6", "Selección de\nmodelos"),
        ("7", "Entrenamiento\ne hiperparámetros"), ("8", "Evaluación\ny equidad"),
        ("9", "Despliegue\n(Streamlit)"), ("10", "Monitoreo\ny mejora"),
    ]
    fig, ax = plt.subplots(figsize=(10.6, 3.5))
    ax.set_xlim(0, 10.6)
    ax.set_ylim(0, 3.2)
    ax.axis("off")
    for i, (num, txt) in enumerate(pasos):
        fila, col = divmod(i, 5)
        x = 0.28 + col * 2.05
        y = 1.85 if fila == 0 else 0.45
        color = BLUE if fila == 0 else GREEN
        ax.add_patch(FancyBboxPatch((x, y), 1.72, 0.95,
                                    boxstyle="round,pad=0.05,rounding_size=0.1",
                                    linewidth=1.1, edgecolor=color, facecolor="#F4F8FC"))
        ax.text(x + 0.18, y + 0.72, num, fontsize=8.5, fontweight="bold", color=color)
        ax.text(x + 0.86, y + 0.42, txt, ha="center", va="center", fontsize=7.4,
                color=NAVY)
        if col < 4:
            ax.annotate("", xy=(x + 1.98, y + 0.47), xytext=(x + 1.76, y + 0.47),
                        arrowprops=dict(arrowstyle="-|>", color=GRAY, lw=1))
        elif fila == 0:
            ax.annotate("", xy=(x + 0.86, 1.28), xytext=(x + 0.86, 1.82),
                        arrowprops=dict(arrowstyle="-|>", color=GRAY, lw=1))
        if fila == 1 and col < 4:
            pass
    ax.text(5.3, 0.05, "", fontsize=1)
    guardar(fig, "fig_17_ciclo_vida.png")


def main() -> None:
    df = P.enriquecer(P.cargar_datos())
    print("Figuras EDA...")
    fig_eda(df)
    print("Figuras de modelos...")
    fig_modelos(df)
    print("Diagramas...")
    fig_arquitectura()
    fig_flujo()
    print("Listo.")


if __name__ == "__main__":
    main()
