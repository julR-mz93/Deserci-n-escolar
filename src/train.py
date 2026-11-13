#!/usr/bin/env python3
"""
Entrena y compara los modelos supervisados del proyecto de deserción escolar.

Genera:
  results/metricas_baseline.csv   métricas con hiperparámetros por defecto
  results/metricas_ajustadas.csv  métricas tras GridSearchCV
  results/cv_resumen.csv          validación cruzada (media ± desviación)
  results/mejores_parametros.json
  results/equidad.csv             métricas por subgrupos (equidad algorítmica)
  results/umbrales.json           umbral óptimo de decisión
  models/modelo_desercion.pkl     pipeline final desplegable (escenario temprano)
  models/metadata.json            columnas, umbral y métricas para la app
"""
from __future__ import annotations

import json
import time
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (confusion_matrix, f1_score, precision_recall_curve,
                             roc_curve)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_validate

import pipeline as P

warnings.filterwarnings("ignore")

RES = P.BASE / "results"
MOD = P.BASE / "models"
RES.mkdir(exist_ok=True)
MOD.mkdir(exist_ok=True)
CV = StratifiedKFold(n_splits=5, shuffle=True, random_state=P.RANDOM_STATE)
ESCENARIOS = ["completo", "temprano"]


def evaluar(nombre, modelo, Xtr, ytr, Xte, yte, escenario, etapa):
    prob = modelo.predict_proba(Xte)[:, 1]
    pred = (prob >= 0.5).astype(int)
    m = P.metricas(yte, pred, prob)
    prob_tr = modelo.predict_proba(Xtr)[:, 1]
    pred_tr = (prob_tr >= 0.5).astype(int)
    m_tr = P.metricas(ytr, pred_tr, prob_tr)
    return {
        "escenario": escenario,
        "etapa": etapa,
        "modelo": nombre,
        **{k: round(v, 4) for k, v in m.items()},
        "f1_train": round(m_tr["f1"], 4),
        "brecha_f1": round(m_tr["f1"] - m["f1"], 4),
    }


