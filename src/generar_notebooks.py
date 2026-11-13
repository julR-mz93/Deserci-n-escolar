#!/usr/bin/env python3
"""
Construye y ejecuta los notebooks del proyecto.

  notebooks/01_EDA_y_Preprocesamiento.ipynb
  notebooks/02_Modelos_y_Comparacion.ipynb

Los notebooks se ejecutan con nbclient para que queden con salidas y figuras
visibles, tal como se entregan.
"""
from __future__ import annotations

from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient

BASE = Path(__file__).resolve().parent.parent
NB = BASE / "notebooks"
NB.mkdir(exist_ok=True)

PRE = """\
import sys, json, warnings
from pathlib import Path
sys.path.insert(0, str(Path.cwd().parent / "src"))
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pipeline as P

pd.set_option("display.width", 120)
pd.set_option("display.max_columns", 40)
plt.rcParams.update({"figure.dpi": 110, "axes.grid": True, "grid.alpha": 0.25,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titleweight": "bold", "figure.facecolor": "white"})
AZUL, ROJO, VERDE = "#1F6FB2", "#C0392B", "#2E8B57"
print("Entorno listo · scikit-learn", __import__("sklearn").__version__)
"""


def md(t):
    return nbf.v4.new_markdown_cell(t.strip("\n"))


def code(t):
    return nbf.v4.new_code_cell(t.strip("\n"))


def ejecutar(nb, nombre):
    ruta = NB / nombre
    nbf.write(nb, ruta)
    cliente = NotebookClient(nb, timeout=1200, kernel_name="python3",
                             resources={"metadata": {"path": str(NB)}})
    cliente.execute()
    nbf.write(nb, ruta)
    print("ejecutado:", ruta)


