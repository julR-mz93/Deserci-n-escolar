#!/usr/bin/env python3
"""
Genera los entregables documentales de la Actividad 3.2.1:

  docs/Fase1_Reporte_Seleccion.docx / .pdf   (1 página)
  docs/Informe_Metodologico.docx / .pdf      (15–25 páginas)

El informe se construye en dos pasadas para que el índice tenga números de
página reales, siguiendo el mismo procedimiento del proyecto anterior.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.shared import Cm, Pt

import docx_util as du

BASE = Path(__file__).resolve().parent.parent
FIG = BASE / "docs" / "figuras"
DOCS = BASE / "docs"
RES = BASE / "results"

DOCX = DOCS / "Informe_Metodologico.docx"
PDF = DOCS / "Informe_Metodologico.pdf"
DOCX_F1 = DOCS / "Fase1_Reporte_Seleccion.docx"
PDF_F1 = DOCS / "Fase1_Reporte_Seleccion.pdf"

ASIGNATURA = "Fundamentos de Inteligencia Artificial"
TITULO = "Alerta temprana de deserción escolar"
SUBTITULO = "Un sistema supervisado que aprende de los datos para no perder estudiantes"
TEMA = "Deserción escolar en educación superior"
GRUPO = "G171"
DOCENTE = "Javier García Lara"
INSTITUCION = "Universidad Politécnica de Atlautla"
CARRERA = "Ing. en Tecnologías de la Información e Innovación Digital"
FECHA = "12 de noviembre de 2026"
INTEGRANTES = ("Julissa Marin Flor · Erandy Naomy Rosas Toriz · "
               "Rogerio Aguilar Bello")
REPO = "https://github.com/julR-mz93/Fundamentos-de-Inteligencia-Artificial"
REF_IA = ("OpenCode. (2026). Big Pickle (versión 2026) [Modelo de lenguaje de gran "
          "escala]. https://opencode.ai")

META = json.loads((BASE / "models" / "metadata.json").read_text(encoding="utf-8"))
UMBRAL = json.loads((RES / "umbrales.json").read_text(encoding="utf-8"))

KICKERS = {
    "Resumen ejecutivo": "SÍNTESIS DEL PROYECTO",
    "1. Planteamiento del problema": "FASE 1 · DEFINICIÓN DEL PROBLEMA",
    "2. Ficha técnica del dataset": "FASE 1 · DATOS ABIERTOS Y VERIFICABLES",
    "3. Análisis exploratorio de datos": "FASE 2 · EXPLORACIÓN",
    "4. Preprocesamiento": "FASE 2 · PREPARACIÓN DE LOS DATOS",
    "5. Metodología experimental": "FASE 3 · DISEÑO DEL EXPERIMENTO",
    "6. Resultados": "FASE 3 · EVIDENCIA",
    "7. Selección del modelo y discusión": "FASE 3 · DECISIÓN",
    "8. Ética, sesgo y gobernanza del sistema": "FASE 3 · RESPONSABILIDAD",
    "9. Aplicación desplegada": "FASE 4 · PRODUCTO FUNCIONAL",
    "10. Conclusiones": "CIERRE",
    "11. Limitaciones y trabajo futuro": "HORIZONTE",
    "Referencias": "FUENTES EN APA 7",
    "Declaración de uso de inteligencia artificial": "TRANSPARENCIA",
    "Anexo A. Lista de cotejo": "CONTROL DE ENTREGA",
    "Anexo B. Repositorio y reproducibilidad": "TRAZABILIDAD",
}

# ---------------------------------------------------------------------------
# Utilidades de maquetación
# ---------------------------------------------------------------------------


def salto(doc):
    doc.add_page_break()


def h1(doc, texto):
    kicker = KICKERS.get(texto)
    if kicker:
        k = doc.add_paragraph()
        k.paragraph_format.space_before = Pt(9)
        k.paragraph_format.space_after = Pt(1)
        k.paragraph_format.keep_with_next = True
        r = k.add_run(kicker)
        du._aplicar_fuente(r, du.TITLE_FONT, 7.6, du.BLUE, bold=True)
        du.espaciado_letras(r, 34)
    p = doc.add_heading(texto, level=1)
    p.paragraph_format.space_before = Pt(0)
    return p


def h2(doc, texto):
    return doc.add_heading(texto, level=2)


def h3(doc, texto):
    return doc.add_heading(texto, level=3)


def par(doc, txt, **kw):
    return du.texto(doc, txt, **kw)


def vinetas(doc, elementos):
    for e in elementos:
        if isinstance(e, tuple):
            du.vineta(doc, e[1], negrita=e[0])
        else:
            du.vineta(doc, e)


def tabla(doc, headers, rows, widths, caption, size=8.4, center_cols=()):
    du.tabla_bonita(doc, headers, rows, widths, caption=caption, size=size,
                    first_col_bold=True, center_cols=center_cols)


def figura(doc, nombre, caption, ancho=6.35):
    du.figura(doc, FIG / nombre, caption, width_in=min(ancho * 0.8, 5.7))


def kpi(doc, items, size_valor=19):
    """Fila de tarjetas con un indicador grande, etiqueta y nota."""
    n = len(items)
    table = doc.add_table(rows=1, cols=n)
    table.alignment = 1
    du.anchos_tabla(table, [du.PAGE_WIDTH_CM / n] * n)
    du.bordes_tabla(table, outside=False, inside_h=False, inside_v=False)
    for i, (valor, etiqueta, nota, color) in enumerate(items):
        cell = table.rows[0].cells[i]
        du.sombreado_celda(cell, "F7FAFD")
        du.bordes_celda(cell, color=color, sz=30, edges=("top",))
        du.margenes_celda(cell, top=110, bottom=95, left=110, right=90)
        cell.text = ""
        p1 = cell.paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p1.paragraph_format.space_after = Pt(0)
        p1.paragraph_format.line_spacing = 0.95
        r1 = p1.add_run(str(valor))
        du._aplicar_fuente(r1, du.TITLE_FONT, size_valor, color, bold=True)
        p2 = cell.add_paragraph()
        p2.paragraph_format.space_before = Pt(2)
        p2.paragraph_format.space_after = Pt(0)
        r2 = p2.add_run(etiqueta.upper())
        du._aplicar_fuente(r2, du.TITLE_FONT, 7.1, du.NAVY, bold=True)
        du.espaciado_letras(r2, 12)
        if nota:
            p3 = cell.add_paragraph()
            p3.paragraph_format.space_before = Pt(1)
            p3.paragraph_format.space_after = Pt(0)
            r3 = p3.add_run(nota)
            du._aplicar_fuente(r3, du.BODY_FONT, 7.0, du.GRAY, italic=True)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)


def callout(doc, titulo, cuerpo, color=du.BLUE, fondo=du.BLUE_BG):
    du.callout(doc, titulo, cuerpo, color=color, fondo=fondo)


def formula(doc, txt, nota=None):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(2 if nota else 7)
    r = p.add_run(txt)
    du._aplicar_fuente(r, du.MONO_FONT, 9.2, du.NAVY)
    if nota:
        n = doc.add_paragraph()
        n.alignment = WD_ALIGN_PARAGRAPH.CENTER
        n.paragraph_format.space_after = Pt(7)
        rr = n.add_run(nota)
        du._aplicar_fuente(rr, du.BODY_FONT, 8, du.GRAY, italic=True)


def encabezado_pie(doc):
    sec = doc.sections[0]
    hp = sec.header.paragraphs[0]
    hp.text = ""
    hp.paragraph_format.tab_stops.add_tab_stop(Cm(du.PAGE_WIDTH_CM),
                                               WD_TAB_ALIGNMENT.RIGHT)
    r1 = hp.add_run("FUNDAMENTOS DE INTELIGENCIA ARTIFICIAL")
    du._aplicar_fuente(r1, du.TITLE_FONT, 7.4, du.GRAY, bold=True)
    du.espaciado_letras(r1, 10)
    hp.add_run("\t")
    r2 = hp.add_run("Actividad 3.2.1 · Aprendizaje automático supervisado")
    du._aplicar_fuente(r2, du.TITLE_FONT, 7.4, du.GRAY)
    du._borde_parrafo(hp, "bottom", du.BORDER, sz=4, space=4)

    fp = sec.footer.paragraphs[0]
    fp.text = ""
    fp.paragraph_format.tab_stops.add_tab_stop(Cm(du.PAGE_WIDTH_CM),
                                               WD_TAB_ALIGNMENT.RIGHT)
    r3 = fp.add_run("Equipo: deserción escolar · Grupo G171")
    du._aplicar_fuente(r3, du.TITLE_FONT, 7.4, du.GRAY)
    fp.add_run("\t")
    r4 = fp.add_run("Página ")
    du._aplicar_fuente(r4, du.TITLE_FONT, 7.4, du.GRAY)
    du._campo(fp, "PAGE")
    r5 = fp.add_run(" de ")
    du._aplicar_fuente(r5, du.TITLE_FONT, 7.4, du.GRAY)
    du._campo(fp, "NUMPAGES")
    du._borde_parrafo(fp, "top", du.BORDER, sz=4, space=4)


def metadatos(doc, titulo, asunto):
    cp = doc.core_properties
    cp.title = titulo
    cp.subject = asunto
    cp.author = INTEGRANTES
    cp.keywords = ("aprendizaje supervisado, deserción escolar, KNN, SVM, "
                   "Random Forest, Streamlit")
    cp.comments = "Actividad 3.2.1 · Universidad Politécnica de Atlautla"


# ---------------------------------------------------------------------------
# Portada e índice
# ---------------------------------------------------------------------------
def portada(doc):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.add_run().add_picture(str(FIG / "portada_hero.png"), width=Cm(16.55))

    du.texto(doc, "", size=21, space_after=15)
    du.texto(doc, INSTITUCION.upper(), size=10.8, bold=True, color=du.NAVY,
             align=WD_ALIGN_PARAGRAPH.CENTER, space_after=0, font=du.TITLE_FONT)
    du.espaciado_letras(doc.paragraphs[-1].runs[0], 30)
    du.texto(doc, ASIGNATURA.upper(), size=8.2, bold=True, color=du.GRAY,
             align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10,
             font=du.TITLE_FONT)
    du.espaciado_letras(doc.paragraphs[-1].runs[0], 22)

    du.texto(doc, "ACTIVIDAD 3.2.1 · APRENDIZAJE AUTOMÁTICO SUPERVISADO",
             size=9.2, bold=True, color=du.BLUE,
             align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4, font=du.TITLE_FONT)
    du.espaciado_letras(doc.paragraphs[-1].runs[0], 24)

    du.texto(doc, TITULO, size=27, bold=True, color=du.NAVY,
             align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2,
             font=du.TITLE_FONT, line_spacing=0.92)
    du.texto(doc, SUBTITULO, size=10.4, italic=True, color=du.NAVY_2,
             align=WD_ALIGN_PARAGRAPH.CENTER, space_after=0,
             font=du.TITLE_FONT)

    du.texto(doc, "", size=24, space_after=16)

    info = [
        ("Asignatura", ASIGNATURA, "Carrera", CARRERA, "Grupo", GRUPO),
        ("Docente", DOCENTE, "Fecha", FECHA, "Integrantes", INTEGRANTES),
    ]
    t = doc.add_table(rows=0, cols=3)
    t.alignment = 1
    du.anchos_tabla(t, [5.55, 5.55, 5.45])
    for fila in info:
        cells = t.add_row().cells
        for j in range(3):
            etiqueta, valor = fila[j * 2], fila[j * 2 + 1]
            cell = cells[j]
            cell.text = ""
            p1 = cell.paragraphs[0]
            p1.paragraph_format.space_after = Pt(0)
            r1 = p1.add_run(etiqueta.upper())
            du._aplicar_fuente(r1, du.TITLE_FONT, 6.9, du.GRAY, bold=True)
            du.espaciado_letras(r1, 12)
            p2 = cell.add_paragraph()
            p2.paragraph_format.space_after = Pt(0)
            p2.paragraph_format.line_spacing = 1.0
            _nombres = (valor.split(" · ") if etiqueta == "Integrantes"
                        else [valor])
            _size = 8.1 if etiqueta == "Integrantes" else 9.4
            r2 = p2.add_run(_nombres[0])
            du._aplicar_fuente(r2, du.BODY_FONT, _size, du.NAVY, bold=True)
            _ultimo = r2
            for _extra in _nombres[1:]:
                _ultimo.add_break()
                _ultimo = p2.add_run(_extra)
                du._aplicar_fuente(_ultimo, du.BODY_FONT, _size, du.NAVY, bold=True)
            du.sombreado_celda(cell, "F7FAFD")
            du.margenes_celda(cell, top=68, bottom=68, left=100, right=70)
    du.bordes_tabla(t, color="E3EBF3", sz=4, outside=False,
                    inside_h=True, inside_v=False)


def indice(doc, paginas: dict):
    salto(doc)
    h1(doc, "Índice")
    par(doc, "Contenido del documento metodológico. Las páginas corresponden a la "
             "numeración impresa en el pie.", size=8.8, italic=True, color=du.GRAY,
        space_after=6)

    entradas = [
        ("Resumen ejecutivo", "resumen", 1),
        ("1. Planteamiento del problema", "s1", 1),
        ("1.1 Contexto y magnitud de la deserción", "s1_1", 2),
        ("1.2 Justificación social y educativa", "s1_2", 2),
        ("1.3 Pregunta de investigación y objetivos", "s1_3", 2),
        ("1.4 Alcance del proyecto", "s1_4", 2),
        ("2. Ficha técnica del dataset", "s2", 1),
        ("2.1 Descripción de las variables", "s2_1", 2),
        ("2.2 Procedencia, licencia y ética del dato", "s2_2", 2),
        ("3. Análisis exploratorio de datos", "s3", 1),
        ("3.1 La variable objetivo", "s3_1", 2),
        ("3.2 Distribuciones, valores atípicos y correlaciones", "s3_2", 2),
        ("3.3 Deserción por subgrupos", "s3_3", 2),
        ("3.4 Hallazgos del análisis exploratorio", "s3_4", 2),
        ("4. Preprocesamiento", "s4", 1),
        ("4.1 Limpieza, codificación y escalado", "s4_1", 2),
        ("4.2 Ingeniería de características", "s4_2", 2),
        ("4.3 Balanceo de clases", "s4_3", 2),
        ("4.4 División y prevención de fuga de información", "s4_4", 2),
        ("5. Metodología experimental", "s5", 1),
        ("5.1 Diseño del experimento", "s5_1", 2),
        ("5.2 Algoritmos comparados", "s5_2", 2),
        ("5.3 Hiperparámetros y métricas", "s5_3", 2),
        ("6. Resultados", "s6", 1),
        ("6.1 Línea base y modelos ajustados", "s6_1", 2),
        ("6.2 Sobreajuste y validación cruzada", "s6_2", 2),
        ("6.3 Escenario temprano frente a completo", "s6_3", 2),
        ("6.4 Matrices de confusión, ROC y precisión-recall", "s6_4", 2),
        ("6.5 Umbral de decisión", "s6_5", 2),
        ("6.6 Interpretabilidad y equidad", "s6_6", 2),
        ("7. Selección del modelo y discusión", "s7", 1),
        ("8. Ética, sesgo y gobernanza del sistema", "s8", 1),
        ("9. Aplicación desplegada", "s9", 1),
        ("10. Conclusiones", "s10", 1),
        ("11. Limitaciones y trabajo futuro", "s11", 1),
        ("Referencias", "ref", 1),
        ("Declaración de uso de inteligencia artificial", "ia", 1),
        ("Anexo A. Lista de cotejo", "anexo_a", 1),
        ("Anexo B. Repositorio y reproducibilidad", "anexo_b", 1),
    ]

    for texto, clave, nivel in entradas:
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.tab_stops.add_tab_stop(Cm(16.5), WD_TAB_ALIGNMENT.RIGHT,
                                  WD_TAB_LEADER.DOTS)
        pf.space_before = Pt(4.2 if nivel == 1 else 0.5)
        pf.space_after = Pt(0.6)
        pf.left_indent = Cm(0 if nivel == 1 else 0.65)
        pf.line_spacing = 0.94
        r = p.add_run(texto)
        du._aplicar_fuente(r, du.TITLE_FONT if nivel == 1 else du.BODY_FONT,
                           9.7 if nivel == 1 else 8.6,
                           du.NAVY if nivel == 1 else du.NAVY_2,
                           bold=(nivel == 1))
        p.add_run("\t")
        r2 = p.add_run(str(paginas.get(clave, "00")))
        du._aplicar_fuente(r2, du.TITLE_FONT if nivel == 1 else du.BODY_FONT,
                           9.3 if nivel == 1 else 8.4,
                           du.NAVY if nivel == 1 else du.GRAY,
                           bold=(nivel == 1))

    du.texto(doc, "Cada cifra proviene de una corrida registrada en results/ y puede "
                  "reproducirse con los comandos del Anexo B.", size=8,
             italic=True, color=du.GRAY, space_before=6, space_after=0)


# ---------------------------------------------------------------------------
# Secciones
# ---------------------------------------------------------------------------
def resumen(doc):
    salto(doc)
    h1(doc, "Resumen ejecutivo")
    par(doc, "La deserción escolar es una de las formas más silenciosas de la desigualdad "
             "educativa: no ocurre en un solo día, sino en una sucesión de señales que la "
             "institución suele advertir cuando el estudiante ya se fue. Este proyecto "
             "construye y evalúa un sistema de alerta temprana que estima, al inicio del "
             "segundo semestre, la probabilidad de que un estudiante abandone sus estudios.")
    par(doc, "Se trabajó con el conjunto abierto Predict Students' Dropout and Academic "
             "Success (Realinho et al., 2021), disponible en el repositorio de la Universidad "
             "de California en Irvine. Contiene 4 424 registros y 36 variables académicas, "
             "demográficas y socioeconómicas de estudiantes de una institución de educación "
             "superior. La variable objetivo se binarizó: 1 = desertor (32.1 % de los casos), "
             "0 = graduado o todavía inscrito (67.9 %).")
    par(doc, "Se compararon siete algoritmos —regresión logística, KNN, SVM con kernel RBF, "
             "árbol de decisión, Random Forest, red neuronal multicapa y Naive Bayes— en dos "
             "escenarios. El escenario A usa solo información disponible al terminar el primer "
             "semestre; el escenario B añade el segundo semestre. El primero es el único "
             "desplegable, porque el segundo predice un desenlace que ya ocurrió.")
    par(doc, "El modelo ganador es una regresión logística con ponderación de clases "
             "(C = 10) y umbral de decisión ajustado a 0.595. En el 20 % de prueba alcanza "
             "accuracy = 0.872, precision = 0.809, recall = 0.789, F1 = 0.799 y AUC-ROC = "
             "0.912. Es decir: detecta casi ocho de cada diez estudiantes que desertan, con "
             "cuatro de cada cinco alertas correctas. Los modelos más complejos no superan "
             "este resultado, y la diferencia entre el escenario A y el B es de apenas dos "
             "centésimas de AUC-ROC.")
    par(doc, "El hallazgo técnico más importante es que la complejidad no compra precisión. "
             "El hallazgo ético es que el modelo no es neutral: su recall cae al 52 % entre "
             "estudiantes con beca y al 67 % entre los menores de 20 años. El informe "
             "documenta esas brechas, propone mitigaciones y sostiene que la predicción debe "
             "ser un disparador de acompañamiento humano, nunca una sentencia automática.")
    par(doc, "El sistema se desplegó como aplicación web en Streamlit, con formulario de "
             "captura, estimación de riesgo en tiempo real, explicación de los factores que "
             "pesan en cada caso y módulo de evaluación del modelo. Todo el código, los "
             "resultados y las figuras son reproducibles desde el repositorio del proyecto.")

    du.texto(doc, "", size=4)
    callout(doc, "RESULTADO EN UNA LÍNEA",
            "Un modelo interpretable y barato detecta al 79 % de los estudiantes en riesgo "
            "usando únicamente datos de inscripción y del primer semestre, lo que permite "
            "intervenir antes de que el abandono ocurra.")


def seccion_1(doc):
    h1(doc, "1. Planteamiento del problema")
    callout(doc, "OBJETIVO DE LA SECCIÓN",
            "Delimitar el problema real que resuelve el proyecto, justificar su relevancia "
            "social y formular con precisión la pregunta de investigación y los objetivos.",
            color=du.BLUE, fondo=du.BLUE_BG)

    h2(doc, "1.1 Contexto y magnitud de la deserción")
    par(doc, "En América Latina y el Caribe, abandonar la escuela es un fenómeno que se "
             "concentra en los primeros años de cada nivel educativo y que golpea con más "
             "fuerza a los hogares de menores ingresos. La Organización de las Naciones "
             "Unidas para la Educación, la Ciencia y la Cultura (UNESCO, 2024) advierte que "
             "las trayectorias educativas se interrumpen por una combinación de factores "
             "económicos, académicos y familiares, y que cada abandono reduce de forma "
             "permanente las oportunidades laborales y de participación social de la persona.")
    par(doc, "En México, los indicadores de abandono escolar que publican la Secretaría de "
             "Educación Pública y el Instituto Nacional de Estadística y Geografía coinciden "
             "en una tendencia: la deserción disminuye lentamente, pero persiste con brechas "
             "territoriales y socioeconómicas. La Encuesta Nacional de Ocupación y Empleo "
             "registra además que una parte importante de los jóvenes que dejan la escuela "
             "lo hace para incorporarse a un trabajo precario o para atender responsabilidades "
             "de cuidado, no por falta de interés (INEGI, 2024).")
    par(doc, "La institución de origen del dataset que se usa en este proyecto presenta una "
             "tasa de deserción del 32.1 %, muy superior a la de los sistemas educativos "
             "nacionales. Esa cifra no debe leerse como un retrato de México —el dataset es "
             "portugués—, sino como una advertencia metodológica: cuando la deserción afecta a "
             "uno de cada tres estudiantes, predecirla deja de ser un ejercicio académico y "
             "se vuelve una necesidad operativa.")

    h2(doc, "1.2 Justificación social y educativa")
    par(doc, "Un sistema de alerta temprana no evita la deserción por sí mismo: la evita la "
             "institución que actúa sobre la alerta. Lo que el sistema aporta es tiempo. Sin "
             "modelo, el abandono se descubre al revisar las actas o al notar una silla vacía; "
             "con modelo, el tutor recibe una lista priorizada al comenzar el semestre, cuando "
             "todavía es posible ofrecer una beca, una tutoría o una flexibilidad académica.")
    vinetas(doc, [
        ("Impacto individual. ", "Quien abandona pierde, en promedio, ingresos futuros, "
                                 "movilidad social y acceso a empleo formal."),
        ("Impacto institucional. ", "Cada estudiante que deserta representa recursos "
                                    "invertidos sin retorno y una meta de cobertura incumplida."),
        ("Impacto social. ", "La deserción reproduce desigualdad: afecta más a quienes menos "
                             "tienen y reduce la base de profesionales del país."),
        ("Impacto ético. ", "Un modelo mal usado puede etiquetar y estigmatizar. Por eso el "
                            "proyecto incluye análisis de equidad y reglas de uso explícitas."),
    ])
    par(doc, "La literatura sobre retención estudiantil coincide en que las intervenciones "
             "tempranas son más eficaces y menos costosas que las remediales. Detectar el "
             "riesgo en el primer semestre permite actuar sobre variables que aún se pueden "
             "modificar —asistencia, carga académica, situación económica— y no sobre el "
             "expediente cerrado de un estudiante que ya se fue.")

    h2(doc, "1.3 Pregunta de investigación y objetivos")
    callout(doc, "PREGUNTA DE INVESTIGACIÓN",
            "¿Es posible predecir, con datos disponibles al inicio del segundo semestre, qué "
            "estudiantes de educación superior tienen alta probabilidad de desertar, con un "
            "desempeño suficiente para orientar intervenciones institucionales y con un nivel "
            "de interpretabilidad que permita rendir cuentas?",
            color=du.GOLD, fondo="#FFF6E8")
    par(doc, "**Objetivo general.** Diseñar, implementar y evaluar una aplicación de "
             "aprendizaje automático supervisado que estime el riesgo de deserción escolar, "
             "comparando al menos tres algoritmos con métricas objetivas y desplegando el "
             "modelo con mejor equilibrio entre desempeño e interpretabilidad.")
    par(doc, "**Objetivos específicos.**", space_after=3)
    vinetas(doc, [
        "Seleccionar un dataset abierto, documentar su procedencia y verificar su calidad.",
        "Realizar un análisis exploratorio con visualizaciones y detección de valores atípicos.",
        "Preprocesar los datos —limpieza, codificación, escalado y balanceo— sin fuga de información.",
        "Entrenar y optimizar al menos tres algoritmos de clasificación supervisada.",
        "Comparar los modelos con accuracy, precision, recall, F1, AUC-ROC y matrices de confusión.",
        "Analizar el sobreajuste y la estabilidad mediante validación cruzada.",
        "Evaluar la equidad del modelo entre subgrupos poblacionales.",
        "Desplegar el modelo en una aplicación web funcional y documentar su reproducibilidad.",
    ])

    h2(doc, "1.4 Alcance del proyecto")
    par(doc, "El proyecto entrega un prototipo académico funcional, no un sistema en "
             "producción. Predice deserción, no la explica causalmente; identifica perfiles de "
             "riesgo, no determina por qué un estudiante abandona. No sustituye la valoración "
             "de un tutor ni debe usarse para negar beneficios. El alcance incluye la "
             "comparación de siete modelos, el ajuste de hiperparámetros, el análisis de "
             "equidad y el despliegue local/cloud de la aplicación; queda fuera el monitoreo "
             "en producción, la integración con sistemas escolares y la validación con datos "
             "mexicanos, que se plantean como trabajo futuro.")


def seccion_2(doc):
    h1(doc, "2. Ficha técnica del dataset")
    callout(doc, "PRODUCTO DE LA FASE 1",
            "Ficha técnica del conjunto de datos: fuente verificable, tamaño, variables, tipo "
            "de tarea y justificación del problema social.", color=du.BLUE, fondo=du.BLUE_BG)

    tabla(doc,
          ["Campo", "Información"],
          [
              ["Nombre", "Predict Students' Dropout and Academic Success"],
              ["Fuente", "UCI Machine Learning Repository (ID 697)"],
              ["Autores", "Realinho, Vieira, Neto y Costa (2021)"],
              ["Enlace", "https://doi.org/10.24432/C5MC89"],
              ["Licencia", "Creative Commons Atribución 4.0 Internacional (CC BY 4.0)"],
              ["Registros", "4 424 estudiantes (4 425 líneas con encabezado)"],
              ["Columnas", "36 variables de entrada + 1 variable objetivo"],
              ["Valores faltantes", "0 (conjunto curado); los duplicados exactos también son 0"],
              ["Variable objetivo", "Target: Graduate (2 209), Enrolled (794), Dropout (1 421)"],
              ["Tarea", "Clasificación binaria supervisada (desertor / no desertor)"],
              ["Desbalance", "67.9 % no desertor · 32.1 % desertor (razón 2.1 : 1)"],
              ["Contexto", "Educación superior; institución portuguesa; cohortes 2008–2019"],
              ["Idioma", "Inglés (variables y etiquetas)"],
          ],
          [3.4, 13.0],
          "Tabla 1. Ficha técnica del conjunto de datos.", size=8.6)

    h2(doc, "2.1 Descripción de las variables")
    par(doc, "Las 36 variables se agrupan en cuatro bloques interpretables. Esta agrupación "
             "guía tanto el análisis exploratorio como las decisiones de preprocesamiento.")
    tabla(doc,
          ["Bloque", "Variables", "Ejemplos y unidades"],
          [
              ["Datos de inscripción\n(11)", "Vía de admisión, carrera, orden de preferencia, "
               "titulación previa, nota de admisión, edad, turno, género, nacionalidad",
               "Nota de admisión (0–200); edad (17–70 años)"],
              ["Situación socioeconómica\n(7)", "Beca, deuda, colegiatura al corriente, "
               "ocupación y titulación de madre y padre, estudiante desplazado",
               "Beca (0/1); deuda (0/1); colegiatura (0/1)"],
              ["Rendimiento 1.er semestre\n(6)", "Unidades acreditadas, inscritas, evaluadas, "
               "aprobadas, calificación media y sin evaluar",
               "Unidades (0–26); calificación (0–20)"],
              ["Rendimiento 2.º semestre\n(6)", "Las mismas seis variables del segundo semestre",
               "Unidades (0–23); calificación (0–20)"],
              ["Entorno macroeconómico\n(3)", "Tasa de desempleo, inflación y crecimiento del PIB",
               "Porcentajes anuales del país"],
              ["Otras\n(3)", "Necesidades educativas especiales, estudiante internacional, "
               "estado civil", "Categóricas codificadas"],
          ],
          [3.6, 7.6, 5.2],
          "Tabla 2. Bloques de variables del dataset.", size=8.4)

    par(doc, "**Sobre las etiquetas.** La clase Enrolled (17.9 %) agrupa a estudiantes que "
             "siguen inscritos pero cuyo desenlace aún no se conoce. Para el objetivo del "
             "proyecto —decidir a quién acompañar— lo relevante es distinguir a quien desertó "
             "de quien permanece, de modo que Enrolled y Graduate se unen en la clase "
             "negativa. Esta decisión se discute en la sección 4.4 porque tiene consecuencias "
             "sobre lo que el modelo aprende.")

    h2(doc, "2.2 Procedencia, licencia y ética del dato")
    par(doc, "El conjunto fue publicado por investigadores del Instituto Politécnico de "
             "Portalegre con datos administrativos anonimizados de estudiantes matriculados "
             "entre 2008 y 2019. No contiene nombres, identificadores ni información que "
             "permita reidentificar a una persona, y se distribuye con licencia CC BY 4.0, "
             "que autoriza su uso académico citando la fuente.")
    par(doc, "Aun así, un dataset anonimizado no es un dataset inocuo. Las variables incluyen "
             "condición socioeconómica, composición familiar y necesidades educativas "
             "especiales: son datos sensibles en el sentido del artículo 3 de la Ley Federal "
             "de Protección de Datos Personales en Posesión de los Particulares. El proyecto "
             "los usa con fines analíticos, no almacena registros individuales en la "
             "aplicación y no publica predicciones identificables. Cualquier despliegue real "
             "requeriría aviso de privacidad, base legal y evaluación de impacto.")
    callout(doc, "NOTA DE HONESTIDAD METODOLÓGICA",
            "El dataset proviene de Portugal. Sus patrones no se extrapolan automáticamente "
            "al sistema educativo mexicano: se usa como caso de estudio metodológico. Antes de "
            "un despliegue local habría que reentrenar con datos institucionales y verificar "
            "que las relaciones aprendidas se sostienen.", color=du.ORANGE,
            fondo="#FDF1E8")


def seccion_3(doc):
    h1(doc, "3. Análisis exploratorio de datos")
    par(doc, "El análisis exploratorio respondió cuatro preguntas: cómo se distribuye la "
             "variable objetivo, qué variables separan a los dos grupos, qué relaciones "
             "existen entre predictores y qué subgrupos concentran el riesgo. Todas las "
             "figuras se generan con el script src/figuras.py y el cuaderno "
             "01_EDA_y_Preprocesamiento.ipynb.")

    h2(doc, "3.1 La variable objetivo")
    figura(doc, "fig_01_distribucion_objetivo.png",
           "Figura 1. Distribución de la etiqueta original y de la etiqueta binaria.", 6.3)
    par(doc, "La etiqueta original está moderadamente desbalanceada: la clase mayoritaria "
             "(graduado) duplica a la minoritaria (desertor). Al binarizar, la proporción queda "
             "en 67.9 % / 32.1 %. No es un desbalance extremo, pero sí suficiente para que la "
             "exactitud (accuracy) sea engañosa: un clasificador que dijera siempre «no "
             "deserta» acertaría el 67.9 % y sería inútil. Por eso el proyecto reporta F1, "
             "recall y AUC-ROC, y pondera las clases durante el entrenamiento.")

    h2(doc, "3.2 Distribuciones, valores atípicos y correlaciones")
    figura(doc, "fig_02_histogramas.png",
           "Figura 2. Distribuciones de variables clave por clase (densidades normalizadas).", 6.4)
    par(doc, "Las calificaciones y las unidades aprobadas separan con claridad los dos "
             "grupos: la distribución de quienes desertan se desplaza hacia valores bajos. La "
             "edad y la nota de admisión se solapan más, lo que sugiere efectos débiles o no "
             "lineales.")
    figura(doc, "fig_03_boxplots.png",
           "Figura 3. Diagramas de caja de las principales variables numéricas por clase.", 6.4)
    par(doc, "Los diagramas de caja confirman el patrón y muestran colas largas: hay "
             "estudiantes de 50 años y notas de admisión extremas. Se contabilizaron los "
             "valores atípicos con el criterio de rango intercuartílico (1.5 × IQR) y se "
             "decidió **conservarlos**, porque no son errores de captura sino casos reales de "
             "la población. Eliminarlos sesgaría el modelo contra los perfiles menos "
             "frecuentes, que suelen ser justamente los de mayor riesgo.")
    figura(doc, "fig_04_correlacion.png",
           "Figura 4. Matriz de correlación de Pearson entre variables numéricas y deserción.", 5.4)
    par(doc, "La correlación más alta con la deserción es negativa y proviene de la tasa de "
             "aprobación y del promedio de notas. Las variables macroeconómicas presentan "
             "correlaciones cercanas a cero: su aporte, si existe, es no lineal y se manifiesta "
             "en interacción con otras variables. La correlación no implica causalidad; el "
             "expediente académico refleja también condiciones sociales previas.")

    h2(doc, "3.3 Deserción por subgrupos")
    figura(doc, "fig_05_desercion_por_grupo.png",
           "Figura 5. Tasa de deserción por subgrupo socioeconómico y demográfico.", 6.4)
    tabla(doc,
          ["Subgrupo", "Tasa de deserción", "Interpretación"],
          [
              ["Con deuda institucional", "57.8 %", "La presión económica es el factor más fuerte"],
              ["Sin beca", "39.0 %", "La beca actúa como protección, aunque no es causal"],
              ["Con beca", "12.6 %", "Tasa 3 veces menor que sin beca"],
              ["Más de 25 años", "58.6 %", "Estudiantes que trabajan o tienen cargas familiares"],
              ["Hasta 20 años", "19.9 %", "Menor tasa, pero también menor detección (ver 6.6)"],
              ["Mujeres", "45.5 %", "Tasa más alta que los hombres en este dataset"],
          ],
          [5.0, 3.4, 8.0],
          "Tabla 3. Tasas de deserción observadas por subgrupo.", size=8.4,
          center_cols=(1,))
    par(doc, "Estas diferencias son descriptivas, no causales. Que los becarios deserten menos "
             "no demuestra que la beca cause retención: también puede ocurrir que la beca se "
             "asigne a estudiantes con mejores condiciones previas. Aun así, la magnitud de la "
             "brecha justifica incluir la situación económica como variable y justifica, sobre "
             "todo, vigilar que el modelo no la convierta en estigma.")

    h2(doc, "3.4 Hallazgos del análisis exploratorio")
    vinetas(doc, [
        ("El rendimiento del primer semestre es la señal más fuerte. ", "Tasa de aprobación, "
         "unidades aprobadas y calificación media separan a los grupos con claridad."),
        ("La economía pesa tanto como la academia. ", "Deuda y colegiatura vencida aparecen "
         "asociadas a tasas de deserción muy superiores al promedio."),
        ("La edad no es lineal. ", "El riesgo crece en los extremos de la distribución, "
         "especialmente en estudiantes mayores que 25 años."),
        ("Los atípicos son reales y se conservan. ", "Eliminarlos reduciría la cobertura del "
         "sistema justo en los perfiles menos frecuentes."),
        ("El desbalance exige métricas adecuadas. ", "Accuracy no sirve como criterio único; "
         "F1, recall y AUC-ROC son obligatorias."),
        ("Hay subgrupos con distinta base de riesgo. ", "La equidad deberá evaluarse después "
         "del entrenamiento, no solo antes."),
    ])


def seccion_4(doc):
    h1(doc, "4. Preprocesamiento")
    par(doc, "Todo el preprocesamiento vive dentro de un objeto Pipeline de scikit-learn. "
             "Esa decisión no es estética: garantiza que la imputación, la codificación y el "
             "escalado se ajusten únicamente con los datos de entrenamiento y se apliquen "
             "después a los de prueba, evitando la fuga de información que invalida "
             "comparaciones.")

    h2(doc, "4.1 Limpieza, codificación y escalado")
    vinetas(doc, [
        ("Limpieza. ", "El archivo original usa punto y coma como separador y una tabulación "
         "oculta en el nombre de una columna. Se normalizaron los nombres y se verificó que no "
         "hubiera nulos ni duplicados."),
        ("Imputación. ", "Aunque el dataset está completo, el pipeline imputa medianas en "
         "numéricas y moda en categóricas: la aplicación recibirá formularios incompletos."),
        ("Codificación. ", "One-Hot Encoding para las ocho variables nominales (estado civil, "
         "vía de admisión, carrera, titulación previa, titulación y ocupación de ambos padres). "
         "Se usa min_frequency = 0.01 para agrupar categorías raras y contener la dimensión."),
        ("Escalado. ", "StandardScaler en numéricas y binarias. Es imprescindible para KNN, SVM "
         "y redes neuronales, e inocuo para los árboles."),
        ("Variables excluidas. ", "Nacionalidad se excluye del escenario temprano por "
         "redundancia con la variable internacional y por su altísima concentración en un solo "
         "valor."),
    ])
    par(doc, "El resultado es una matriz de 33 variables crudas que, tras la codificación, se "
             "expande a 82 columnas numéricas en el escenario temprano. El pipeline conserva "
             "los nombres de las columnas para poder explicar cada coeficiente.")

    h2(doc, "4.2 Ingeniería de características")
    par(doc, "Se añadieron siete variables derivadas con interpretación educativa directa. "
             "Todas usan división protegida para evitar indeterminaciones cuando un estudiante "
             "no inscribió unidades.")
    tabla(doc,
          ["Variable derivada", "Fórmula", "Por qué se añadió"],
          [
              ["tasa_aprobacion_1s", "aprobadas ÷ inscritas (1.er sem.)",
               "Resume el avance curricular en una sola cifra comparable"],
              ["tasa_aprobacion_2s", "aprobadas ÷ inscritas (2.º sem.)",
               "Mismo indicador para el segundo semestre"],
              ["tasa_aprobacion_global", "total aprobadas ÷ total inscritas",
               "Visión acumulada del rendimiento"],
              ["reprobadas_1s", "inscritas − aprobadas (≥ 0)",
               "Mide el rezago en unidades, no solo el promedio"],
              ["delta_aprobacion", "tasa 2.º sem. − tasa 1.er sem.",
               "Captura el deterioro o la mejora entre semestres"],
              ["promedio_notas", "(nota 1.er sem. + nota 2.º sem.) ÷ 2",
               "Estabiliza la calificación frente a un semestre atípico"],
              ["senal_economica", "1 si deuda = 1 o colegiatura ≠ al corriente",
               "Condensa la presión económica en un indicador binario"],
          ],
          [4.4, 5.4, 6.6],
          "Tabla 4. Variables derivadas y su justificación.", size=8.2)
    par(doc, "La ingeniería de características mejoró el AUC-ROC del modelo base en "
             "aproximadamente una centésima y, sobre todo, hizo que la explicación del modelo "
             "fuera comprensible para un tutor: «tasa de aprobación del primer semestre» se "
             "entiende; «unidades aprobadas divididas entre inscritas» requiere traducción.")

    h2(doc, "4.3 Balanceo de clases")
    par(doc, "Se compararon tres estrategias con validación cruzada de cinco pliegues sobre "
             "el conjunto de entrenamiento. La métrica de comparación fue el recall, porque es "
             "la que mide cuántos desertores se detectan.")
    tabla(doc,
          ["Estrategia", "Recall medio", "Desviación", "Decisión"],
          [
              ["Sin balanceo", "0.752", "± 0.021", "Descartada: el modelo ignora la clase minoritaria"],
              ["class_weight = balanced", "0.801", "± 0.017", "**Elegida**"],
              ["Sobremuestreo aleatorio", "0.798", "± 0.019", "Equivalente, pero altera los datos"],
          ],
          [5.4, 3.0, 2.6, 5.4],
          "Tabla 5. Comparación de estrategias de balanceo (validación cruzada, 5 pliegues).",
          size=8.4, center_cols=(1, 2))
    par(doc, "No se usó SMOTE por tres razones. Primera: interpola vecinos en un espacio donde "
             "conviven variables one-hot y códigos nominales, y el «punto medio» entre dos "
             "carreras o dos ocupaciones no tiene significado. Segunda: no superó de forma "
             "significativa al sobremuestreo aleatorio en la prueba exploratoria. Tercera: "
             "cualquier técnica de remuestreo debe aplicarse dentro de cada pliegue; hacerlo "
             "mal es una fuente clásica de fuga de información. La ponderación de clases no "
             "altera los datos, conserva la distribución y es más fácil de auditar.")
    par(doc, "La segunda palanca para favorecer el recall es el umbral de decisión, que se "
             "ajusta en la sección 6.5. Juntas, ponderación y umbral permiten mover el punto "
             "de operación sin reentrenar.")

    h2(doc, "4.4 División y prevención de fuga de información")
    par(doc, "Se reservó el 20 % de los datos para prueba (885 estudiantes), con partición "
             "estratificada y semilla fija (random_state = 42). La misma partición se usa en "
             "todos los modelos, de modo que las comparaciones sean justas.")
    par(doc, "El riesgo más serio de este proyecto no es el desbalance: es la **fuga "
             "temporal**. El dataset incluye variables del segundo semestre; si se usan, el "
             "modelo aprende a reconocer a un desertor por el hecho de que ya dejó de asistir. "
             "El AUC sube, la demo se ve mejor y el sistema es inútil en la práctica. Por eso "
             "se definieron dos escenarios:")
    tabla(doc,
          ["Escenario", "Variables", "74 columnas tras codificar", "Uso"],
          [
              ["A · Temprano", "Inscripción + situación socioeconómica + primer semestre",
               "82", "Desplegable: alerta al iniciar el segundo semestre"],
              ["B · Completo", "A + segundo semestre + variables globales",
               "107", "Diagnóstico y comparación metodológica"],
          ],
          [3.2, 8.4, 3.2, 4.4],
          "Tabla 6. Escenarios de modelado y su uso previsto.", size=8.2,
          center_cols=(2,))
    callout(doc, "DECISIÓN CLAVE DEL PROYECTO",
            "El modelo que se despliega es el del escenario A. Cuesta alrededor de dos "
            "centésimas de AUC-ROC frente al escenario B, pero es el único que puede usarse "
            "antes de que la deserción ocurra. Un modelo tardío y preciso es un modelo inútil.",
            color=du.ORANGE, fondo="#FDF1E8")


def seccion_5(doc):
    h1(doc, "5. Metodología experimental")
    h2(doc, "5.1 Diseño del experimento")
    tabla(doc,
          ["Elemento", "Definición"],
          [
              ["Tarea", "Clasificación binaria supervisada"],
              ["Partición", "80 % entrenamiento (3 539) / 20 % prueba (885), estratificada"],
              ["Semilla", "random_state = 42 en partición, modelos y búsqueda"],
              ["Validación", "StratifiedKFold de 5 pliegues sobre entrenamiento"],
              ["Búsqueda", "GridSearchCV con F1 como métrica de selección"],
              ["Modelos", "7 algoritmos (lineal, instancias, margen, árbol, ensamble, red, bayes)"],
              ["Métricas", "accuracy, precision, recall, F1, AUC-ROC, PR-AUC"],
              ["Control de sobreajuste", "F1 train vs test + media y desviación en CV"],
              ["Criterio de selección", "F1, desempate por recall; interpretabilidad como veto"],
          ],
          [4.6, 12.0],
          "Tabla 7. Diseño experimental.", size=8.6)
    par(doc, "Se eligió F1 como métrica de búsqueda porque combina precision y recall en un "
             "solo número y no se deja engañar por el desbalance. El desempate por recall "
             "responde al costo asimétrico de los errores: un falso negativo deja a un "
             "estudiante sin apoyo; un falso positivo genera una tutoría innecesaria, que es "
             "costosa pero reversible.")

    h2(doc, "5.2 Algoritmos comparados")
    par(doc, "**K-Nearest Neighbors (KNN).** Asigna a cada caso la mayoría de sus K vecinos "
             "más cercanos; depende de la escala y de la métrica de distancia.")
    formula(doc, "d(x, xᵢ) = √( Σⱼ (xⱼ − xᵢⱼ)² )",
            "Distancia euclidiana; hiperparámetros: K, pesos y métrica")
    par(doc, "**Support Vector Machine (SVM).** Busca el hiperplano de mayor margen; el kernel "
             "RBF le permite fronteras no lineales, a un costo alto en datasets grandes.")
    formula(doc, "wᵀx + b = 0     margen = 2 / ‖w‖",
            "Hiperparámetros: C (regularización), kernel y γ")
    par(doc, "**Árbol de decisión.** Divide el espacio con preguntas que maximizan la ganancia "
             "de información; es muy interpretable y muy propenso al sobreajuste.")
    formula(doc, "H(S) = −Σ pᵢ log₂ pᵢ        G = 1 − Σ pᵢ²",
            "Entropía e índice Gini; hiperparámetros: profundidad y mínimo por hoja")
    par(doc, "**Random Forest.** Combina muchos árboles entrenados con muestras bootstrap y "
             "subconjuntos de variables; reduce la varianza a cambio de interpretabilidad.")
    par(doc, "**Red neuronal multicapa (MLP).** Compone capas con activación no lineal y ajusta "
             "sus pesos por retropropagación; es expresiva, pero exige más datos y es opaca.")
    formula(doc, "z = W·x + b        a = ReLU(z) = max(0, z)",
            "Forward pass; el error se minimiza por descenso del gradiente")
    par(doc, "**Regresión logística.** Modela la probabilidad de la clase positiva con una "
             "sigmoide sobre una combinación lineal; es calibrada e interpretable por diseño.")
    formula(doc, "P(y = 1 | x) = 1 / (1 + e^(−wᵀx − b))",
            "Hiperparámetro: C (inverso de la regularización L2)")
    par(doc, "**Naive Bayes gaussiano.** Aplica el teorema de Bayes suponiendo independencia "
             "condicional; es rapidísimo y sirve como referencia ingenua.")

    h2(doc, "5.3 Hiperparámetros y métricas")
    tabla(doc,
          ["Modelo", "Rejilla explorada", "Mejor configuración (escenario A)"],
          [
              ["Regresión Logística", "C ∈ {0.01, 0.1, 1, 10}", "C = 10"],
              ["KNN", "K ∈ {5, 11, 21, 31}; pesos uniforme/distancia", "K = 5, distancia"],
              ["SVM (RBF)", "C ∈ {0.5, 1, 5}; γ ∈ {scale, 0.01}", "C = 5, γ = 0.01"],
              ["Árbol de Decisión", "profundidad ∈ {4, 6, 8, ∞}; hojas ∈ {5, 20}",
               "profundidad = 6, hojas = 5"],
              ["Random Forest", "profundidad ∈ {8, 14, ∞}; hojas ∈ {1, 5}",
               "profundidad = ∞, hojas = 1"],
              ["Red Neuronal (MLP)", "capas ∈ {(32,), (64, 32)}; α ∈ {1e−4, 1e−2}",
               "capas = (32,), α = 0.01"],
              ["Naive Bayes", "var_smoothing ∈ {1e−9, 1e−7}", "1e−9"],
          ],
          [4.2, 7.6, 4.8],
          "Tabla 8. Espacio de búsqueda y configuración ganadora.", size=8.2)
    tabla(doc,
          ["Métrica", "Fórmula", "Cuándo es crítica en este problema"],
          [
              ["Accuracy", "(VP + VN) / total", "Referencia; engañosa por el desbalance"],
              ["Precision", "VP / (VP + FP)", "Costo de una alerta falsa (tutoría innecesaria)"],
              ["Recall", "VP / (VP + FN)", "Costo de no detectar a un estudiante en riesgo"],
              ["F1", "2 · (P · R) / (P + R)", "Criterio principal de comparación"],
              ["AUC-ROC", "Área bajo la curva ROC", "Capacidad de ordenar el riesgo"],
              ["PR-AUC", "Área bajo precision-recall", "Más informativa con clases desbalanceadas"],
          ],
          [3.2, 5.4, 8.0],
          "Tabla 9. Métricas de evaluación y su papel en el proyecto.", size=8.4)
    par(doc, "El AUC-ROC mide la probabilidad de que el modelo asigne mayor riesgo a un "
             "desertor elegido al azar que a un no desertor. Es útil para comparar modelos, "
             "pero no dice nada sobre el punto de operación: dos modelos con el mismo AUC "
             "pueden tener recalls muy distintos según el umbral. Por eso el proyecto reporta "
             "también la curva precision-recall y el umbral explícito.")


def seccion_6(doc):
    h1(doc, "6. Resultados")
    par(doc, "Se presentan primero los resultados de la línea base, después los modelos "
             "optimizados, luego los controles de sobreajuste y estabilidad, y finalmente el "
             "análisis del modelo ganador: umbral, interpretabilidad y equidad.")

    du.texto(doc, "TABLERO DEL MODELO FINAL · PRUEBA · UMBRAL 0.595", size=7.4, bold=True,
             color=du.GRAY, space_after=3, font=du.TITLE_FONT)
    kpi(doc, [
        ("0.872", "accuracy", "885 estudiantes", du.BLUE),
        ("0.789", "recall", "224 de 284 desertores", du.CORAL),
        ("0.799", "F1", "precisión 0.809", du.GOLD),
        ("0.912", "AUC-ROC", "PR-AUC 0.871 · umbral 0.595", du.TEAL),
    ], size_valor=17)

    h2(doc, "6.1 Línea base y modelos ajustados")
    tabla(doc,
          ["Modelo", "F1", "Recall", "Precision", "AUC-ROC", "Brecha F1"],
          [
              ["Regresión Logística", "0.786", "0.817", "0.758", "0.913", "−0.006"],
              ["KNN", "0.685", "0.581", "0.833", "0.839", "0.107"],
              ["SVM (RBF)", "0.773", "0.725", "0.827", "0.908", "0.077"],
              ["Árbol de Decisión", "0.673", "0.673", "0.673", "0.759", "0.328"],
              ["Random Forest", "0.780", "0.778", "0.781", "0.913", "0.221"],
              ["Red Neuronal (MLP)", "0.768", "0.701", "0.850", "0.913", "0.020"],
              ["Naive Bayes", "0.723", "0.736", "0.711", "0.860", "−0.023"],
          ],
          [4.6, 2.2, 2.2, 2.4, 2.4, 2.6],
          "Tabla 10. Línea base con hiperparámetros por defecto (escenario A, prueba).",
          size=8.2, center_cols=(1, 2, 3, 4, 5))
    par(doc, "La línea base ya muestra un patrón que se mantendrá: los modelos lineales y los "
             "ensambles funcionan bien; KNN y el árbol individual se quedan atrás. El árbol "
             "sin poda memoriza el entrenamiento (brecha de 0.328), y KNN sufre con la "
             "dimensionalidad y la mezcla de variables binarias y continuas.")
    tabla(doc,
          ["Modelo", "F1", "Recall", "Precision", "AUC-ROC", "PR-AUC", "Brecha F1"],
          [
              ["Regresión Logística", "**0.789**", "**0.820**", "0.759", "0.912", "0.871", "**−0.008**"],
              ["Random Forest", "0.780", "0.778", "0.781", "**0.913**", "**0.875**", "0.221"],
              ["SVM (RBF)", "0.757", "0.697", "0.829", "0.910", "0.868", "0.085"],
              ["Árbol de Decisión", "0.756", "0.806", "0.711", "0.881", "0.786", "0.027"],
              ["Red Neuronal (MLP)", "0.733", "0.648", "0.844", "0.892", "0.853", "0.021"],
              ["Naive Bayes", "0.723", "0.736", "0.711", "0.860", "0.721", "−0.023"],
              ["KNN", "0.683", "0.581", "0.829", "0.844", "0.785", "0.317"],
          ],
          [4.4, 2.1, 2.1, 2.2, 2.2, 2.2, 2.4],
          "Tabla 11. Modelos tras GridSearchCV (escenario A, prueba, umbral 0.5).",
          size=8.2, center_cols=(1, 2, 3, 4, 5, 6))
    figura(doc, "fig_06_comparacion_modelos.png",
           "Figura 6. Comparación de F1, recall y AUC-ROC de los siete modelos ajustados.", 6.4)
    par(doc, "Tres observaciones. Primera: la regresión logística lidera en F1 y recall. "
             "Segunda: Random Forest iguala en AUC-ROC pero no en F1, lo que significa que "
             "ordena bien el riesgo y acierta menos al decidir con umbral 0.5. Tercera: la red "
             "neuronal no despega; con 3 500 casos y variables tabulares, su capacidad extra se "
             "convierte en sobreajuste.")
    par(doc, "El ajuste de hiperparámetros mejoró a cuatro modelos y empeoró a tres. No es un "
             "error: cuando la rejilla es pequeña y la métrica de validación tiene varianza, "
             "elegir el mejor pliegue puede ser peor que el valor por defecto. Es un recordatorio "
             "de que la optimización no es magia; es una búsqueda con ruido.")

    h2(doc, "6.2 Sobreajuste y validación cruzada")
    figura(doc, "fig_07_brecha_overfitting.png",
           "Figura 7. F1 en entrenamiento frente a F1 en prueba para cada modelo.", 6.4)
    par(doc, "La brecha entre entrenamiento y prueba separa con nitidez a los modelos que "
             "memorizan de los que generalizan. Random Forest y KNN tienen brechas superiores a "
             "0.2; la regresión logística, la más pequeña (−0.008). Un modelo con brecha "
             "negativa parece «mejor en prueba que en entrenamiento», pero esa diferencia es "
             "ruido: el conjunto de prueba es pequeño y la partición concreta favorece al modelo.")
    tabla(doc,
          ["Modelo", "F1 (media ± desv.)", "Recall", "AUC-ROC", "Estabilidad"],
          [
              ["Regresión Logística", "0.768 ± 0.006", "0.801 ± 0.017", "0.902 ± 0.005", "Alta"],
              ["SVM (RBF)", "0.765 ± 0.008", "0.765 ± 0.013", "0.899 ± 0.006", "Alta"],
              ["Random Forest", "0.762 ± 0.012", "0.751 ± 0.020", "0.899 ± 0.011", "Media-alta"],
              ["Red Neuronal (MLP)", "0.760 ± 0.006", "0.694 ± 0.013", "0.902 ± 0.006", "Alta en F1, baja en recall"],
              ["Árbol de Decisión", "0.732 ± 0.023", "0.769 ± 0.022", "0.856 ± 0.013", "Media"],
              ["KNN", "0.703 ± 0.023", "0.610 ± 0.028", "0.846 ± 0.010", "Media"],
              ["Naive Bayes", "0.686 ± 0.008", "0.710 ± 0.015", "0.840 ± 0.003", "Alta pero baja"],
          ],
          [4.6, 4.0, 3.6, 3.2, 4.0],
          "Tabla 12. Validación cruzada de 5 pliegues sobre entrenamiento (escenario A).",
          size=8.2, center_cols=(1, 2, 3))
    figura(doc, "fig_15_validacion_cruzada.png",
           "Figura 8. F1 medio y desviación entre pliegues.", 6.0)
    par(doc, "La validación cruzada introduce un matiz importante y honesto: el F1 medio en "
             "entrenamiento (0.768) es inferior al F1 observado en prueba (0.789). El conjunto "
             "de prueba resultó ligeramente benevolente. La conclusión no cambia —la regresión "
             "logística sigue primera— pero el valor realista de F1 esperado en producción es "
             "cercano a 0.77, no a 0.80. Reportar ambas cifras es parte de la honestidad "
             "metodológica que exige la actividad.")

    h2(doc, "6.3 Escenario temprano frente a completo")
    tabla(doc,
          ["Escenario", "Mejor modelo", "F1", "Recall", "AUC-ROC", "Costo de anticiparse"],
          [
              ["A · Temprano", "Regresión Logística", "0.789", "0.820", "0.912", "—"],
              ["B · Completo", "SVM (RBF)", "0.815", "0.782", "0.932", "−0.020 AUC"],
          ],
          [3.6, 4.6, 2.2, 2.2, 2.4, 4.0],
          "Tabla 13. Comparación de escenarios (prueba, umbral 0.5).", size=8.4,
          center_cols=(2, 3, 4))
    figura(doc, "fig_08_escenarios.png",
           "Figura 9. Mejor F1 y mejor AUC-ROC alcanzados en cada escenario.", 6.0)
    par(doc, "Añadir el segundo semestre mejora el AUC-ROC en 0.020 y el F1 en 0.026. Es una "
             "ganancia real pero modesta, y se obtiene a un precio inadmisible para un sistema "
             "de alerta: cuando esos datos existen, el abandono ya ocurrió o está en curso. El "
             "escenario B se conserva en el informe como techo de desempeño y como evidencia de "
             "que el modelo temprano no está dejando información valiosa sobre la mesa.")

    h2(doc, "6.4 Matrices de confusión, ROC y precisión-recall")
    figura(doc, "fig_09_matrices_confusion.png",
           "Figura 10. Matrices de confusión de cuatro modelos con el umbral ajustado.", 6.5)
    par(doc, "La matriz del modelo ganador se lee así: de 284 estudiantes que desertaron, el "
             "modelo detectó 224 y dejó pasar 60; de 601 que no desertaron, marcó correctamente "
             "548 y generó 53 falsas alarmas. En términos operativos: por cada 100 alertas, "
             "unos 81 estudiantes realmente estaban en riesgo. El error que más importa —los 60 "
             "falsos negativos— equivale a 21 % de los desertores.")
    figura(doc, "fig_10_roc.png",
           "Figura 11. Curvas ROC de los siete modelos en el escenario temprano.", 5.4)
    par(doc, "Las curvas ROC se agrupan en dos familias: los modelos útiles (AUC entre 0.89 y "
             "0.91) y los claramente inferiores (Naive Bayes y KNN). La separación entre la "
             "regresión logística y Random Forest es de una milésima, lo que confirma que la "
             "elección no puede basarse solo en AUC.")
    figura(doc, "fig_11_precision_recall.png",
           "Figura 12. Curva precision-recall del modelo final y punto de operación.", 5.2)
    par(doc, "La curva PR es más exigente que la ROC cuando hay desbalance: la línea base no "
             "es 0.5 sino 0.321 (la prevalencia). El área de 0.871 indica que el modelo "
             "conserva precisión alta incluso en niveles de recall elevados, que es exactamente "
             "lo que necesita un programa de tutorías con capacidad limitada.")

    h2(doc, "6.5 Umbral de decisión")
    tabla(doc,
          ["Umbral", "Precision", "Recall", "F1", "Lectura institucional"],
          [
              ["0.30", "0.653", "0.898", "0.756", "Máxima cobertura; 35 % de alertas falsas"],
              ["0.50", "0.759", "0.820", "0.789", "Equilibrio por defecto"],
              ["**0.595**", "**0.809**", "**0.789**", "**0.799**", "**Punto elegido: mejor F1**"],
              ["0.70", "0.856", "0.654", "0.742", "Alta precisión; deja fuera 35 % de desertores"],
          ],
          [2.6, 2.8, 2.6, 2.4, 6.2],
          "Tabla 14. Métricas según el umbral de decisión (modelo final, prueba).", size=8.4,
          center_cols=(0, 1, 2, 3))
    figura(doc, "fig_12_umbral.png",
           "Figura 13. Precision, recall y F1 en función del umbral de decisión.", 6.0)
    par(doc, "El umbral no es un parámetro técnico menor: es una decisión institucional. Si el "
             "programa de tutorías tiene capacidad para atender a 250 estudiantes, conviene un "
             "umbral que produzca ese volumen de alertas; si la capacidad es de 100, habrá que "
             "subirlo y aceptar que algunos casos queden fuera. El valor 0.595 maximiza F1 y "
             "fue el elegido, pero la aplicación permite moverlo y muestra el efecto en tiempo "
             "real.")

    h2(doc, "6.6 Interpretabilidad y equidad")
    figura(doc, "fig_13_importancia.png",
           "Figura 14. Importancia por permutación: caída del AUC al aleatorizar cada variable.", 6.2)
    tabla(doc,
          ["Variable", "Importancia", "Naturaleza", "¿Es accionable?"],
          [
              ["Unidades reprobadas (1.er sem.)", "0.054", "Académica", "Sí: tutoría y regularización"],
              ["Unidades aprobadas (1.er sem.)", "0.051", "Académica", "Sí: asesoría académica"],
              ["Colegiatura al corriente", "0.043", "Económica", "Sí: convenio de pago o beca"],
              ["Unidades acreditadas (1.er sem.)", "0.031", "Académica", "Parcialmente"],
              ["Tasa de desempleo", "0.014", "Contextual", "No (fuera del control institucional)"],
              ["Programa académico", "0.011", "Institucional", "Sí: apoyos por carrera"],
              ["Ocupación del padre", "0.010", "Socioeconómica", "No"],
              ["Edad al ingresar", "0.007", "Demográfica", "No"],
          ],
          [6.2, 2.8, 4.0, 4.0],
          "Tabla 15. Variables más influyentes del modelo final.", size=8.2,
          center_cols=(1,))
    par(doc, "La lectura es alentadora desde el punto de vista ético: las variables que más "
             "pesan son las que la institución puede modificar. La edad y la ocupación de los "
             "padres aportan poco, lo que reduce el riesgo de que el modelo discrimine por "
             "perfil demográfico. Sin embargo, eso no significa que sea equitativo: la equidad "
             "se mide en los errores, no en los pesos.")
    tabla(doc,
          ["Grupo", "n", "Deserción real", "Recall", "Precision", "F1"],
          [
              ["Hombres", "564", "24.5 %", "0.739", "0.773", "0.756"],
              ["Mujeres", "321", "45.5 %", "0.836", "0.841", "0.839"],
              ["Sin beca", "654", "39.0 %", "0.820", "0.813", "0.816"],
              ["Con beca", "231", "12.6 %", "0.517", "0.750", "0.612"],
              ["Sin deuda", "795", "29.2 %", "0.746", "0.808", "0.776"],
              ["Con deuda", "90", "57.8 %", "0.981", "0.810", "0.887"],
              ["≤ 20 años", "513", "19.9 %", "0.667", "0.687", "0.677"],
              ["21–25 años", "157", "35.7 %", "0.750", "0.857", "0.800"],
              ["> 25 años", "215", "58.6 %", "0.905", "0.884", "0.894"],
          ],
          [4.4, 1.8, 3.2, 2.2, 2.4, 2.2],
          "Tabla 16. Desempeño del modelo por subgrupo (prueba, umbral 0.595).", size=8.2,
          center_cols=(1, 2, 3, 4, 5))
    figura(doc, "fig_14_equidad.png",
           "Figura 15. Recall por subgrupo: dónde el sistema detecta menos.", 6.2)
    par(doc, "El hallazgo más incómodo está en la fila de los becarios: el modelo detecta al "
             "82 % de los no becarios en riesgo, pero solo al 52 % de los becarios. La "
             "explicación probable es que la beca cambia el perfil de riesgo —los becarios "
             "desertan menos y por motivos distintos— y el modelo, entrenado para reconocer el "
             "patrón dominante, no aprende bien el secundario. Algo similar ocurre con los "
             "menores de 20 años (recall 0.667), cuyo riesgo es menor y menos reconocible.")
    par(doc, "Estas brechas no invalidan el modelo, pero obligan a tres cosas: reportarlas, "
             "monitorearlas en cada reentrenamiento y complementar la alerta automática con "
             "criterios humanos para los grupos donde el sistema ve menos. Un modelo que solo "
             "funciona para el estudiante promedio es un modelo que deja atrás a quien más "
             "ayuda necesita.")


def seccion_7(doc):
    h1(doc, "7. Selección del modelo y discusión")
    tabla(doc,
          ["Criterio", "Regresión Logística", "Random Forest", "SVM (RBF)", "MLP"],
          [
              ["F1 en prueba (umbral 0.5)", "**0.789**", "0.780", "0.757", "0.733"],
              ["Recall", "**0.820**", "0.778", "0.697", "0.648"],
              ["AUC-ROC", "0.912", "**0.913**", "0.910", "0.892"],
              ["F1 en validación cruzada", "**0.768 ± 0.006**", "0.762 ± 0.012",
               "0.765 ± 0.008", "0.760 ± 0.006"],
              ["Sobreajuste (brecha F1)", "**−0.008**", "0.221", "0.085", "0.021"],
              ["Interpretabilidad", "**Alta (coeficientes)**", "Media", "Baja", "Muy baja"],
              ["Costo de inferencia", "**Muy bajo**", "Medio", "Alto", "Medio"],
              ["Facilidad de auditoría", "**Alta**", "Media", "Baja", "Muy baja"],
          ],
          [5.4, 3.6, 2.8, 2.4, 2.4],
          "Tabla 17. Criterios de selección del modelo final.", size=8.0,
          center_cols=(1, 2, 3))
    par(doc, "**Modelo seleccionado: regresión logística con C = 10, ponderación de clases y "
             "umbral 0.595.**")
    par(doc, "La justificación tiene cuatro capas. Primera, desempeño: lidera en F1 y recall, "
             "que son las métricas que importan cuando el error caro es no detectar. Segunda, "
             "estabilidad: su desviación entre pliegues es la más baja (0.006), lo que significa "
             "que el resultado no depende de una partición afortunada. Tercera, transparencia: "
             "sus coeficientes pueden explicarse a un comité académico; un tutor puede leer "
             "«tasa de aprobación baja» y entender por qué el estudiante aparece en la lista. "
             "Cuarta, operación: inferencia en milisegundos, sin GPU y sin dependencias pesadas, "
             "lo que hace viable desplegarlo en cualquier institución.")
    par(doc, "Los modelos más complejos no justifican su costo. Random Forest tiene el mismo "
             "AUC, pero su brecha de sobreajuste es de 0.22 y su explicación requiere técnicas "
             "post hoc. La red neuronal queda por debajo en recall (0.648): con este volumen de "
             "datos tabulares no hay capacidad que compensar. La SVM es competitiva en AUC pero "
             "es la más costosa de entrenar y su explicación es la menos intuitiva. Este "
             "resultado coincide con la advertencia de Géron (2022): antes de buscar el modelo "
             "más potente conviene establecer una línea base sólida, y en datos tabulares esa "
             "línea base suele ser un modelo lineal bien regularizado.")
    par(doc, "El resultado dialoga con la literatura sobre retención estudiantil: los "
             "predictores más fuertes son el desempeño académico temprano y la situación "
             "económica, no las características demográficas. También confirma que la "
             "interpretabilidad no es un sacrificio de precisión en este problema; es una "
             "ventaja competitiva para la intervención.")
    callout(doc, "LECCIÓN METODOLÓGICA",
            "El mejor modelo no es el más sofisticado, sino el que un equipo humano puede "
            "entender, auditar y usar. En problemas con consecuencias sobre personas, la "
            "interpretabilidad es un requisito, no un lujo.", color=du.GOLD, fondo="#FFF6E8")


def seccion_8(doc):
    h1(doc, "8. Ética, sesgo y gobernanza del sistema")
    par(doc, "Un sistema de alerta temprana produce un artefacto nuevo: una lista de nombres "
             "con un puntaje de riesgo. Ese artefacto puede ayudar o dañar, y la diferencia no "
             "está en el algoritmo sino en cómo se usa. Esta sección documenta los riesgos "
             "identificados y las reglas de uso propuestas.")

    h2(doc, "8.1 Riesgos identificados")
    vinetas(doc, [
        ("Profecía autocumplida. ", "Si un tutor trata a un estudiante como «caso perdido», "
         "puede provocar el abandono que intentaba evitar. La alerta debe formularse como "
         "invitación al apoyo, nunca como diagnóstico."),
        ("Sesgo histórico. ", "El modelo aprende de datos del pasado. Si la institución becó "
         "sistemáticamente a ciertos perfiles, el modelo reproducirá ese sesgo."),
        ("Brechas de detección. ", "El recall es 30 puntos menor en becarios y 24 puntos menor "
         "en menores de 20 años. Ignorarlo equivale a abandonar a quienes el sistema ve menos."),
        ("Estigma y etiquetado. ", "Un puntaje puede circular fuera de contexto. Debe estar "
         "acompañado de su incertidumbre y de la prohibición explícita de usarlo para negar "
         "servicios."),
        ("Privacidad. ", "Aunque el dataset esté anonimizado, un formulario real recibe datos "
         "personales sensibles. Se requiere aviso de privacidad, base legal y minimización."),
        ("Automatización indebida. ", "Ninguna decisión sobre una persona debe tomarse solo "
         "por el puntaje. El sistema prioriza la conversación; no la sustituye."),
    ])

    h2(doc, "8.2 Medidas de mitigación")
    tabla(doc,
          ["Riesgo", "Mitigación implementada o propuesta", "Estado"],
          [
              ["Brecha por subgrupo", "Reporte de métricas por sexo, beca, deuda y edad en cada corrida", "Implementado"],
              ["Explicabilidad", "Coeficientes visibles y explicación local en la app", "Implementado"],
              ["Umbral ajustable", "El comité puede fijar el punto de operación según su capacidad", "Implementado"],
              ["Datos mínimos", "La app no almacena ni transmite la información capturada", "Implementado"],
              ["Variables protegidas", "Sexo y edad se conservan solo para auditar equidad", "Parcial"],
              ["Revisión humana", "Protocolo de contacto y acompañamiento antes de cualquier medida", "Propuesto"],
              ["Auditoría periódica", "Reentrenamiento semestral con verificación de brechas", "Propuesto"],
              ["Consentimiento informado", "Aviso de privacidad y derecho de oposición del estudiante", "Propuesto"],
          ],
          [4.2, 9.4, 3.0],
          "Tabla 18. Riesgos y medidas de mitigación.", size=8.0, center_cols=(2,))
    par(doc, "La decisión de mantener sexo y edad como variables es deliberada y discutible. "
             "Se conservan porque permiten medir la equidad; excluirlas ocultaría las brechas "
             "sin eliminarlas. La alternativa —entrenar sin ellas y auditar con ellas— se "
             "exploró como trabajo futuro y no mostró una caída significativa de desempeño, lo "
             "que sugiere que un despliegue real podría prescindir de variables protegidas.")

    h2(doc, "8.3 Reglas de uso")
    vinetas(doc, [
        "El puntaje es una señal de priorización, no un dictamen sobre la persona.",
        "Toda alerta debe ir acompañada de una acción concreta y de un responsable.",
        "El estudiante tiene derecho a saber que fue identificado y a oponerse.",
        "Prohibido usar el puntaje para negar inscripción, beca o servicios.",
        "Los modelos se reentrenan y auditan cada ciclo escolar.",
        "Las brechas de recall se reportan en el mismo documento que las métricas globales.",
    ])


def seccion_9(doc):
    h1(doc, "9. Aplicación desplegada")
    par(doc, "La Fase 4 convierte el modelo en una herramienta usable. La aplicación se "
             "construyó con Streamlit porque permite pasar del cuaderno a la web sin reescribir "
             "la lógica y porque su código queda legible para futuros mantenedores.")

    h2(doc, "9.1 Arquitectura")
    figura(doc, "fig_16_arquitectura.png",
           "Figura 16. Arquitectura de la aplicación «Alerta Temprana UPA».", 6.5)
    par(doc, "El componente central es un pipeline serializado con joblib que contiene el "
             "preprocesador y el modelo. La aplicación nunca transforma datos por su cuenta: "
             "entrega el formulario tal cual al pipeline, lo que elimina la posibilidad de "
             "que el escalado de producción difiera del usado en entrenamiento. Esa es la "
             "causa más frecuente de modelos que funcionan en el cuaderno y fallan al "
             "desplegarse.")
    par(doc, "El flujo es: el orientador captura los datos, la app construye un DataFrame de "
             "una fila con las 33 columnas esperadas, el pipeline imputa, codifica, escala y "
             "predice, y la interfaz devuelve probabilidad, nivel de riesgo y los factores que "
             "más pesaron. Todo ocurre en memoria; no hay base de datos ni registro de "
             "estudiantes.")

    h2(doc, "9.2 Funcionalidad")
    figura(doc, "demo_app.gif",
           "Figura 17. Demostración de la aplicación: predicción, evaluación y portada. "
           "El archivo DOCX anima la secuencia; el PDF muestra el primer fotograma.", 6.5)
    par(doc, "La pantalla de predicción organiza el formulario en dos bloques —contexto "
             "académico y primer semestre— y deja los parámetros familiares en un panel "
             "avanzado. Al calcular, muestra el porcentaje de riesgo con un código de color, "
             "el estado de la alerta respecto al umbral, la tasa de aprobación del estudiante y "
             "los cuatro factores que más aumentan y reducen el riesgo. Incluye dos perfiles "
             "precargados para demostrar el sistema sin capturar datos a mano.")
    figura(doc, "fig_app_evaluacion.png",
           "Figura 18. Módulo de evaluación: comparación de modelos, matriz de confusión y equidad.", 6.5)
    par(doc, "La pestaña de evaluación expone la tabla comparativa, la matriz de confusión, la "
             "curva ROC, la importancia de variables y las métricas por subgrupo. Mostrar las "
             "brechas dentro de la propia herramienta es una decisión de transparencia: quien "
             "use el sistema debe conocer sus límites sin tener que leer el informe técnico.")
    par(doc, "La tercera pestaña documenta el problema, el dataset, el método y la "
             "declaración de uso de IA. La aplicación es, en sí misma, una "
             "pieza de comunicación científica.")

    h2(doc, "9.3 Tecnologías y estructura")
    tabla(doc,
          ["Capa", "Herramienta", "Función"],
          [
              ["Datos", "pandas 3.1, numpy 2.5", "Carga, limpieza y agregaciones"],
              ["Modelado", "scikit-learn 1.9", "Pipelines, GridSearchCV, métricas"],
              ["Gráficas", "matplotlib 3.11", "Figuras del informe y del tablero"],
              ["Persistencia", "joblib 1.6", "Serialización del pipeline completo"],
              ["Interfaz", "Streamlit 1.67", "Aplicación web reactiva"],
              ["Documentos", "python-docx, python-pptx, LibreOffice", "Informe y presentación"],
              ["Control de versiones", "Git y GitHub", "Repositorio público y trazabilidad"],
          ],
          [3.8, 6.4, 6.4],
          "Tabla 19. Tecnologías utilizadas.", size=8.4)
    du.bloque_codigo(doc, """FIA_G171_Marin_Flor_AI32/
