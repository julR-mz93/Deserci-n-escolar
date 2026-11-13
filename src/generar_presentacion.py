#!/usr/bin/env python3
"""
Genera la presentación ejecutiva de la Actividad 3.2.1 (12 diapositivas).

Salida:
  docs/Presentacion_Ejecutiva.pptx
  docs/Presentacion_Ejecutiva.pdf
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

BASE = Path(__file__).resolve().parent.parent
FIG = BASE / "docs" / "figuras"
DOCS = BASE / "docs"
PPTX = DOCS / "Presentacion_Ejecutiva.pptx"
PDF = DOCS / "Presentacion_Ejecutiva.pdf"

NAVY = RGBColor(0x0B, 0x1F, 0x33)
NAVY_2 = RGBColor(0x18, 0x3A, 0x5A)
BLUE = RGBColor(0x1F, 0x6F, 0xB2)
AQUA = RGBColor(0x7F, 0xD1, 0xE8)
GOLD = RGBColor(0xE2, 0xB6, 0x5C)
TEAL = RGBColor(0x2A, 0x9D, 0x8F)
CORAL = RGBColor(0xD9, 0x5F, 0x4B)
GRAY = RGBColor(0x6B, 0x7A, 0x8A)
LIGHT = RGBColor(0xF4, 0xF8, 0xFC)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BORDER = RGBColor(0xDD, 0xE5, 0xED)

FONT = "Montserrat"
REPO = "https://github.com/julR-mz93/Fundamentos-de-Inteligencia-Artificial"
REF_IA = ("OpenCode. (2026). Big Pickle (versión 2026) [Modelo de lenguaje de gran "
          "escala]. https://opencode.ai")

W, H = 13.333, 7.5


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def slide_nueva(prs: Presentation, fondo=WHITE):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(W), Inches(H))
    bg.fill.solid()
    bg.fill.fore_color.rgb = fondo
    bg.line.fill.background()
    bg.shadow.inherit = False
    return s


def caja(s, x, y, w, h, relleno, borde=None, radio=True):
    forma = s.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if radio else MSO_SHAPE.RECTANGLE,
        Inches(x), Inches(y), Inches(w), Inches(h))
    forma.fill.solid()
    forma.fill.fore_color.rgb = relleno
    if borde:
        forma.line.color.rgb = borde
        forma.line.width = Pt(0.75)
    else:
        forma.line.fill.background()
    forma.shadow.inherit = False
    return forma


def texto(s, x, y, w, h, txt, size=16, color=NAVY, bold=False, italic=False,
          align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=1.0, font=FONT):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = align
    p.line_spacing = spacing
    r = p.add_run()
    r.text = txt
    r.font.name = font
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.italic = italic
    r.font.color.rgb = color
    return tb


def parrafos(s, x, y, w, h, items, size=15, color=NAVY, spacing=7,
             bullet="•", bullet_color=BLUE, line=1.05):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(spacing)
        p.line_spacing = line
        if bullet:
            rb = p.add_run()
            rb.text = bullet + "  "
            rb.font.name = FONT
            rb.font.size = Pt(size)
            rb.font.bold = True
            rb.font.color.rgb = bullet_color
        if isinstance(item, tuple):
            negrita, resto = item
            r1 = p.add_run()
            r1.text = negrita
            r1.font.name = FONT
            r1.font.size = Pt(size)
            r1.font.bold = True
            r1.font.color.rgb = color
            r2 = p.add_run()
            r2.text = resto
            r2.font.name = FONT
            r2.font.size = Pt(size)
            r2.font.color.rgb = color
        else:
            r = p.add_run()
            r.text = item
            r.font.name = FONT
            r.font.size = Pt(size)
            r.font.color.rgb = color
    return tb


def encabezado(s, kicker, titulo, numero, total=12):
    barra = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.16), Inches(H))
    barra.fill.solid()
    barra.fill.fore_color.rgb = NAVY
    barra.line.fill.background()
    barra.shadow.inherit = False
    oro = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.16), 0, Inches(0.035), Inches(H))
    oro.fill.solid()
    oro.fill.fore_color.rgb = GOLD
    oro.line.fill.background()
    oro.shadow.inherit = False

    texto(s, 0.55, 0.34, 11.5, 0.26, kicker.upper(), 9.5, BLUE, bold=True)
    texto(s, 0.55, 0.6, 12.0, 0.7, titulo, 29, NAVY, bold=True, spacing=0.92)
    linea = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.57), Inches(1.27),
                               Inches(1.35), Inches(0.045))
    linea.fill.solid()
    linea.fill.fore_color.rgb = GOLD
    linea.line.fill.background()
    linea.shadow.inherit = False
    pie(s, numero, total)


def pie(s, numero, total=12):
    texto(s, 0.55, 7.16, 8.0, 0.2,
          "Alerta temprana de deserción escolar · Grupo G171", 8, GRAY)
    texto(s, 12.1, 7.16, 0.75, 0.2, f"{numero:02d} / {total:02d}", 8,
          GRAY, align=PP_ALIGN.RIGHT)


def kpi(s, x, y, w, h, valor, etiqueta, nota, color, tam=30):
    caja(s, x, y, w, h, LIGHT)
    barra = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y),
                               Inches(w), Inches(0.07))
    barra.fill.solid()
    barra.fill.fore_color.rgb = color
    barra.line.fill.background()
    barra.shadow.inherit = False
    texto(s, x + 0.22, y + 0.16, w - 0.35, 0.55, valor, tam, color, bold=True)
    texto(s, x + 0.22, y + 0.72, w - 0.35, 0.24, etiqueta.upper(), 9, NAVY, bold=True)
    if nota:
        texto(s, x + 0.22, y + 0.98, w - 0.35, h - 1.05, nota, 9.5, GRAY, italic=True)


def tabla(s, x, y, w, h, headers, rows, col_w, size=11, alto=0.34,
          resaltar=()):
    shp = s.shapes.add_table(len(rows) + 1, len(headers), Inches(x), Inches(y),
                             Inches(w), Inches(h))
    tbl = shp.table
    for i, cw in enumerate(col_w):
        tbl.columns[i].width = Inches(cw)
    for j, htxt in enumerate(headers):
        cell = tbl.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        cell.margin_left = Inches(0.08)
        cell.margin_right = Inches(0.08)
        cell.margin_top = Inches(0.03)
        cell.margin_bottom = Inches(0.03)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER if j else PP_ALIGN.LEFT
        r = p.add_run()
        r.text = htxt
        r.font.name = FONT
        r.font.size = Pt(size - 0.5)
        r.font.bold = True
        r.font.color.rgb = WHITE
    for i, fila in enumerate(rows):
        for j, valor in enumerate(fila):
            cell = tbl.cell(i + 1, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if i % 2 == 0 else LIGHT
            cell.margin_left = Inches(0.08)
            cell.margin_right = Inches(0.08)
            cell.margin_top = Inches(0.03)
            cell.margin_bottom = Inches(0.03)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER if j else PP_ALIGN.LEFT
            r = p.add_run()
            r.text = str(valor)
            r.font.name = FONT
            r.font.size = Pt(size)
            r.font.bold = (i, j) in resaltar if resaltar else (j == 0)
            r.font.color.rgb = NAVY if j == 0 else NAVY_2
    return tbl


def imagen(s, nombre, x, y, w=None, h=None):
    kw = {}
    if w:
        kw["width"] = Inches(w)
    if h:
        kw["height"] = Inches(h)
    return s.shapes.add_picture(str(FIG / nombre), Inches(x), Inches(y), **kw)


# ---------------------------------------------------------------------------
# Diapositivas
# ---------------------------------------------------------------------------
def d1_portada(prs):
    s = slide_nueva(prs, NAVY)
    imagen(s, "hero_portada_slide.png", 0, 0, w=W)

    # Cabecera institucional
    texto(s, 0.9, 0.5, 7.4, 0.24,
          "UNIVERSIDAD POLITÉCNICA DE ATLAUTLA", 9.5, WHITE, bold=True)
    texto(s, 0.9, 0.78, 7.4, 0.24,
          "FUNDAMENTOS DE INTELIGENCIA ARTIFICIAL · GRUPO G171", 9, GOLD, bold=True)

    # Bloque editorial
    texto(s, 0.9, 1.98, 7.2, 0.3,
          "ACTIVIDAD 3.2.1 · APRENDIZAJE AUTOMÁTICO SUPERVISADO", 11, GOLD, bold=True)
    texto(s, 0.9, 2.34, 7.2, 1.6, "Alerta temprana\nde deserción escolar", 45,
          WHITE, bold=True, spacing=0.9)
    texto(s, 0.9, 3.86, 6.9, 0.72,
          "Un sistema supervisado que aprende de los datos\npara no perder estudiantes",
          15.5, AQUA, italic=True, spacing=1.15)

    lin = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.92), Inches(4.72),
                             Inches(1.9), Inches(0.045))
    lin.fill.solid()
    lin.fill.fore_color.rgb = GOLD
    lin.line.fill.background()
    lin.shadow.inherit = False

    # Equipo en lista vertical
    texto(s, 0.9, 4.98, 4.0, 0.22, "EQUIPO", 8.5, AQUA, bold=True)
    nombres = ["Julissa Marin Flor", "Erandy Naomy Rosas Toriz",
               "Rogerio Aguilar Bello"]
    for i, nombre in enumerate(nombres):
        y = 5.28 + i * 0.4
        punto = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.94), Inches(y + 0.09),
                                   Inches(0.09), Inches(0.09))
        punto.fill.solid()
        punto.fill.fore_color.rgb = GOLD
        punto.line.fill.background()
        punto.shadow.inherit = False
        texto(s, 1.2, y, 5.6, 0.3, nombre, 14, WHITE, bold=True)

    # Pie de la portada
    texto(s, 0.9, 6.82, 7.2, 0.24,
          "Docente: Javier García Lara · 12 de noviembre de 2026", 9.5,
          RGBColor(0xA9, 0xC3, 0xD8))


def d2_problema(prs):
    s = slide_nueva(prs)
    encabezado(s, "El problema", "Una silla vacía que se ve demasiado tarde", 2)
    texto(s, 0.55, 1.55, 6.9, 1.1,
          "La deserción no ocurre en un día: es una sucesión de señales que la "
          "institución suele advertir cuando el estudiante ya se fue.", 15, GRAY,
          italic=True, spacing=1.1)
    parrafos(s, 0.55, 2.75, 6.7, 3.0, [
        ("Impacto individual. ", "Menos ingresos, menor movilidad y más empleo informal."),
        ("Impacto institucional. ", "Recursos invertidos sin retorno y metas de cobertura incumplidas."),
        ("Impacto social. ", "Se reproduce la desigualdad y se pierde talento."),
        ("Impacto ético. ", "Un modelo mal usado etiqueta y estigmatiza."),
    ], size=13.5)
    kpi(s, 7.75, 1.65, 4.85, 1.35, "32.1 %", "tasa de deserción", "1 421 de 4 424 estudiantes", CORAL, 31)
    kpi(s, 7.75, 3.15, 4.85, 1.35, "57.8 %", "con deuda institucional", "frente al 29.2 % sin deuda", BLUE, 31)
    kpi(s, 7.75, 4.65, 4.85, 1.35, "58.6 %", "mayores de 25 años", "frente al 19.9 % de ≤ 20 años", GOLD, 31)
    texto(s, 0.55, 6.35, 6.7, 0.5,
          "Cada alerta temprana compra tiempo para una tutoría, una beca o una flexibilidad académica.",
          10.5, BLUE, italic=True)


def d3_objetivo(prs):
    s = slide_nueva(prs)
    encabezado(s, "Pregunta y objetivos", "¿Podemos actuar antes de que ocurra?", 3)
    caja(s, 0.55, 1.55, 12.2, 1.25, NAVY)
    texto(s, 0.85, 1.7, 11.6, 1.0,
          "¿Es posible predecir, con datos del primer semestre, qué estudiantes tienen alta "
          "probabilidad de desertar, con desempeño suficiente para orientar intervenciones y "
          "con interpretabilidad para rendir cuentas?", 15, WHITE, italic=True, spacing=1.1)

    datos = [
        ("01", "Datos verificables", "Dataset abierto UCI, 4 424 estudiantes y 36 variables documentadas.", BLUE),
        ("02", "Exploración honesta", "EDA, atípicos, desbalance y detección de fuga temporal.", TEAL),
        ("03", "Siete modelos", "GridSearchCV, validación cruzada y métricas más allá del accuracy.", GOLD),
        ("04", "Producto y ética", "App funcional, auditoría de equidad y reglas de uso claras.", CORAL),
    ]
    for i, (num, tit, txt, color) in enumerate(datos):
        x = 0.55 + (i % 2) * 6.25
        y = 3.05 + (i // 2) * 1.75
        caja(s, x, y, 5.95, 1.5, LIGHT)
        barra = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y),
                                   Inches(0.07), Inches(1.5))
        barra.fill.solid()
        barra.fill.fore_color.rgb = color
        barra.line.fill.background()
        barra.shadow.inherit = False
        texto(s, x + 0.22, y + 0.14, 0.6, 0.45, num, 20, color, bold=True)
        texto(s, x + 0.85, y + 0.15, 4.9, 0.3, tit.upper(), 10, NAVY, bold=True)
        texto(s, x + 0.85, y + 0.48, 4.9, 0.85, txt, 11.5, NAVY_2, spacing=1.05)


def d4_dataset(prs):
    s = slide_nueva(prs)
    encabezado(s, "Fase 1 · Dataset", "Datos abiertos, trazables y sin atajos", 4)
    tabla(s, 0.55, 1.6, 7.15, 4.0,
          ["Campo", "Información"],
          [
              ["Dataset", "Predict Students' Dropout and Academic Success"],
              ["Fuente", "UCI Machine Learning Repository · ID 697"],
              ["Autores", "Realinho, Vieira, Neto y Costa (2021)"],
              ["Licencia", "CC BY 4.0 · DOI 10.24432/C5MC89"],
              ["Tamaño", "4 424 × 36 variables + objetivo"],
              ["Calidad", "0 nulos · 0 duplicados"],
          ],
          [1.55, 5.6], size=10.5, alto=0.45)
    texto(s, 0.55, 5.78, 7.1, 0.9,
          "La etiqueta original tiene tres clases; se binariza para distinguir a quien "
          "desertó de quien permanece. El reto no es el volumen, es la temporalidad.",
          11, GRAY, italic=True, spacing=1.1)
    imagen(s, "fig_01_distribucion_objetivo.png", 8.05, 1.55, w=4.55)
    texto(s, 8.05, 5.55, 4.55, 0.6,
          "32.1 % desertores · 67.9 % graduados o inscritos", 10, BLUE, bold=True,
          align=PP_ALIGN.CENTER)


def d5_eda(prs):
    s = slide_nueva(prs)
    encabezado(s, "Fase 2 · Exploración", "El rendimiento temprano es la señal más fuerte", 5)
    imagen(s, "fig_02_histogramas.png", 0.55, 1.55, w=5.85)
    imagen(s, "fig_05_desercion_por_grupo.png", 6.95, 1.55, w=5.85)
    parrafos(s, 0.55, 5.65, 12.1, 1.2, [
        ("Notas y unidades aprobadas. ", "Separan con claridad a los dos grupos; la economía pesa tanto como la academia."),
        ("Atípicos reales. ", "No son errores de captura: eliminarlos sesgaría el modelo contra los perfiles menos frecuentes."),
        ("Subgrupos distintos. ", "Deuda, beca y edad cambian la base de riesgo; la equidad se audita después del entrenamiento."),
    ], size=11.5, spacing=3)


def d6_preproceso(prs):
    s = slide_nueva(prs)
    encabezado(s, "Fase 2 · Preparación", "Un pipeline que no se contamina con el futuro", 6)
    bloques = [
        ("Limpieza", "Nombres normalizados, sin nulos ni duplicados. Imputación robusta para formularios incompletos.", BLUE),
        ("Codificación y escalado", "One-Hot con frecuencia mínima, StandardScaler en numéricas y binarias.", TEAL),
        ("Sin fuga temporal", "Todo se ajusta solo con entrenamiento; el test permanece intacto.", GOLD),
    ]
    for i, (tit, txt, color) in enumerate(bloques):
        x = 0.55 + i * 4.15
        caja(s, x, 1.55, 3.85, 2.1, LIGHT)
        barra = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(1.55),
                                   Inches(3.85), Inches(0.08))
        barra.fill.solid()
        barra.fill.fore_color.rgb = color
        barra.line.fill.background()
        barra.shadow.inherit = False
        texto(s, x + 0.22, 1.75, 3.4, 0.35, tit.upper(), 9.5, color, bold=True)
        texto(s, x + 0.22, 2.12, 3.4, 1.4, txt, 12, NAVY_2, spacing=1.1)

    caja(s, 0.55, 3.95, 6.0, 2.15, NAVY)
    texto(s, 0.85, 4.12, 5.4, 0.3, "ESCENARIO A · TEMPRANO", 10, GOLD, bold=True)
    texto(s, 0.85, 4.45, 5.4, 0.55, "Inscripción + primer semestre", 19, WHITE, bold=True)
    texto(s, 0.85, 5.05, 5.3, 0.85,
          "82 columnas. Es el único escenario desplegable: la alerta llega cuando todavía "
          "se puede intervenir.", 11, AQUA, spacing=1.1)

    caja(s, 6.75, 3.95, 6.0, 2.15, LIGHT, BORDER)
    texto(s, 7.05, 4.12, 5.4, 0.3, "ESCENARIO B · COMPLETO", 10, BLUE, bold=True)
    texto(s, 7.05, 4.45, 5.4, 0.55, "Añade el segundo semestre", 19, NAVY, bold=True)
    texto(s, 7.05, 5.05, 5.3, 0.85,
          "107 columnas. Diagnóstico: +0.020 AUC, pero predice un desenlace que ya ocurrió.",
          11, GRAY, spacing=1.1)
    texto(s, 0.55, 6.3, 12.1, 0.4,
          "Balanceo: class_weight='balanced' · sin SMOTE, para no inventar combinaciones sin sentido educativo.",
          11, BLUE, italic=True)


def d7_metodo(prs):
    s = slide_nueva(prs)
    encabezado(s, "Fase 3 · Metodología", "Siete algoritmos, una misma vara", 7)
    modelos = ["Regresión Logística", "KNN", "SVM (RBF)", "Árbol de Decisión",
               "Random Forest", "Red Neuronal (MLP)", "Naive Bayes"]
    colores = [BLUE, TEAL, GOLD, CORAL, BLUE, TEAL, GOLD]
    for i, (m, c) in enumerate(zip(modelos, colores)):
        y = 1.55 + i * 0.62
        caja(s, 0.55, y, 5.3, 0.5, LIGHT)
        barra = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.55), Inches(y),
                                   Inches(0.06), Inches(0.5))
        barra.fill.solid()
        barra.fill.fore_color.rgb = c
        barra.line.fill.background()
        barra.shadow.inherit = False
        texto(s, 0.75, y + 0.1, 4.9, 0.3, m, 12, NAVY, bold=True)

    datos = [
        ("Partición", "80 / 20 estratificada · semilla 42"),
        ("Validación", "StratifiedKFold de 5 pliegues"),
        ("Búsqueda", "GridSearchCV con F1 como criterio"),
        ("Métricas", "accuracy · precision · recall · F1 · AUC-ROC · PR-AUC"),
        ("Control", "Brecha train-test + media y desviación en CV"),
    ]
    for i, (k, v) in enumerate(datos):
        y = 1.55 + i * 0.88
        texto(s, 6.35, y, 1.45, 0.3, k.upper(), 9, BLUE, bold=True)
        texto(s, 7.85, y - 0.04, 4.9, 0.75, v, 11.5, NAVY_2, spacing=1.05)
    texto(s, 6.35, 6.15, 6.4, 0.5,
          "El desempate es por recall: un falso negativo es un estudiante sin apoyo.",
          10.5, CORAL, italic=True)


def d8_resultados(prs):
    s = slide_nueva(prs)
    encabezado(s, "Fase 3 · Resultados", "La complejidad no compró precisión", 8)
    tabla(s, 0.55, 1.55, 6.55, 3.7,
          ["Modelo", "F1", "Recall", "AUC"],
          [
              ["Regresión Logística", "0.789", "0.820", "0.912"],
              ["Random Forest", "0.780", "0.778", "0.913"],
              ["SVM (RBF)", "0.757", "0.697", "0.910"],
              ["Árbol de Decisión", "0.756", "0.806", "0.881"],
              ["Red Neuronal (MLP)", "0.733", "0.648", "0.892"],
              ["Naive Bayes", "0.723", "0.736", "0.860"],
              ["KNN", "0.683", "0.581", "0.844"],
          ],
          [2.85, 1.1, 1.2, 1.2], size=10.5, alto=0.42,
          resaltar={(0, 0), (0, 1), (0, 2), (0, 3)})
    imagen(s, "fig_06_comparacion_modelos.png", 7.35, 1.5, w=5.45)
    texto(s, 0.55, 5.65, 12.1, 1.0,
          "Random Forest empata en AUC pero sobreajusta (brecha F1 = 0.221). La regresión "
          "logística lidera F1 y recall, y su brecha es la más pequeña. Con 3 500 casos "
          "tabulares, la capacidad extra de la red neuronal se convierte en ruido.",
          11.5, GRAY, italic=True, spacing=1.1)


def d9_umbral(prs):
    s = slide_nueva(prs)
    encabezado(s, "Fase 3 · Estabilidad", "Un umbral es una decisión institucional", 9)
    imagen(s, "fig_07_brecha_overfitting.png", 0.55, 1.5, w=5.55)
    imagen(s, "fig_12_umbral.png", 6.6, 1.5, w=5.9)
    parrafos(s, 0.55, 5.55, 12.1, 1.2, [
        ("F1 en CV = 0.768. ", "El 0.789 de prueba fue ligeramente benevolente: el valor realista en producción ronda 0.77."),
        ("Umbral 0.595. ", "Maximiza F1: precision 0.809, recall 0.789. Si el programa tiene capacidad limitada, el umbral se sube."),
    ], size=11.5, spacing=3)


def d10_equidad(prs):
    s = slide_nueva(prs)
    encabezado(s, "Fase 3 · Decisión y equidad", "El mejor modelo es el que se puede auditar", 10)
    kpi(s, 0.55, 1.5, 2.95, 1.15, "0.799", "F1", "umbral 0.595", GOLD, 26)
    kpi(s, 3.65, 1.5, 2.95, 1.15, "0.789", "recall", "224 de 284", CORAL, 26)
    kpi(s, 6.75, 1.5, 2.95, 1.15, "0.912", "AUC-ROC", "PR-AUC 0.871", TEAL, 26)
    kpi(s, 9.85, 1.5, 2.9, 1.15, "60", "falsos neg.", "21 % de desertores", BLUE, 26)

    parrafos(s, 0.55, 2.95, 6.4, 2.6, [
        ("Transparencia. ", "Coeficientes visibles y explicación local en la app."),
        ("Estabilidad. ", "La desviación entre pliegues más baja del comparativo."),
        ("Operación. ", "Inferencia en milisegundos, sin GPU ni dependencias pesadas."),
    ], size=12.5, spacing=6)

    tabla(s, 7.35, 2.95, 5.4, 2.5,
          ["Grupo", "Recall"],
          [
              ["Mujeres", "0.836"],
              ["Hombres", "0.739"],
              ["Sin beca", "0.820"],
              ["Con beca", "0.517"],
              ["≤ 20 años", "0.667"],
          ],
          [3.5, 1.8], size=10.5, alto=0.4, resaltar={(3, 1), (4, 1)})
    texto(s, 0.55, 5.85, 12.1, 0.9,
          "La brecha de becarios (0.517 vs. 0.820) es el hallazgo más incómodo: el modelo "
          "reconoce mejor al perfil dominante. Se reporta, se monitorea y se complementa con "
          "criterio humano.", 11, GRAY, italic=True, spacing=1.1)


def d11_app(prs):
    s = slide_nueva(prs)
    encabezado(s, "Fase 4 · Producto", "De la libreta a una app que se puede usar", 11)
    imagen(s, "demo_app.gif", 0.55, 1.5, w=6.7)
    parrafos(s, 7.55, 1.6, 5.25, 3.9, [
        ("Predicción individual. ", "Riesgo en tiempo real y explicación de los factores que más pesan."),
        ("Evaluación del modelo. ", "Comparativa, matriz de confusión, ROC y equidad dentro de la app."),
        ("Metodología y datos. ", "Método, límites y declaración de IA visibles para cualquiera."),
        ("Privacidad. ", "Todo ocurre en memoria; no se almacenan datos del estudiante."),
    ], size=11.5, spacing=6)

    caja(s, 0.55, 6.02, 12.2, 0.95, LIGHT)
    texto(s, 0.85, 6.18, 8.6, 0.6,
          "Streamlit · pipeline serializado con joblib · umbral ajustable · dos perfiles de ejemplo",
          11.5, NAVY, bold=True)
    imagen(s, "qr_repo.png", 11.35, 6.02, w=0.8)
    texto(s, 9.5, 6.22, 1.75, 0.5, "Abre la app\ndesde el repo", 8, GRAY,
          align=PP_ALIGN.RIGHT, spacing=1.0)


def d12_cierre(prs):
    s = slide_nueva(prs, NAVY)
    imagen(s, "hero_slide.png", 0, 0, w=W)
    texto(s, 0.9, 2.7, 11.5, 0.3, "CIERRE", 11, GOLD, bold=True)
    texto(s, 0.9, 3.0, 11.6, 0.95,
          "Predecir no es el objetivo;\nevitar que ocurra, sí.", 34, WHITE, bold=True,
          spacing=0.95)
    parrafos(s, 0.9, 4.2, 11.4, 1.6, [
        ("Un modelo simple gana. ", "F1 0.799 y AUC 0.912 con datos del primer semestre."),
        ("La equidad se reporta. ", "Becarios y menores de 20 años se detectan peor; hay que actuar sobre eso."),
        ("El producto está vivo. ", "App funcional, notebooks ejecutados y resultados reproducibles."),
    ], size=12.5, color=WHITE, bullet_color=GOLD, spacing=5)
    texto(s, 0.9, 6.25, 7.8, 0.7,
          "Repositorio: " + REPO + "\nIA: " + REF_IA, 8.5, AQUA, spacing=1.2)
    imagen(s, "qr_repo.png", 11.55, 5.95, w=0.95)


# ---------------------------------------------------------------------------
def main() -> None:
    prs = Presentation()
    prs.slide_width = Inches(W)
    prs.slide_height = Inches(H)
    d1_portada(prs)
    d2_problema(prs)
    d3_objetivo(prs)
    d4_dataset(prs)
    d5_eda(prs)
    d6_preproceso(prs)
    d7_metodo(prs)
    d8_resultados(prs)
    d9_umbral(prs)
    d10_equidad(prs)
    d11_app(prs)
    d12_cierre(prs)
    prs.save(PPTX)

    perfil = "file:///tmp/opencode/lo_profile_ai32"
    subprocess.run([
        "soffice", "--headless", f"-env:UserInstallation={perfil}",
        "--convert-to", "pdf", "--outdir", str(DOCS), str(PPTX),
    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("PPTX:", PPTX)
    print("PDF: ", PDF)


if __name__ == "__main__":
    main()