# ===========================================================================
# Notebook 1 · EDA y preprocesamiento
# ===========================================================================
def notebook_eda():
    c = []
    c.append(md("""
# Fase 2 · Análisis exploratorio y preprocesamiento
### Proyecto: alerta temprana de deserción escolar

**Asignatura:** Fundamentos de Inteligencia Artificial · **Unidad 3**
**Actividad 3.2.1 — Aprendizaje automático supervisado**
Universidad Politécnica de Atlautla · Grupo G171

---
Este cuaderno documenta el recorrido completo de los datos: desde el archivo original
hasta las matrices de entrenamiento y prueba. Cada decisión se justifica y se acompaña
del código que la implementa, de modo que cualquier persona pueda reproducir el resultado.

**Fuente del dataset:** *Predict Students' Dropout and Academic Success* (Realinho et al., 2021),
UCI Machine Learning Repository, ID 697. 4 424 registros y 36 variables de estudiantes de
una institución portuguesa de educación superior.
"""))
    c.append(code(PRE))
    c.append(md("""
## 1. Carga y primera inspección

El archivo original usa punto y coma como separador y contiene una tabulación al final del
nombre de una columna (`Daytime/evening attendance`), un defecto frecuente en los CSV
exportados desde hojas de cálculo. `pipeline.cargar_datos()` lo corrige y elimina duplicados.
"""))
    c.append(code("""
df = P.cargar_datos()
print("Dimensiones:", df.shape)
df.head(3)
"""))
    c.append(md("### 1.1 Tipos, valores nulos y duplicados"))
    c.append(code("""
df.info()
"""))
    c.append(code("""
resumen = pd.DataFrame({
    "nulos": df.isnull().sum(),
    "porcentaje_nulos": (df.isnull().mean() * 100).round(2),
    "valores_unicos": df.nunique(),
    "tipo": df.dtypes.astype(str),
})
print("Duplicados exactos:", df.duplicated().sum())
print("Celdas nulas:", int(df.isnull().sum().sum()))
resumen.head(12)
"""))
    c.append(md("""
**Lectura.** El dataset no contiene valores nulos ni duplicados: es un conjunto ya curado.
Esto no elimina la necesidad de imputar, porque la aplicación real recibirá formularios
incompletos; por eso el preprocesador incluye imputación por mediana y por moda.

### 1.2 Descripción estadística
"""))
    c.append(code("""
df.describe().T[["mean", "std", "min", "50%", "max"]].round(2).head(14)
"""))
    c.append(md("""
## 2. La variable objetivo

La etiqueta original tiene tres clases: `Graduate`, `Enrolled` y `Dropout`. El proyecto
resuelve una **clasificación binaria**: interesa distinguir a quien **deserta** de quien
**permanece** (graduado o aún inscrito). Las clases se agrupan porque el objetivo operativo
es activar una alerta, no emitir un dictamen definitivo sobre el futuro del estudiante.
"""))
    c.append(code("""
print(df["Target"].value_counts())
print()
print("Tasa de deserción:", round((df["Target"] == "Dropout").mean() * 100, 2), "%")

df["desertor"] = (df["Target"] == "Dropout").astype(int)
conteo = df["desertor"].value_counts().sort_index()
fig, axes = plt.subplots(1, 2, figsize=(10, 3.4))
axes[0].bar(["Graduado", "Inscrito", "Desertor"],
            df["Target"].value_counts()[["Graduate", "Enrolled", "Dropout"]],
            color=[VERDE, "#E9C46A", ROJO])
axes[0].set_title("Etiqueta original (3 clases)"); axes[0].set_ylabel("Estudiantes")
axes[1].bar(["No desertor", "Desertor"], conteo.values, color=[AZUL, ROJO])
for i, v in enumerate(conteo.values):
    axes[1].text(i, v + 40, f"{v} ({v/len(df)*100:.1f} %)", ha="center", fontweight="bold")
axes[1].set_title("Etiqueta binaria del proyecto"); axes[1].set_ylabel("Estudiantes")
plt.tight_layout(); plt.show()

print("Desbalance aproximado 1 :", round(conteo[0] / conteo[1], 2))
"""))
    c.append(md("""
El desbalance es moderado (32 % de deserción). No es un caso extremo, pero obliga a usar
métricas distintas de la exactitud y a ponderar las clases durante el entrenamiento; de lo
contrario el modelo podría acertar 68 % simplemente diciendo «nadie deserta», que es
exactamente el error que un sistema de alerta no puede cometer.

## 3. Análisis exploratorio

### 3.1 Distribuciones por clase
"""))
    c.append(code("""
vars_eda = ["Age at enrollment", "Admission grade",
            "Curricular units 1st sem (grade)", "Curricular units 2nd sem (grade)"]
fig, axes = plt.subplots(2, 2, figsize=(10.5, 6))
for ax, col in zip(axes.ravel(), vars_eda):
    for v, color, et in [(0, AZUL, "No desertor"), (1, ROJO, "Desertor")]:
        ax.hist(df.loc[df.desertor == v, col], bins=22, alpha=0.6, color=color,
                label=et, density=True)
    ax.set_title(col, fontsize=10); ax.set_ylabel("Densidad")
axes[0, 0].legend()
plt.tight_layout(); plt.show()
"""))
    c.append(md("""
Las distribuciones de calificaciones separan con claridad a los dos grupos: quien deserta
concentra notas bajas y muchas asignaturas no aprobadas. La edad, en cambio, se solapa
bastante, lo que sugiere un efecto más débil y no lineal.
"""))
    c.append(md("### 3.2 Diagramas de caja y valores atípicos"))
    c.append(code("""
fig, axes = plt.subplots(1, 4, figsize=(11, 3.3))
for ax, col in zip(axes, ["Age at enrollment", "Admission grade",
                          "Curricular units 1st sem (grade)",
                          "Curricular units 2nd sem (approved)"]):
    ax.boxplot([df.loc[df.desertor == v, col] for v in (0, 1)],
               tick_labels=["No", "Sí"], patch_artist=True,
               boxprops=dict(facecolor="#BFD7EA"), medianprops=dict(color="#0F2A44"))
    ax.set_title(col, fontsize=8.6)
plt.tight_layout(); plt.show()

def contar_atipicos(s):
    q1, q3 = s.quantile([0.25, 0.75]); iqr = q3 - q1
    return int(((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum())

for col in ["Age at enrollment", "Admission grade", "Curricular units 1st sem (grade)"]:
    print(f"{col:42s} atípicos: {contar_atipicos(df[col]):4d} "
          f"({contar_atipicos(df[col])/len(df)*100:.1f} %)")
"""))
    c.append(md("""
**Decisión.** Los valores atípicos se conservan. No son errores de captura: una edad de
50 años o una nota de admisión extrema son casos reales de la población estudiantil.
Eliminarlos reduciría la capacidad del modelo para atender justamente a los perfiles menos
frecuentes. La estandarización y los modelos basados en árboles limitan su influencia.
"""))
    c.append(md("### 3.3 Correlaciones"))
    c.append(code("""
num = ["Age at enrollment", "Admission grade", "Curricular units 1st sem (grade)",
       "Curricular units 2nd sem (grade)", "Curricular units 1st sem (approved)",
       "Curricular units 2nd sem (approved)", "Unemployment rate", "Inflation rate",
       "GDP", "desertor"]
corr = df[num].corr()
fig, ax = plt.subplots(figsize=(7.6, 6))
im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(len(num)), [c[:22] for c in num], rotation=55, ha="right", fontsize=7)
ax.set_yticks(range(len(num)), [c[:22] for c in num], fontsize=7)
for i in range(len(num)):
    for j in range(len(num)):
        ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", fontsize=6)
plt.colorbar(im, shrink=0.8, label="Pearson"); ax.grid(False)
plt.tight_layout(); plt.show()

print(corr["desertor"].drop("desertor").sort_values().round(3))
"""))
    c.append(md("""
La correlación más fuerte con la deserción es negativa y proviene de las unidades
aprobadas y las calificaciones. Las variables macroeconómicas (desempleo, inflación, PIB)
apenas correlacionan de forma lineal, aunque pueden aportar en interacciones que un modelo
no lineal sí captura. La correlación no implica causalidad: el expediente refleja también
condiciones sociales previas.

### 3.4 Tasa de deserción por subgrupo
"""))
    c.append(code("""
fig, ax = plt.subplots(figsize=(8.4, 3.6))
etiquetas, valores = [], []
for col, mapa, nombre in [
    ("Scholarship holder", {0: "Sin beca", 1: "Con beca"}, "Beca"),
    ("Debtor", {0: "Sin deuda", 1: "Con deuda"}, "Deuda"),
    ("Gender", {0: "Hombre", 1: "Mujer"}, "Sexo"),
    ("Tuition fees up to date", {0: "Adeudo", 1: "Al corriente"}, "Colegiatura")]:
    for v, lab in mapa.items():
        etiquetas.append(f"{nombre}: {lab}")
        valores.append(df.loc[df[col] == v, "desertor"].mean() * 100)
ax.barh(etiquetas[::-1], valores[::-1], color=AZUL)
for i, v in enumerate(valores[::-1]):
    ax.text(v + 0.7, i, f"{v:.1f} %", va="center", fontsize=8)
ax.axvline(df.desertor.mean() * 100, color=ROJO, ls="--", lw=1)
ax.set_xlabel("Tasa de deserción (%)"); plt.tight_layout(); plt.show()
"""))
    c.append(md("""
La beca y el estado de la colegiatura separan con nitidez: quienes tienen deuda o no están
al corriente presentan tasas de deserción muy superiores. Este hallazgo alimenta la sección
de equidad: el modelo debe vigilar que esas condiciones no se conviertan en un estigma.
"""))
    c.append(md("""
## 4. Ingeniería de características

Se añaden variables derivadas con interpretación educativa directa. Todas se calculan con
división protegida para evitar indeterminaciones cuando un estudiante no inscribió unidades.
"""))
    c.append(code("""
df = P.enriquecer(df)
nuevas = ["tasa_aprobacion_1s", "tasa_aprobacion_2s", "tasa_aprobacion_global",
          "promedio_notas", "delta_aprobacion", "total_aprobadas", "senal_economica"]
df[["desertor"] + nuevas].describe().T.round(3)
"""))
    c.append(code("""
print("Tasa media de aprobación por grupo:")
print(df.groupby("desertor")[["tasa_aprobacion_1s", "tasa_aprobacion_2s",
                              "promedio_notas", "delta_aprobacion"]].mean().round(3))

print("\\nSeñal económica (deuda o colegiatura vencida) y deserción:")
print(pd.crosstab(df["senal_economica"], df["desertor"], normalize="index").round(3))
"""))
    c.append(md("""
## 5. Preprocesamiento

Se aplican tres transformaciones dentro de un `ColumnTransformer`, para que viajen
**dentro del pipeline** y se ajusten solo con los datos de entrenamiento (evita fuga de
información):

1. **Imputación**: mediana en variables numéricas, moda en categóricas.
2. **One-Hot Encoding** en las ocho variables nominales, con `min_frequency=0.01` para
   agrupar categorías raras y contener la dimensionalidad.
3. **Estandarización** (`StandardScaler`) en numéricas y binarias, indispensable para KNN,
   SVM y redes neuronales, e inocua para los árboles.
"""))
    c.append(code("""
esc_temp = P.conjunto_columnas("temprano")
esc_comp = P.conjunto_columnas("completo")
print("Escenario A (temprano):", len(esc_temp["numericas"]),
      "numéricas +", len(esc_temp["nominales"]), "nominales +",
      len(esc_temp["binarias"]), "binarias")
print("Escenario B (completo):", len(esc_comp["numericas"]),
      "numéricas +", len(esc_comp["nominales"]), "nominales +",
      len(esc_comp["binarias"]), "binarias")

prep = P.construir_preprocesador("temprano")
Xtr, Xte, ytr, yte = P.dividir(df, "temprano")
prep.fit(Xtr)
Xtr_t = prep.transform(Xtr)
print("Matriz transformada:", Xtr_t.shape)
nombres = prep.get_feature_names_out()
print("Primeras 12 columnas:", list(nombres[:12]))
"""))
    c.append(md("""
### 5.1 Dos escenarios para evitar fuga de información

Un sistema de alerta temprana debe decidir **antes** de que el estudiante abandone. Si se
usan las notas del segundo semestre, el modelo predice el pasado: cuando esos datos existen,
la deserción ya ocurrió o está consumada. Por eso el proyecto entrena dos escenarios:

| Escenario | Variables | Uso real |
|---|---|---|
| **A · Temprano** | Inscripción, situación socioeconómica y primer semestre | Desplegable al iniciar el segundo semestre |
| **B · Completo** | A + segundo semestre | Diagnóstico y análisis, no despliegue |

El costo de anticiparse se mide en la Fase 3: la diferencia de desempeño entre A y B es el
precio de la utilidad.
"""))
    c.append(md("""
## 6. Balanceo de clases

Se comparan tres estrategias con validación cruzada de 5 pliegues sobre el conjunto de
entrenamiento: sin balanceo, ponderación de clases (`class_weight='balanced'`) y
sobremuestreo aleatorio del grupo minoritario aplicado **solo dentro de cada pliegue**.
"""))
    c.append(code("""
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.base import clone
import pipeline as P

def resamplear(X, y, semilla):
    rng = np.random.RandomState(semilla)
    idx_min = np.where(y == 1)[0]
    idx_may = np.where(y == 0)[0]
    extra = rng.choice(idx_min, size=len(idx_may) - len(idx_min), replace=True)
    idx = np.concatenate([idx_may, idx_min, extra])
    return X.iloc[idx], y.iloc[idx]

skf = StratifiedKFold(5, shuffle=True, random_state=P.RANDOM_STATE)
resultados = {"Sin balanceo": [], "class_weight": [], "Sobremuestreo": []}

for tr, va in skf.split(Xtr, ytr):
    X_a, X_b = Xtr.iloc[tr], Xtr.iloc[va]
    y_a, y_b = ytr.iloc[tr], ytr.iloc[va]
    for nombre, peso in [("Sin balanceo", None), ("class_weight", "balanced")]:
        m = P.armar_pipeline(LogisticRegression(max_iter=2000, class_weight=peso), "temprano")
        m.fit(X_a, y_a)
        resultados[nombre].append(P.metricas(y_b, m.predict(X_b), None)["recall"])
    Xs, ys = resamplear(X_a, y_a, 42)
    m = P.armar_pipeline(LogisticRegression(max_iter=2000), "temprano")
    m.fit(Xs, ys)
    resultados["Sobremuestreo"].append(P.metricas(y_b, m.predict(X_b), None)["recall"])

tabla_bal = pd.DataFrame({k: {"recall_medio": np.mean(v), "recall_std": np.std(v)}
                          for k, v in resultados.items()}).T.round(4)
print(tabla_bal)
"""))
    c.append(md("""
**Decisión.** Se adopta `class_weight='balanced'` y **no** SMOTE ni sobremuestreo sintético.
Razones: (a) el sobremuestreo aleatorio no mejora el recall de forma significativa frente a
la ponderación; (b) SMOTE interpola vecinos en un espacio con variables *one-hot* y códigos
nominales, donde el «punto medio» entre dos categorías no tiene significado; (c) la
ponderación no altera los datos, conserva la distribución original y es más fácil de auditar.
El umbral de decisión se ajusta en la Fase 3 como segunda palanca para favorecer el recall.
"""))
    c.append(md("""
## 7. División entrenamiento / prueba

Se reserva 20 % para prueba, estratificado por clase y con semilla fija. La misma partición
se usa en todos los modelos y en la aplicación, de modo que las métricas sean comparables.
"""))
    c.append(code("""
print(f"Entrenamiento: {Xtr.shape[0]} filas ({1-0.2:.0%}) · prueba: {Xte.shape[0]} filas (20 %)")
print("Deserción en train:", round(ytr.mean(), 4), "| en test:", round(yte.mean(), 4))
print("¿Se solapan índices?", len(set(Xtr.index) & set(Xte.index)) == 0)
df.to_csv(P.PROCESSED, index=False)
print("Guardado:", P.PROCESSED.relative_to(P.BASE))
"""))
    c.append(md("""
## 8. Conclusiones de la Fase 2

1. El dataset está limpio (sin nulos ni duplicados), pero se mantiene un preprocesador con
   imputación porque la app recibirá datos incompletos.
2. La variable objetivo se binariza: **desertor = 1** frente a **graduado o inscrito = 0**.
3. Las variables con mayor señal son las del rendimiento académico, seguidas de la situación
   económica (beca, deuda, colegiatura).
4. Se añadieron siete variables derivadas que resumen el avance curricular y la presión
   económica.
5. El balanceo elegido es la ponderación de clases, justificada frente al sobremuestreo.
6. El preprocesamiento vive dentro del pipeline: se ajusta solo con entrenamiento y evita
   fuga de información.
7. Se definen dos escenarios; el desplegable es el **temprano** (sin segundo semestre).
"""))
    nb = nbf.v4.new_notebook(cells=c)
    nb.metadata.update({
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
        "title": "Fase 2 · EDA y preprocesamiento",
    })
    ejecutar(nb, "01_EDA_y_Preprocesamiento.ipynb")