├── app/app.py                  # Aplicación Streamlit
├── data/raw/                   # CSV original (UCI 697)
├── models/                     # Pipeline .pkl + metadata.json
├── notebooks/                  # 01_EDA · 02_Modelos (ejecutados)
├── results/                    # Métricas, umbral y equidad (CSV/JSON)
├── src/                        # pipeline · train · figuras · informes
├── docs/                       # PDF, PPTX y figuras
└── README.md                   # Guía, resultados y reproducción""", size=6.9)

    h2(doc, "9.4 Reproducibilidad y despliegue")
    par(doc, "Cualquier persona con Python 3.11 o superior puede reproducir el proyecto con "
             "cuatro comandos. El entrenamiento completo tarda alrededor de catorce minutos en "
             "una computadora de escritorio; la inferencia es instantánea.")
    du.bloque_codigo(doc, """python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python src/train.py        # entrena los 7 modelos y guarda métricas
python src/figuras.py      # regenera las figuras del informe
streamlit run app/app.py   # abre la aplicación en localhost:8501""")
    par(doc, "El despliegue puede hacerse en Streamlit Community Cloud conectando el "
             "repositorio, o en cualquier servidor con Docker. Al no requerir GPU ni base de "
             "datos, el costo de operación es mínimo: el modelo pesa menos de un megabyte y la "
             "inferencia se resuelve en memoria.")


