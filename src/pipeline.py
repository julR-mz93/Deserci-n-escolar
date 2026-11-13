#!/usr/bin/env python3
"""
Núcleo reproducible del proyecto «Alerta temprana de deserción escolar».

Contiene la carga del dataset, la ingeniería de características, la construcción
de los preprocesadores y el catálogo de modelos. Lo reutilizan los notebooks,
el script de entrenamiento y la aplicación Streamlit, de modo que existe una
sola fuente de verdad para la transformación de los datos.

Dataset: Predict Students' Dropout and Academic Success (UCI ID 697).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "data" / "raw" / "estudiantes_desercion_raw.csv"
PROCESSED = BASE / "data" / "processed" / "estudiantes_procesado.csv"
RANDOM_STATE = 42

# ---------------------------------------------------------------------------
# Columnas del dataset original
# ---------------------------------------------------------------------------
# Variables conocidas al momento de la inscripción
COLS_INSCRIPCION = [
    "Marital status", "Application mode", "Application order", "Course",
    "Daytime/evening attendance", "Previous qualification",
    "Previous qualification (grade)", "Nacionality", "Mother's qualification",
    "Father's qualification", "Mother's occupation", "Father's occupation",
    "Admission grade", "Displaced", "Educational special needs", "Debtor",
    "Tuition fees up to date", "Gender", "Scholarship holder",
    "Age at enrollment", "International", "Unemployment rate",
    "Inflation rate", "GDP",
]

# Variables del primer semestre (disponibles al iniciar el segundo)
COLS_1ER_SEM = [
    "Curricular units 1st sem (credited)", "Curricular units 1st sem (enrolled)",
    "Curricular units 1st sem (evaluations)", "Curricular units 1st sem (approved)",
    "Curricular units 1st sem (grade)", "Curricular units 1st sem (without evaluations)",
]

# Variables del segundo semestre (solo se conocen al final del ciclo)
COLS_2DO_SEM = [
    "Curricular units 2nd sem (credited)", "Curricular units 2nd sem (enrolled)",
    "Curricular units 2nd sem (evaluations)", "Curricular units 2nd sem (approved)",
    "Curricular units 2nd sem (grade)", "Curricular units 2nd sem (without evaluations)",
]

BINARIAS = [
    "Daytime/evening attendance", "Displaced", "Educational special needs",
    "Debtor", "Tuition fees up to date", "Gender", "Scholarship holder",
    "International",
]

# Categóricas nominales de baja/media cardinalidad -> One-Hot
NOMINALES = [
    "Marital status", "Application mode", "Course", "Previous qualification",
    "Mother's qualification", "Father's qualification", "Mother's occupation",
    "Father's occupation",
]

NUMERICAS_BASE = [
    "Application order", "Previous qualification (grade)", "Admission grade",
    "Age at enrollment", "Unemployment rate", "Inflation rate", "GDP",
]

# Características derivadas (feature engineering)
FE_1ER_SEM = ["tasa_aprobacion_1s", "evaluaciones_por_inscrita_1s",
              "reprobadas_1s", "sin_evaluar_1s"]
FE_2DO_SEM = ["tasa_aprobacion_2s", "evaluaciones_por_inscrita_2s",
              "reprobadas_2s", "sin_evaluar_2s"]
FE_GLOBAL = ["tasa_aprobacion_global", "promedio_notas", "delta_aprobacion",
             "total_aprobadas", "total_inscritas", "senal_economica"]


def cargar_datos(ruta: Path | str = RAW) -> pd.DataFrame:
    """Carga el CSV original (separado por ';') y normaliza los nombres."""
    df = pd.read_csv(ruta, sep=";")
    df.columns = [c.replace("\t", "").strip() for c in df.columns]
    df = df.drop_duplicates().reset_index(drop=True)
    return df


def _tasa(aprobadas: pd.Series, inscritas: pd.Series) -> pd.Series:
    return np.where(inscritas > 0, aprobadas / inscritas.replace(0, np.nan), 0.0)


def enriquecer(df: pd.DataFrame) -> pd.DataFrame:
    """Añade variables derivadas interpretables y la etiqueta binaria."""
    d = df.copy()
    insc1 = d["Curricular units 1st sem (enrolled)"]
    apro1 = d["Curricular units 1st sem (approved)"]
    eval1 = d["Curricular units 1st sem (evaluations)"]
    sin1 = d["Curricular units 1st sem (without evaluations)"]
    insc2 = d["Curricular units 2nd sem (enrolled)"]
    apro2 = d["Curricular units 2nd sem (approved)"]
    eval2 = d["Curricular units 2nd sem (evaluations)"]
    sin2 = d["Curricular units 2nd sem (without evaluations)"]

    d["tasa_aprobacion_1s"] = _tasa(apro1, insc1)
    d["evaluaciones_por_inscrita_1s"] = _tasa(eval1, insc1)
    d["reprobadas_1s"] = (insc1 - apro1).clip(lower=0)
    d["sin_evaluar_1s"] = sin1

    d["tasa_aprobacion_2s"] = _tasa(apro2, insc2)
    d["evaluaciones_por_inscrita_2s"] = _tasa(eval2, insc2)
    d["reprobadas_2s"] = (insc2 - apro2).clip(lower=0)
    d["sin_evaluar_2s"] = sin2

    total_insc = insc1 + insc2
    total_aprob = apro1 + apro2
    d["tasa_aprobacion_global"] = _tasa(total_aprob, total_insc)
    d["promedio_notas"] = (
        d["Curricular units 1st sem (grade)"] + d["Curricular units 2nd sem (grade)"]
    ) / 2
    d["delta_aprobacion"] = d["tasa_aprobacion_2s"] - d["tasa_aprobacion_1s"]
    d["total_aprobadas"] = total_aprob
    d["total_inscritas"] = total_insc
    d["senal_economica"] = (
        (d["Debtor"] == 1) | (d["Tuition fees up to date"] == 0)
    ).astype(int)

    d["desertor"] = (d["Target"] == "Dropout").astype(int)
    return d


def conjunto_columnas(escenario: str = "completo") -> dict:
    """
    Devuelve la especificación de columnas de cada escenario.

    escenario='temprano'  -> solo inscripción + 1er semestre (desplegable)
    escenario='completo'  -> añade 2º semestre (diagnóstico, mayor AUC)
    """
    num = NUMERICAS_BASE + COLS_1ER_SEM + FE_1ER_SEM
    if escenario == "completo":
        num = num + COLS_2DO_SEM + FE_2DO_SEM + FE_GLOBAL
    num = [c for c in dict.fromkeys(num) if c not in NOMINALES and c not in BINARIAS]
    nominales = NOMINALES + (["Nacionality"] if escenario == "completo" else [])
    binarias = BINARIAS
    return {"numericas": num, "nominales": nominales, "binarias": binarias}


def construir_preprocesador(escenario: str = "completo") -> ColumnTransformer:
    cols = conjunto_columnas(escenario)
    numericas = cols["numericas"] + cols["binarias"]

    num_pipe = Pipeline([
        ("imputar", SimpleImputer(strategy="median")),
        ("escalar", StandardScaler()),
    ])
    cat_pipe = Pipeline([
        ("imputar", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", min_frequency=0.01,
                                 sparse_output=False)),
    ])
    return ColumnTransformer(
        transformers=[
            ("num", num_pipe, numericas),
            ("cat", cat_pipe, cols["nominales"]),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def catalogo_modelos(escenario: str = "completo") -> dict:
    """Modelos y rejillas de hiperparámetros para GridSearchCV."""
    return {
        "Regresión Logística": {
            "modelo": LogisticRegression(max_iter=2000, class_weight="balanced",
                                         random_state=RANDOM_STATE),
            "rejilla": {"modelo__C": [0.01, 0.1, 1, 10]},
        },
        "KNN": {
            "modelo": KNeighborsClassifier(),
            "rejilla": {"modelo__n_neighbors": [5, 11, 21, 31],
                        "modelo__weights": ["uniform", "distance"]},
        },
        "SVM (RBF)": {
            "modelo": SVC(probability=True, class_weight="balanced",
                          random_state=RANDOM_STATE),
            "rejilla": {"modelo__C": [0.5, 1, 5], "modelo__gamma": ["scale", 0.01]},
        },
        "Árbol de Decisión": {
            "modelo": DecisionTreeClassifier(class_weight="balanced",
                                             random_state=RANDOM_STATE),
            "rejilla": {"modelo__max_depth": [4, 6, 8, None],
                        "modelo__min_samples_leaf": [5, 20]},
        },
        "Random Forest": {
            "modelo": RandomForestClassifier(n_estimators=300, class_weight="balanced",
                                             random_state=RANDOM_STATE, n_jobs=-1),
            "rejilla": {"modelo__max_depth": [8, 14, None],
                        "modelo__min_samples_leaf": [1, 5]},
        },
        "Red Neuronal (MLP)": {
            "modelo": MLPClassifier(max_iter=800, early_stopping=True,
                                    random_state=RANDOM_STATE),
            "rejilla": {"modelo__hidden_layer_sizes": [(32,), (64, 32)],
                        "modelo__alpha": [1e-4, 1e-2]},
        },
        "Naive Bayes": {
            "modelo": GaussianNB(),
            "rejilla": {"modelo__var_smoothing": [1e-9, 1e-7]},
        },
    }


def armar_pipeline(clasificador, escenario: str = "completo") -> Pipeline:
    return Pipeline([
        ("prep", construir_preprocesador(escenario)),
        ("modelo", clasificador),
    ])


def dividir(df: pd.DataFrame, escenario: str = "completo",
            test_size: float = 0.20):
    cols = conjunto_columnas(escenario)
    X = df[cols["numericas"] + cols["nominales"] + cols["binarias"]]
    y = df["desertor"]
    return train_test_split(X, y, test_size=test_size,
                            random_state=RANDOM_STATE, stratify=y)


def columnas_entrada(escenario: str = "temprano") -> list[str]:
    """Orden exacto de columnas crudas que espera el pipeline."""
    cols = conjunto_columnas(escenario)
    return cols["numericas"] + cols["nominales"] + cols["binarias"]


def valores_por_defecto(df: pd.DataFrame, escenario: str = "temprano") -> dict:
    """Valores típicos (mediana/moda) para precargar el formulario de la app."""
    cols = columnas_entrada(escenario)
    salida = {}
    for c in cols:
        serie = df[c]
        if serie.dtype.kind in "if":
            salida[c] = float(serie.median())
        else:
            salida[c] = int(serie.mode().iloc[0])
    return salida


def metricas(y_true, y_pred, y_prob=None) -> dict:
    from sklearn.metrics import (accuracy_score, average_precision_score,
                                 f1_score, precision_score, recall_score,
                                 roc_auc_score)
    m = {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
    }
    if y_prob is not None:
        m["roc_auc"] = roc_auc_score(y_true, y_prob)
        m["pr_auc"] = average_precision_score(y_true, y_prob)
    return m