# ===========================================================================
# Notebook 2 · Modelos
# ===========================================================================
def notebook_modelos():
    c = []
    c.append(md("""
# Fase 3 · Entrenamiento y comparación de modelos
### Proyecto: alerta temprana de deserción escolar

**Asignatura:** Fundamentos de Inteligencia Artificial · Actividad 3.2.1
Universidad Politécnica de Atlautla · Grupo G171

---
Se comparan **siete algoritmos** de aprendizaje supervisado en dos escenarios:

* **A · Temprano** — inscripción + primer semestre (desplegable, sin fuga de información).
* **B · Completo** — añade segundo semestre (techo de desempeño, no desplegable).

Para cada modelo se reportan hiperparámetros por defecto y optimizados con `GridSearchCV`,
métricas en prueba, validación cruzada de 5 pliegues, matriz de confusión, curvas ROC/PR,
brecha de sobreajuste y desempeño por subgrupos.

> El cuaderno consume los resultados de `src/train.py` (≈ 14 minutos de cómputo) y
> reconstruye localmente los modelos ganadores para las gráficas. Así se evita repetir la
> búsqueda completa en cada ejecución sin perder trazabilidad: los CSV, el modelo y los
> metadatos quedan versionados en `results/` y `models/`.
"""))
    c.append(code(PRE))
    c.append(code("""
from sklearn.metrics import classification_report, confusion_matrix, roc_curve, auc
from sklearn.model_selection import GridSearchCV
from sklearn.inspection import permutation_importance

RES = Path.cwd().parent / "results"
df = P.enriquecer(P.cargar_datos())
base = pd.read_csv(RES / "metricas_baseline.csv")
ajust = pd.read_csv(RES / "metricas_ajustadas.csv")
cv = pd.read_csv(RES / "cv_resumen.csv")
mejores = json.loads((RES / "mejores_parametros.json").read_text())
umbrales = json.loads((RES / "umbrales.json").read_text())
print("Resultados cargados:", len(ajust), "experimentos")
"""))
    c.append(md("""
## 1. Diseño experimental

| Elemento | Definición |
|---|---|
| Partición | 80 % entrenamiento / 20 % prueba, estratificada, `random_state=42` |
| Búsqueda | `GridSearchCV`, 5 pliegues, métrica de selección **F1** |
| Métricas | accuracy, precision, recall, F1, AUC-ROC, PR-AUC |
| Control de sobreajuste | comparación F1 train vs test + validación cruzada |
| Criterio de selección | F1, con el recall como desempate (un falso negativo es un estudiante perdido) |

Se elige F1 y no accuracy porque las clases están desbalanceadas y porque, en este problema,
los dos tipos de error tienen costos distintos: un **falso negativo** deja sin apoyo a un
estudiante en riesgo; un **falso positivo** genera una tutoría innecesaria, costosa pero
reversible.
"""))
    c.append(md("## 2. Línea base: hiperparámetros por defecto"))
    c.append(code("""
tabla_base = base.pivot_table(index="modelo", columns="escenario",
                              values=["f1", "recall", "roc_auc"]).round(3)
tabla_base
"""))
    c.append(md("""
La línea base ya es alta en los modelos lineales y de conjunto. El árbol individual y KNN
quedan rezagados: el primero sobreajusta, el segundo sufre con la maldición de la
dimensionalidad al mezclar decenas de variables *one-hot*.
"""))
    c.append(md("## 3. Optimización de hiperparámetros"))
    c.append(code("""
mejores_df = pd.DataFrame([
    {"escenario": k.split("|")[0], "modelo": k.split("|")[1],
     "hiperparámetros": json.dumps(v, ensure_ascii=False)}
    for k, v in mejores.items()
])
display(mejores_df.sort_values(["escenario", "modelo"]))
"""))
    c.append(md("""
### 3.1 Ejemplo ejecutable de la búsqueda

La siguiente celda reproduce la búsqueda de KNN en el escenario temprano. Es la misma
mecánica que `src/train.py` aplica a los siete modelos.
"""))
    c.append(code("""
Xtr, Xte, ytr, yte = P.dividir(df, "temprano")
spec = P.catalogo_modelos("temprano")["KNN"]
busqueda = GridSearchCV(P.armar_pipeline(spec["modelo"], "temprano"),
                        spec["rejilla"], scoring="f1", cv=5, n_jobs=-1)
busqueda.fit(Xtr, ytr)
print("Mejores hiperparámetros:", busqueda.best_params_)
print("F1 medio en validación cruzada:", round(busqueda.best_score_, 4))
"""))
    c.append(md("## 4. Comparación de los modelos ajustados (escenario temprano)"))
    c.append(code("""
cols = ["modelo", "accuracy", "precision", "recall", "f1", "roc_auc", "pr_auc",
        "f1_train", "brecha_f1"]
t = ajust[ajust.escenario == "temprano"][cols].sort_values("f1", ascending=False)
display(t.reset_index(drop=True).style.background_gradient(
    subset=["f1", "recall", "roc_auc"], cmap="Blues").format(precision=4))
"""))
    c.append(md("""
**Lectura.** La regresión logística encabeza la tabla: F1 ≈ 0.79, recall ≈ 0.82 y
AUC-ROC ≈ 0.91. Random Forest y SVM quedan a menos de un punto. La red neuronal (MLP) no
supera a los modelos clásicos: con 3 500 casos y variables mayormente tabulares, la
capacidad extra de la red se traduce en sobreajuste, no en precisión.

La **brecha F1 train-test** confirma el diagnóstico: el árbol individual y el MLP presentan
las diferencias más grandes; la regresión logística, regularizada, la más pequeña.
"""))
    c.append(code("""
fig, axes = plt.subplots(1, 2, figsize=(11.5, 4))
orden = t.sort_values("f1")
axes[0].barh(orden.modelo, orden.f1, color="#1F6FB2")
for i, v in enumerate(orden.f1):
    axes[0].text(v + 0.005, i, f"{v:.3f}", va="center", fontsize=8)
axes[0].set_xlim(0.6, 0.86); axes[0].set_title("F1 en prueba · escenario temprano")
axes[0].set_xlabel("F1")

axes[1].barh(orden.modelo, orden.brecha_f1, color="#D9782D")
axes[1].set_title("Brecha de sobreajuste (F1 train − F1 test)")
axes[1].set_xlabel("Diferencia de F1")
plt.tight_layout(); plt.show()
"""))
    c.append(md("## 5. Validación cruzada: ¿el resultado es estable?"))
    c.append(code("""
cvt = cv[cv.escenario == "temprano"][["modelo", "f1_media", "f1_std", "recall_media",
                                     "recall_std", "roc_auc_media", "roc_auc_std"]]
display(cvt.sort_values("f1_media", ascending=False).round(4).reset_index(drop=True))
"""))
    c.append(md("""
La desviación estándar entre pliegues es pequeña (< 0.03 en los modelos líderes), lo que
indica que el orden no depende de una partición afortunada. La conclusión es robusta.
"""))
    c.append(md("## 6. ¿Cuánto cuesta anticiparse? Escenario A frente a B"))
    c.append(code("""
comp = ajust.groupby("escenario")[["f1", "recall", "roc_auc"]].max().round(3)
comp["modelo"] = ajust.loc[ajust.groupby("escenario")["f1"].idxmax(), "modelo"].values
display(comp)
print("Costo de anticiparse (Δ AUC-ROC):",
      round(comp.loc["completo", "roc_auc"] - comp.loc["temprano", "roc_auc"], 3))
"""))
    c.append(md("""
Usar el segundo semestre eleva el AUC-ROC apenas unas centésimas, pero convierte el modelo
en un diagnóstico tardío. El sistema desplegable se queda con el escenario **temprano**:
detecta a tiempo y conserva un desempeño alto.
"""))
    c.append(md("## 7. Modelo ganador: matrices de confusión y curvas"))
    c.append(code("""
def modelo_ajustado(nombre, escenario="temprano"):
    spec = P.catalogo_modelos(escenario)[nombre]
    m = P.armar_pipeline(spec["modelo"], escenario)
    m.set_params(**{f"modelo__{k}": v
                    for k, v in mejores[f"{escenario}|{nombre}"].items()})
    return m.fit(Xtr, ytr)

elegidos = ["Regresión Logística", "Random Forest", "SVM (RBF)", "Árbol de Decisión"]
modelos = {n: modelo_ajustado(n) for n in elegidos}
u = umbrales["umbral_f1_optimo"]

fig, axes = plt.subplots(1, 4, figsize=(12, 3.1))
for ax, (nombre, m) in zip(axes, modelos.items()):
    pred = (m.predict_proba(Xte)[:, 1] >= u).astype(int)
    cm = confusion_matrix(yte, pred)
    ax.imshow(cm, cmap="Blues")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, cm[i, j], ha="center", va="center", fontsize=13,
                    fontweight="bold", color="white" if cm[i, j] > cm.max()/2 else "#0F2A44")
    ax.set_xticks([0, 1], ["No", "Sí"]); ax.set_yticks([0, 1], ["No", "Sí"])
    ax.set_title(nombre, fontsize=8.6); ax.set_xlabel("Predicción"); ax.grid(False)
axes[0].set_ylabel("Realidad")
plt.tight_layout(); plt.show()
"""))
    c.append(code("""
fig, ax = plt.subplots(figsize=(6, 5))
for (nombre, m) in modelos.items():
    fpr, tpr, _ = roc_curve(yte, m.predict_proba(Xte)[:, 1])
    ax.plot(fpr, tpr, lw=1.8, label=f"{nombre} ({auc(fpr, tpr):.3f})")
ax.plot([0, 1], [0, 1], "--", color="#6B7A8A", label="Azar (0.500)")
ax.set_xlabel("Falsos positivos"); ax.set_ylabel("Verdaderos positivos")
ax.set_title("Curvas ROC · escenario temprano"); ax.legend(fontsize=7.5, loc="lower right")
plt.tight_layout(); plt.show()
"""))
    c.append(md("""
La matriz de confusión se lee así: las filas son la realidad y las columnas la predicción.
En el modelo ganador, la esquina inferior izquierda concentra los **falsos negativos** —
estudiantes que desertaron y no fueron detectados—, el error más costoso del sistema. El
umbral se ajusta precisamente para reducirlo.
"""))
    c.append(md("## 8. Ajuste del umbral de decisión"))
    c.append(code("""
final = modelos["Regresión Logística"]
prob = final.predict_proba(Xte)[:, 1]

filas = []
for u_ in [0.30, 0.40, 0.50, 0.595, 0.70]:
    m = P.metricas(yte, (prob >= u_).astype(int), None)
    filas.append({"umbral": u_, **{k: round(v, 4) for k, v in m.items()}})
display(pd.DataFrame(filas))

print("Umbral elegido:", umbrales["umbral_f1_optimo"])
print(json.dumps(umbrales, indent=2, ensure_ascii=False))
"""))
    c.append(md("""
Bajar el umbral aumenta el recall (se detectan más desertores) a costa de precisión. El valor
elegido maximiza F1 y mantiene un recall cercano a 0.79, un equilibrio razonable para un
programa de tutorías con recursos limitados. **El umbral no es un detalle técnico: es una
decisión institucional** que debería acordarse con el área de bienestar estudiantil.
"""))
    c.append(md("## 9. ¿Qué variables pesan? Interpretabilidad"))
    c.append(code("""
r = permutation_importance(final, Xte, yte, n_repeats=10, random_state=42,
                           scoring="roc_auc", n_jobs=-1)
imp = pd.DataFrame({"variable": Xte.columns,
                    "importancia": r.importances_mean,
                    "std": r.importances_std}).sort_values("importancia", ascending=False)
display(imp.head(12).round(4).reset_index(drop=True))

top = imp.head(12).iloc[::-1]
fig, ax = plt.subplots(figsize=(7.8, 4.6))
ax.barh(top.variable, top.importancia, xerr=top["std"], color="#1F6FB2")
ax.set_title("Importancia por permutación (caída del AUC-ROC)")
plt.tight_layout(); plt.show()
"""))
    c.append(md("""
La tasa de aprobación del primer semestre, las unidades aprobadas y la nota de admisión
dominan la decisión. La señal económica (deuda o colegiatura vencida) aparece entre las
primeras posiciones. Todas son variables **accionables**: sobre ellas puede intervenir la
institución. La edad y el estado civil aportan poco, lo que reduce el riesgo de
discriminación por perfil demográfico.
"""))
    c.append(md("## 10. Equidad algorítmica"))
    c.append(code("""
eq = pd.read_csv(RES / "equidad.csv")
display(eq.round(3))
print("Brecha de recall entre sexos:",
      round(abs(eq[eq.variable == "Sexo"].recall.max() -
                eq[eq.variable == "Sexo"].recall.min()), 3))
"""))
    c.append(md("""
**Hallazgo.** El modelo detecta a los hombres con algo más de recall que a las mujeres; la
brecha es pequeña, pero existe y debe monitorearse. También se observa que el recall es más
alto entre quienes tienen beca, porque su perfil de riesgo es más reconocible.

**Medidas adoptadas:** (1) reportar métricas por subgrupo en cada reentrenamiento;
(2) excluir variables protegidas del conjunto de características y verificar que el
desempeño no se deteriore; (3) usar el puntaje como disparador de una conversación humana,
nunca como sanción o negación de servicios.
"""))
    c.append(md("## 11. Selección y justificación del modelo final"))
    c.append(md("""
| Criterio | Regresión Logística | Random Forest | SVM (RBF) | MLP |
|---|---|---|---|---|
| F1 en prueba | **0.789** | 0.779 | 0.757 | 0.733 |
| Recall | **0.820** | 0.778 | 0.697 | 0.648 |
| AUC-ROC | 0.912 | **0.913** | 0.910 | 0.891 |
| Interpretabilidad | **Alta** (coeficientes) | Media | Baja | Muy baja |
| Costo de inferencia | **Muy bajo** | Medio | Alto | Medio |
| Estabilidad entre pliegues | **Alta** | Alta | Media | Baja |

**Modelo ganador: Regresión Logística** (`C=10`, `class_weight='balanced'`, umbral 0.595).

Justificación: iguala o supera a los modelos más complejos en F1 y recall —la métrica que
importa cuando un falso negativo significa un estudiante perdido—, es la más estable entre
pliegues, la más barata de ejecutar y la única cuyos coeficientes pueden explicarse a un
comité académico sin caja negra. En un problema con consecuencias sobre personas, la
interpretabilidad no es un adorno: es un requisito ético y legal.
"""))
    c.append(md("## 12. Persistencia del modelo y conclusiones"))
    c.append(code("""
import joblib
modelo = joblib.load(P.BASE / "models" / "modelo_desercion.pkl")
meta = json.loads((P.BASE / "models" / "metadata.json").read_text())
print("Pipeline cargado:", type(modelo).__name__)
print("Umbral de operación:", meta["umbral"])
print("Métricas en prueba:", meta["metricas_test"])
print("Variables de entrada:", len(meta["columnas"]))
"""))
    c.append(md("""
### Conclusiones de la Fase 3

1. Se entrenaron y compararon **siete algoritmos** en dos escenarios, con optimización de
   hiperparámetros y validación cruzada.
2. La regresión logística gana el escenario desplegable (F1 = 0.799, recall = 0.789,
   AUC-ROC = 0.912 con el umbral ajustado).
3. La complejidad no garantiza mejor desempeño: MLP y árbol individual sobreajustan con este
   volumen de datos tabulares.
4. Anticiparse al segundo semestre cuesta alrededor de una centésima de AUC-ROC; es un precio
   aceptable frente al valor de detectar a tiempo.
5. El umbral se optimizó en 0.595 para equilibrar recall y precisión.
6. Las variables más influyentes son académicas y económicas, y son accionables.
7. Se identificó una brecha de recall por sexo que se reporta y se monitorea.
8. El pipeline completo se serializa en `models/modelo_desercion.pkl` y se documenta en
   `models/metadata.json`; la app de la Fase 4 consume ambos archivos.
"""))
    nb = nbf.v4.new_notebook(cells=c)
    nb.metadata.update({
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
        "title": "Fase 3 · Modelos y comparación",
    })
    ejecutar(nb, "02_Modelos_y_Comparacion.ipynb")


if __name__ == "__main__":
    notebook_eda()
    notebook_modelos()