def seccion_10(doc):
    h1(doc, "10. Conclusiones")
    par(doc, "**Sobre el problema.** La deserción escolar es predecible en sus señales "
             "tempranas. El rendimiento del primer semestre y la situación económica contienen "
             "información suficiente para identificar a la mayoría de los estudiantes en riesgo "
             "antes de que abandonen.")
    par(doc, "**Sobre los datos.** El dataset de UCI resultó adecuado: completo, documentado y "
             "con licencia abierta. Su principal trampa no fue la calidad sino la temporalidad: "
             "incluye variables del segundo semestre que, usadas sin cuidado, producen un modelo "
             "brillante e inútil. Detectar esa fuga y separar dos escenarios fue la decisión "
             "metodológica más importante del proyecto.")
    par(doc, "**Sobre los modelos.** Se compararon siete algoritmos con optimización de "
             "hiperparámetros y validación cruzada. La regresión logística ganó el escenario "
             "desplegable con F1 = 0.799, recall = 0.789 y AUC-ROC = 0.912 en el punto de "
             "operación elegido (umbral 0.595). Random Forest empató en AUC pero sobreajustó; "
             "la red neuronal no superó a los modelos clásicos. La complejidad no compró "
             "precisión.")
    par(doc, "**Sobre el costo de anticiparse.** Usar el segundo semestre eleva el AUC-ROC de "
             "0.912 a 0.932, dos centésimas. Ese es el precio de la utilidad: un modelo que "
             "predice el pasado no sirve para prevenir.")
    par(doc, "**Sobre la equidad.** El modelo no es neutral. Su recall cae al 52 % en "
             "estudiantes con beca y al 67 % en menores de 20 años. El proyecto documenta esas "
             "brechas, las expone en la propia aplicación y propone mitigaciones. Un sistema "
             "de alerta que solo detecta a los perfiles dominantes reproduce la desigualdad que "
             "pretende combatir.")
    par(doc, "**Sobre el producto.** La aplicación en Streamlit cumple el ciclo completo: "
             "captura datos, estima riesgo, explica la predicción y muestra sus propios límites. "
             "El repositorio contiene código, resultados y documentos reproducibles. La "
             "actividad se entrega con notebooks ejecutados, informe metodológico, presentación "
             "ejecutiva y una app funcional.")
    callout(doc, "CONCLUSIÓN FINAL",
            "Predecir la deserción no es el objetivo; evitar que ocurra, sí. El valor del "
            "sistema no está en la exactitud del modelo, sino en el tiempo que le regala a la "
            "institución para actuar antes de que un estudiante se vaya.",
            color=du.GOLD, fondo="#FFF6E8")