def main() -> None:
    t0 = time.time()
    df = P.enriquecer(P.cargar_datos())
    df.to_csv(P.PROCESSED, index=False)
    print(f"Dataset: {df.shape[0]} filas x {df.shape[1]} columnas")
    print("Tasa de deserción:", round(df['desertor'].mean() * 100, 2), "%")

    filas_base, filas_ajust, filas_cv = [], [], []
    mejores, umbrales = {}, {}

    for esc in ESCENARIOS:
        print(f"\n===== ESCENARIO: {esc} =====")
        Xtr, Xte, ytr, yte = P.dividir(df, esc)
        print(f"train={Xtr.shape} test={Xte.shape} features crudas={Xtr.shape[1]}")

        for nombre, spec in P.catalogo_modelos(esc).items():
            # 1) Línea base con hiperparámetros por defecto
            base = P.armar_pipeline(spec["modelo"], esc)
            base.fit(Xtr, ytr)
            fila = evaluar(nombre, base, Xtr, ytr, Xte, yte, esc, "baseline")
            filas_base.append(fila)
            print(f"  [base] {nombre:24s} F1={fila['f1']:.3f} "
                  f"Recall={fila['recall']:.3f} AUC={fila['roc_auc']:.3f}")

            # 2) Búsqueda de hiperparámetros con validación cruzada
            grid = GridSearchCV(
                P.armar_pipeline(spec["modelo"], esc),
                param_grid=spec["rejilla"],
                scoring="f1", cv=CV, n_jobs=-1, refit=True,
            )
            grid.fit(Xtr, ytr)
            fila = evaluar(nombre, grid.best_estimator_, Xtr, ytr, Xte, yte,
                           esc, "ajustado")
            filas_ajust.append(fila)
            mejores[f"{esc}|{nombre}"] = {
                k.replace("modelo__", ""): v for k, v in grid.best_params_.items()
            }
            print(f"  [tune] {nombre:24s} F1={fila['f1']:.3f} "
                  f"Recall={fila['recall']:.3f} AUC={fila['roc_auc']:.3f} "
                  f"| {grid.best_params_}")

            # 3) Validación cruzada del modelo ya ajustado (robustez)
            scores = cross_validate(grid.best_estimator_, Xtr, ytr, cv=CV,
                                    scoring=["accuracy", "precision", "recall",
                                             "f1", "roc_auc", "average_precision"],
                                    n_jobs=1)
            filas_cv.append({
                "escenario": esc, "modelo": nombre,
                **{f"{k.replace('test_', '')}_media": round(v.mean(), 4)
                   for k, v in scores.items() if k.startswith("test_")},
                **{f"{k.replace('test_', '')}_std": round(v.std(), 4)
                   for k, v in scores.items() if k.startswith("test_")},
            })

    pd.DataFrame(filas_base).to_csv(RES / "metricas_baseline.csv", index=False)
    pd.DataFrame(filas_ajust).to_csv(RES / "metricas_ajustadas.csv", index=False)
    pd.DataFrame(filas_cv).to_csv(RES / "cv_resumen.csv", index=False)

    # ------------------------------------------------------------------
    # Modelo final: escenario temprano (sin fuga de información) y umbral
    # de decisión optimizado para maximizar F1 con recall alto.
    # ------------------------------------------------------------------
    tabla = pd.DataFrame(filas_ajust)
    temp = tabla[tabla.escenario == "temprano"].sort_values(
        ["f1", "recall"], ascending=False)
    ganador = temp.iloc[0]["modelo"]
    print(f"\nModelo ganador (temprano): {ganador}")

    Xtr, Xte, ytr, yte = P.dividir(df, "temprano")
    spec = P.catalogo_modelos("temprano")[ganador]
    grid = GridSearchCV(P.armar_pipeline(spec["modelo"], "temprano"),
                        spec["rejilla"],
                        scoring="f1", cv=CV, n_jobs=-1)
    grid.fit(Xtr, ytr)
    final = grid.best_estimator_

    prob_te = final.predict_proba(Xte)[:, 1]
    prec, rec, thr = precision_recall_curve(yte, prob_te)
    f1s = np.divide(2 * prec * rec, prec + rec, out=np.zeros_like(prec),
                    where=(prec + rec) > 0)
    umbral = float(np.clip(thr[np.argmax(f1s[:-1])], 0.15, 0.65))
    umbrales = {
        "umbral_f1_optimo": round(umbral, 3),
        "f1_umbral_0.5": round(f1_score(yte, (prob_te >= 0.5).astype(int)), 4),
        "f1_umbral_optimo": round(f1_score(yte, (prob_te >= umbral).astype(int)), 4),
        "recall_umbral_optimo": round(
            P.metricas(yte, (prob_te >= umbral).astype(int))["recall"], 4),
        "modelo": ganador,
    }
    print("Umbrales:", umbrales)

    new_thr = umbral
    pred_te = (prob_te >= new_thr).astype(int)

    # Matriz de confusión y curvas del modelo final (para las figuras)
    cm = confusion_matrix(yte, pred_te)
    fpr, tpr, _ = roc_curve(yte, prob_te)
    np.savez(RES / "curvas_final.npz", fpr=fpr, tpr=tpr, prob=prob_te,
             y=yte.to_numpy(), cm=cm)
    np.savez(RES / "curva_pr_final.npz", precision=prec, recall=rec)
    pd.DataFrame({"y_real": yte.to_numpy(), "prob": prob_te,
                  "y_pred": pred_te}).to_csv(RES / "predicciones_test.csv",
                                             index=False)

    # Equidad: desempeño por subgrupos demográficos
    sub = Xte.copy()
    sub["y"] = yte.to_numpy()
    sub["pred"] = pred_te
    equidad = []
    cortes = {
        "Sexo": ("Gender", {0: "Masculino", 1: "Femenino"}),
        "Beca": ("Scholarship holder", {0: "Sin beca", 1: "Con beca"}),
        "Deuda": ("Debtor", {0: "Sin deuda", 1: "Con deuda"}),
    }
    for variable, (col, mapa) in cortes.items():
        for valor, etiqueta in mapa.items():
            g = sub[sub[col] == valor]
            if len(g) < 20:
                continue
            m = P.metricas(g["y"], g["pred"], None)
            equidad.append({"variable": variable, "grupo": etiqueta, "n": len(g),
                            "tasa_real_desercion": round(g["y"].mean(), 4),
                            "recall": round(m["recall"], 4),
                            "precision": round(m["precision"], 4),
                            "f1": round(m["f1"], 4)})
    # Grupo de edad
    for etiqueta, (lo, hi) in {"≤20 años": (0, 20), "21-25 años": (21, 25),
                               ">25 años": (26, 99)}.items():
        g = sub[(sub["Age at enrollment"] >= lo) & (sub["Age at enrollment"] <= hi)]
        if len(g) < 20:
            continue
        m = P.metricas(g["y"], g["pred"], None)
        equidad.append({"variable": "Edad", "grupo": etiqueta, "n": len(g),
                        "tasa_real_desercion": round(g["y"].mean(), 4),
                        "recall": round(m["recall"], 4),
                        "precision": round(m["precision"], 4),
                        "f1": round(m["f1"], 4)})
    pd.DataFrame(equidad).to_csv(RES / "equidad.csv", index=False)

    # Persistencia del modelo y metadatos para la app
    joblib.dump(final, MOD / "modelo_desercion.pkl")
    meta = {
        "modelo": ganador,
        "escenario": "temprano (inscripción + primer semestre)",
        "umbral": round(new_thr, 3),
        "columnas": P.columnas_entrada("temprano"),
        "categoricas": P.NOMINALES,
        "binarias": P.BINARIAS,
        "numericas": P.conjunto_columnas("temprano")["numericas"],
        "valores_defecto": P.valores_por_defecto(df, "temprano"),
        "metricas_test": {k: round(v, 4) for k, v in
                          P.metricas(yte, pred_te, prob_te).items()},
        "matriz_confusion": cm.tolist(),
        "n_train": int(len(Xtr)), "n_test": int(len(Xte)),
        "desercion_test": round(float(yte.mean()), 4),
    }
    (MOD / "metadata.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    (RES / "mejores_parametros.json").write_text(
        json.dumps(mejores, ensure_ascii=False, indent=2), encoding="utf-8")
    (RES / "umbrales.json").write_text(
        json.dumps(umbrales, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n--- Métricas del modelo final (test, umbral óptimo) ---")
    print(json.dumps(meta["metricas_test"], indent=2, ensure_ascii=False))
    print(f"\nListo en {time.time() - t0:.1f} s")


if __name__ == "__main__":
    main()