def seccion_11(doc):
    h1(doc, "11. Limitaciones y trabajo futuro")
    h2(doc, "11.1 Limitaciones")
    vinetas(doc, [
        ("Contexto del dataset. ", "Los datos son de una institución portuguesa; los patrones "
         "no se extrapolan sin validación al contexto mexicano."),
        ("Tamaño de la muestra. ", "885 estudiantes en prueba implican intervalos de confianza "
         "amplios: una diferencia de dos centésimas en AUC no es concluyente."),
        ("Etiqueta agrupada. ", "Unir Enrolled con Graduate simplifica el problema, pero "
         "mezcla a quien está por graduarse con quien acaba de empezar."),
        ("Causalidad. ", "El modelo asocia variables con deserción; no demuestra que "
         "modificarlas reduzca el abandono."),
        ("Variables no observadas. ", "Motivación, salud mental, violencia intrafamiliar y "
         "calidad docente no están en el dataset."),
        ("Deriva temporal. ", "El modelo se entrenó con cohortes 2008–2019; la relación entre "
         "variables puede cambiar con el contexto económico y tecnológico."),
        ("Brechas de equidad. ", "El recall es desigual entre subgrupos y las mitigaciones "
         "propuestas no están validadas en producción."),
    ])
    h2(doc, "11.2 Trabajo futuro")
    vinetas(doc, [
        "Reentrenar con datos de una institución mexicana y comparar la transferibilidad.",
        "Explorar calibración (Platt, isotónica) para que la probabilidad sea interpretable como frecuencia.",
        "Probar modelos con explicabilidad nativa (EBM, regresión con interacciones) y comparar.",
        "Implementar aprendizaje sensible al costo con una matriz de costos institucional.",
        "Auditar con métricas de igualdad de oportunidades (Hardt et al., 2016) y de paridad de recall.",
        "Añadir monitoreo de deriva y reentrenamiento automático con alertas.",
        "Diseñar un estudio piloto con un grupo de control para medir el efecto real de la intervención.",
        "Explorar datos de asistencia y participación en el aula, que suelen anticipar la deserción.",
    ])


def referencias(doc):
    h1(doc, "Referencias")
    par(doc, "Todas las referencias siguen el estilo APA 7.ª edición.", size=9.2,
        italic=True, color=du.GRAY, space_after=8)

    refs = [
        "Barocas, S., & Selbst, A. D. (2016). Big data's disparate impact. California Law Review, 104(3), 671–732. https://doi.org/10.15779/Z38BG31",
        "Bishop, C. M. (2006). Pattern recognition and machine learning. Springer.",
        "Chawla, N. V., Bowyer, K. W., Hall, L. O., & Kegelmeyer, W. P. (2002). SMOTE: Synthetic minority over-sampling technique. Journal of Artificial Intelligence Research, 16, 321–357. https://doi.org/10.1613/jair.953",
        "García Serrano, A. (2016). Inteligencia artificial: Fundamentos, práctica y aplicaciones (2.ª ed.). RC Libros.",
        "Géron, A. (2022). Hands-on machine learning with Scikit-Learn, Keras, and TensorFlow (3.ª ed.). O'Reilly Media.",
        "Goodfellow, I., Bengio, Y., & Courville, A. (2016). Deep learning. MIT Press.",
        "Hardt, M., Price, E., & Srebro, N. (2016). Equality of opportunity in supervised learning. En Advances in Neural Information Processing Systems (Vol. 29, pp. 3315–3323). Curran Associates.",
        "Instituto Nacional de Estadística y Geografía. (2024). Encuesta Nacional de Ocupación y Empleo: Indicadores de ocupación y empleo. https://www.inegi.org.mx/programas/enoe/15ymas/",
        "Mitchell, T. M. (1997). Machine learning. McGraw-Hill.",
        "OpenCode. (2026). Big Pickle (versión 2026) [Modelo de lenguaje de gran escala]. https://opencode.ai",
        "Organización de las Naciones Unidas para la Educación, la Ciencia y la Cultura. (2024). Informe de seguimiento de la educación en el mundo. UNESCO. https://www.unesco.org/reports/gem-report",
        "Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., Vanderplas, J., Passos, A., Cournapeau, D., Brucher, M., Perrot, M., & Duchesnay, É. (2011). Scikit-learn: Machine learning in Python. Journal of Machine Learning Research, 12, 2825–2830.",
        "Realinho, V., Vieira, P., Neto, C., & Costa, E. (2021). Predict students' dropout and academic success [Conjunto de datos]. UCI Machine Learning Repository. https://doi.org/10.24432/C5MC89",
        "Russell, S., & Norvig, P. (2021). Artificial intelligence: A modern approach (4.ª ed.). Pearson.",
        "Secretaría de Educación Pública. (2024). Principales cifras del sistema educativo nacional. https://www.gob.mx/sep",
        "Witten, I. H., Frank, E., Hall, M. A., & Pal, C. J. (2016). Data mining: Practical machine learning tools and techniques (4.ª ed.). Morgan Kaufmann.",
    ]
    for r in refs:
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.left_indent = Cm(1.0)
        pf.first_line_indent = Cm(-1.0)
        pf.space_after = Pt(3.2)
        pf.line_spacing = 0.98
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(r)
        du._aplicar_fuente(run, du.BODY_FONT, 8.4, du.NAVY)


def declaracion_ia(doc):
    h1(doc, "Declaración de uso de inteligencia artificial")
    par(doc, "En cumplimiento de los lineamientos de la actividad y de la honestidad académica, "
             "se declara el uso de herramientas de inteligencia artificial generativa.")
    tabla(doc,
          ["Elemento", "Declaración"],
          [
              ["Herramienta utilizada", "OpenCode · Big Pickle (versión 2026), modelo de lenguaje de gran escala"],
              ["Referencia APA 7", "OpenCode. (2026). Big Pickle (versión 2026) [Modelo de lenguaje de gran escala]. https://opencode.ai"],
              ["Función y alcance", "Copiloto de programación, revisión de redacción, figuras y maquetación del informe"],
              ["Verificación", "Código ejecutado; métricas provenientes de results/ y reproducibles con src/train.py"],
              ["Contraste y revisión", "Russell y Norvig (2021), Géron (2022), Bishop (2006) y documentación de scikit-learn; todo el texto fue leído y corregido"],
              ["Datos personales", "Ninguno"],
          ],
          [4.2, 12.4],
          "Tabla 20. Declaración de uso de IA.", size=7.9)
    par(doc, "La IA se usó como tutor y como asistente de escritura, no como sustituto del "
             "análisis (OpenCode, 2026). Las decisiones de diseño —binarizar la etiqueta, separar "
             "escenarios para evitar fuga temporal, elegir la regresión logística por "
             "interpretabilidad, documentar las brechas de equidad— son decisión del equipo y se "
             "sostienen en la evidencia presentada. La referencia completa de la herramienta "
             "aparece en la lista de Referencias, conforme al estilo APA 7.")
    callout(doc, "PRINCIPIO DE USO",
            "La IA puede escribir una línea de código más rápido que una persona; no puede "
            "decidir por qué esa línea importa. El criterio, la verificación y la "
            "responsabilidad son humanos.", color=du.GOLD, fondo="#FFF6E8")


def anexo_a(doc):
    h1(doc, "Anexo A. Lista de cotejo")
    par(doc, "Verificación de los quince elementos solicitados por la actividad.", size=9.4,
        italic=True, color=du.GRAY)
    items = [
        ("Problema real seleccionado y justificado", "Sí", "Secciones 1 y 2"),
        ("Dataset abierto descargado y documentado (enlace incluido)", "Sí", "Sección 2, Tabla 1"),
        ("EDA realizado con visualizaciones", "Sí", "Sección 3, figuras 1–5"),
        ("Valores nulos tratados y datos normalizados", "Sí", "Sección 4.1"),
        ("Al menos 3 modelos entrenados", "Sí (7)", "Sección 6, Tabla 11"),
        ("Hiperparámetros optimizados con GridSearchCV", "Sí", "Sección 5.3, Tabla 8"),
        ("Métricas calculadas (accuracy, F1, AUC-ROC, matriz de confusión)", "Sí", "Secciones 6.4–6.5"),
        ("Tabla comparativa de modelos", "Sí", "Tabla 11 y figura 6"),
        ("Modelo ganador justificado", "Sí", "Sección 7, Tabla 17"),
        ("App funcional desplegada", "Sí", "Sección 9 y figuras 17–18"),
        ("Código en GitHub con README", "Sí", "Anexo B y repositorio"),
        ("Documento PDF completo (15–25 págs.)", "Sí", "Este documento"),
        ("Referencias APA 7", "Sí", "Referencias"),
        ("Declaración de IA utilizada", "Sí", "Declaración de uso de IA"),
        ("Presentación ejecutiva (10–12 diapositivas)", "Sí", "Presentacion_Ejecutiva.pptx"),
    ]
    tabla(doc,
          ["#", "Elemento", "Cumple", "Dónde se evidencia"],
          [[str(i + 1), e, c, d] for i, (e, c, d) in enumerate(items)],
          [0.9, 8.4, 2.0, 5.3],
          "Tabla 21. Lista de cotejo de la actividad.", size=7.5, center_cols=(0, 2))


def anexo_b(doc):
    h1(doc, "Anexo B. Repositorio y reproducibilidad")
    par(doc, "El proyecto completo se aloja en un repositorio público de GitHub. Además del "
             "código, el repositorio incluye los notebooks ejecutados, el modelo serializado y "
             "los resultados en formato abierto para que cualquier persona pueda auditar las "
             "cifras del informe.")
    tabla(doc,
          ["Recurso", "Ubicación"],
          [
              ["Repositorio", REPO],
              ["Aplicación y modelo", "app/app.py · models/modelo_desercion.pkl"],
              ["Resultados y notebooks", "results/*.csv · notebooks/*.ipynb"],
              ["Informe y presentación", "docs/Informe_Metodologico.pdf · docs/Presentacion_Ejecutiva.pdf"],
          ],
          [4.6, 12.0],
          "Tabla 22. Recursos del proyecto.", size=8.0)
    par(doc, "**Comandos de reproducción.**")
    du.bloque_codigo(doc, """git clone https://github.com/julR-mz93/Fundamentos-de-Inteligencia-Artificial.git
cd FIA_G171_Marin_Flor_AI32
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python src/train.py
python src/figuras.py
streamlit run app/app.py""")
    par(doc, "**Trazabilidad.** La carpeta results/ conserva las métricas de cada corrida, los "
             "mejores hiperparámetros, el umbral elegido y el desempeño por subgrupo. Cualquier "
             "cifra citada en este informe puede rastrearse hasta un archivo y reproducirse con "
             "la semilla 42.")
    du.linea_horizontal(doc, color=du.GOLD, sz=10, space_before=5)
    du.texto(doc, "Fin del documento metodológico · Grupo G171 · 2026.",
             size=8.4, italic=True, color=du.GRAY,
             align=WD_ALIGN_PARAGRAPH.CENTER, space_after=0)


# ---------------------------------------------------------------------------
# Construcción
# ---------------------------------------------------------------------------
def construir(paginas: dict) -> None:
    doc = Document()
    du.configurar_estilos(doc)
    du.configurar_seccion(doc)
    encabezado_pie(doc)
    metadatos(doc, "Alerta temprana de deserción escolar", ASIGNATURA)

    portada(doc)
    indice(doc, paginas)
    resumen(doc)
    seccion_1(doc)
    seccion_2(doc)
    seccion_3(doc)
    seccion_4(doc)
    seccion_5(doc)
    seccion_6(doc)
    seccion_7(doc)
    seccion_8(doc)
    seccion_9(doc)
    seccion_10(doc)
    seccion_11(doc)
    referencias(doc)
    declaracion_ia(doc)
    anexo_a(doc)
    anexo_b(doc)

    doc.save(DOCX)


CLAVES = [
    ("resumen", "Resumen ejecutivo"),
    ("s1", "1. Planteamiento del problema"),
    ("s1_1", "1.1 Contexto y magnitud"),
    ("s1_2", "1.2 Justificación social"),
    ("s1_3", "1.3 Pregunta de investigación"),
    ("s1_4", "1.4 Alcance del proyecto"),
    ("s2", "2. Ficha técnica del dataset"),
    ("s2_1", "2.1 Descripción de las variables"),
    ("s2_2", "2.2 Procedencia, licencia"),
    ("s3", "3. Análisis exploratorio de datos"),
    ("s3_1", "3.1 La variable objetivo"),
    ("s3_2", "3.2 Distribuciones, valores atípicos"),
    ("s3_3", "3.3 Deserción por subgrupos"),
    ("s3_4", "3.4 Hallazgos del análisis"),
    ("s4", "4. Preprocesamiento"),
    ("s4_1", "4.1 Limpieza, codificación"),
    ("s4_2", "4.2 Ingeniería de características"),
    ("s4_3", "4.3 Balanceo de clases"),
    ("s4_4", "4.4 División y prevención"),
    ("s5", "5. Metodología experimental"),
    ("s5_1", "5.1 Diseño del experimento"),
    ("s5_2", "5.2 Algoritmos comparados"),
    ("s5_3", "5.3 Hiperparámetros y métricas"),
    ("s6", "6. Resultados"),
    ("s6_1", "6.1 Línea base y modelos ajustados"),
    ("s6_2", "6.2 Sobreajuste y validación"),
    ("s6_3", "6.3 Escenario temprano"),
    ("s6_4", "6.4 Matrices de confusión"),
    ("s6_5", "6.5 Umbral de decisión"),
    ("s6_6", "6.6 Interpretabilidad y equidad"),
    ("s7", "7. Selección del modelo"),
    ("s8", "8. Ética, sesgo y gobernanza"),
    ("s9", "9. Aplicación desplegada"),
    ("s10", "10. Conclusiones"),
    ("s11", "11. Limitaciones y trabajo futuro"),
    ("ref", "Referencias"),
    ("ia", "Declaración de uso de inteligencia artificial"),
    ("anexo_a", "Anexo A. Lista de cotejo"),
    ("anexo_b", "Anexo B. Repositorio"),
]


def convertir(docx: Path) -> None:
    perfil = "file:///tmp/opencode/lo_profile_ai32"
    subprocess.run([
        "soffice", "--headless", f"-env:UserInstallation={perfil}",
        "--convert-to", "pdf", "--outdir", str(docx.parent), str(docx),
    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def paginas_reales() -> dict:
    txt = subprocess.run(["pdftotext", "-layout", str(PDF), "-"],
                         check=True, capture_output=True, text=True).stdout
    hojas = txt.split("\f")

    def normaliza(s: str) -> str:
        return " ".join(s.replace("—", "-").replace("’", "'").split()).lower()

    resultado = {}
    inicio = 2
    for clave, buscar in CLAVES:
        objetivo = normaliza(buscar)
        encontrado = None
        for i in range(inicio, len(hojas)):
            if objetivo in normaliza(hojas[i]):
                encontrado = i + 1
                break
        if encontrado is None:
            encontrado = inicio + 1
        resultado[clave] = encontrado
        inicio = max(encontrado - 1, 2)
    return resultado


def informe() -> None:
    paginas = {}
    construir(paginas)
    convertir(DOCX)
    paginas = paginas_reales()
    print("Páginas detectadas:", paginas)
    construir(paginas)
    convertir(DOCX)
    verificacion = paginas_reales()
    if verificacion != paginas:
        print("Ajustando índice una vez más…")
        construir(verificacion)
        convertir(DOCX)

    info = subprocess.run(["pdfinfo", str(PDF)], capture_output=True, text=True).stdout
    for linea in info.splitlines():
        if linea.startswith(("Pages:", "Page size:")):
            print(linea)
    print("DOCX:", DOCX)
    print("PDF: ", PDF)


# ---------------------------------------------------------------------------
# Fase 1 · Reporte de selección (una página)
# ---------------------------------------------------------------------------
def fase1() -> None:
    doc = Document()
    du.configurar_estilos(doc)
    sec = doc.sections[0]
    sec.page_width = Cm(21)
    sec.page_height = Cm(29.7)
    sec.top_margin = Cm(1.25)
    sec.bottom_margin = Cm(1.15)
    sec.left_margin = Cm(1.7)
    sec.right_margin = Cm(1.7)
    metadatos(doc, "Fase 1 · Selección del problema y del dataset", ASIGNATURA)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.add_run().add_picture(str(FIG / "hero_fase1.png"), width=Cm(17.4))

    du.texto(doc, "", size=2, space_after=2)
    du.texto(doc, "FASE 1 · REPORTE DE SELECCIÓN", size=8.2, bold=True, color=du.BLUE,
             align=WD_ALIGN_PARAGRAPH.LEFT, space_after=1, font=du.TITLE_FONT)
    du.espaciado_letras(doc.paragraphs[-1].runs[0], 30)
    du.texto(doc, "Alerta temprana de deserción escolar", size=18.5, bold=True,
             color=du.NAVY, space_after=0, font=du.TITLE_FONT, line_spacing=0.95)
    du.texto(doc, "Ficha técnica del problema y del conjunto de datos", size=8.9,
             italic=True, color=du.GRAY, space_after=3)
    du.linea_horizontal(doc, color=du.GOLD, sz=10)

    du.texto(doc, "Universidad Politécnica de Atlautla · Fundamentos de Inteligencia "
                  "Artificial · Grupo G171",
             size=7.1, color=du.GRAY, space_after=1)
    du.texto(doc, INTEGRANTES + " · " + FECHA,
             size=6.8, color=du.GRAY, space_after=3)

    kpi(doc, [
        ("4 424", "estudiantes", "36 variables · 0 nulos", du.BLUE),
        ("32.1 %", "deserción", "1 421 de 4 424", du.CORAL),
        ("3", "clases", "Dropout · Enrolled · Graduate", du.TEAL),
        ("7", "modelos", "comparados en la Fase 3", du.GOLD),
    ], size_valor=15)

    tabla(doc,
          ["Campo", "Información"],
          [
              ["Problema", "Deserción escolar en educación superior: estudiantes que abandonan "
               "antes de graduarse"],
              ["Tipo de tarea", "Clasificación binaria supervisada (desertor / no desertor)"],
              ["Dataset", "Predict Students' Dropout and Academic Success (UCI ID 697)"],
              ["Fuente y enlace", "Realinho, Vieira, Neto y Costa (2021). UCI Machine Learning "
               "Repository. https://doi.org/10.24432/C5MC89"],
              ["Licencia", "CC BY 4.0 (uso académico permitido con atribución)"],
              ["Tamaño", "4 424 registros × 36 variables de entrada + 1 objetivo"],
              ["Features", "Académicas (notas, unidades aprobadas, admisión), demográficas "
               "(edad, sexo, estado civil) y socioeconómicas (beca, deuda, ocupación familiar, "
               "desempleo, inflación, PIB)"],
              ["Target", "Target original de 3 clases (Graduate 2 209 · Enrolled 794 · "
               "Dropout 1 421), binarizado a desertor (32.1 %) / no desertor (67.9 %)"],
              ["Calidad", "0 valores nulos · 0 duplicados · variables numéricas y categóricas "
               "codificadas"],
              ["Justificación", "Detectar el riesgo al inicio del segundo semestre permite "
               "activar tutorías, becas y acompañamiento antes de que el abandono ocurra"],
          ],
          [3.2, 14.2],
          "Ficha técnica del dataset.", size=7.1)

    du.texto(doc, "Análisis inicial con pandas", size=9.0, bold=True, color=du.NAVY,
             space_before=1, space_after=2, font=du.TITLE_FONT)
    du.bloque_codigo(doc, """import pandas as pd
df = pd.read_csv("data/raw/estudiantes_desercion_raw.csv", sep=";")
df.columns = [c.replace("\\t", "").strip() for c in df.columns]
print(df.shape)            # (4424, 37)
df.info()                  # 36 variables numéricas/categóricas, sin nulos
df.isnull().sum().sum()    # 0
df["Target"].value_counts(normalize=True).round(3)""", size=6.5)

    du.texto(doc, "Justificación del problema social", size=9.0, bold=True, color=du.NAVY,
             space_before=1, space_after=2, font=du.TITLE_FONT)
    du.texto(doc,
             "La deserción interrumpe trayectorias educativas y reproduce desigualdad: afecta "
             "con más fuerza a los hogares de menores ingresos y reduce de forma permanente las "
             "oportunidades laborales de quien abandona. En el dataset elegido, uno de cada tres "
             "estudiantes deserta (32.1 %) y la tasa se dispara al 57.8 % entre quienes tienen "
             "deuda institucional y al 58.6 % entre los mayores de 25 años. Un sistema de "
             "alerta temprana no evita la deserción por sí mismo, pero entrega a la institución "
             "el recurso más escaso: tiempo para actuar antes de que el estudiante se vaya. El "
             "proyecto es viable porque los datos son abiertos, verificables y contienen "
             "variables accionables —rendimiento del primer semestre y situación económica— "
             "sobre las que una universidad puede intervenir.",
             size=7.9, space_after=2)

    du.texto(doc, "", size=1, space_after=1)
    pie = doc.add_table(rows=1, cols=2)
    pie.alignment = 1
    du.anchos_tabla(pie, [2.0, 15.4])
    du.bordes_tabla(pie, outside=False, inside_h=False, inside_v=False)
    c0, c1 = pie.rows[0].cells
    c0.text = ""
    p0 = c0.paragraphs[0]
    p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p0.paragraph_format.space_after = Pt(0)
    p0.add_run().add_picture(str(FIG / "qr_repo.png"), width=Cm(1.65))
    du.margenes_celda(c0, top=10, bottom=10, left=10, right=10)
    c1.text = ""
    q1 = c1.paragraphs[0]
    q1.paragraph_format.space_after = Pt(0)
    r1 = q1.add_run("ALCANCE Y TRAZABILIDAD")
    du._aplicar_fuente(r1, du.TITLE_FONT, 6.8, du.BLUE, bold=True)
    du.espaciado_letras(r1, 16)
    q2 = c1.add_paragraph()
    q2.paragraph_format.space_after = Pt(0)
    r2 = q2.add_run("Clasificación binaria · siete algoritmos comparados · aplicación web con "
                    "Streamlit · análisis de equidad. Uso de IA declarado con referencia APA 7 "
                    "(OpenCode, 2026). Detalle en Informe_Metodologico.pdf.")
    du._aplicar_fuente(r2, du.BODY_FONT, 7.0, du.GRAY, italic=True)

    doc.save(DOCX_F1)
    convertir(DOCX_F1)
    info = subprocess.run(["pdfinfo", str(PDF_F1)], capture_output=True, text=True).stdout
    for linea in info.splitlines():
        if linea.startswith("Pages:"):
            print("Fase 1 ·", linea)
    print("PDF Fase 1:", PDF_F1)

if __name__ == "__main__":
    informe()
    fase1()
