#!/usr/bin/env python3
"""
Amplía models/metadata.json con rangos y opciones de cada variable.

La aplicación Streamlit usa esta información para construir los controles del
formulario (mínimos, máximos y categorías válidas) sin necesidad de cargar el
dataset completo en tiempo de inferencia.
"""
from __future__ import annotations

import json

import pipeline as P


def main() -> None:
    df = P.enriquecer(P.cargar_datos())
    ruta = P.MOD / "metadata.json" if hasattr(P, "MOD") else P.BASE / "models" / "metadata.json"
    meta = json.loads(ruta.read_text(encoding="utf-8"))

    rangos, opciones, etiquetas = {}, {}, {}
    for col in meta["columnas"]:
        s = df[col]
        if col in meta["categoricas"]:
            vals = sorted(int(v) for v in s.dropna().unique())
            opciones[col] = vals
        elif col in meta["binarias"]:
            opciones[col] = sorted(int(v) for v in s.dropna().unique())
        else:
            rangos[col] = {
                "min": float(s.min()), "max": float(s.max()),
                "p05": float(s.quantile(0.05)), "p95": float(s.quantile(0.95)),
                "mediana": float(s.median()),
            }

    comunes = {
        "Daytime/evening attendance": {0: "Nocturno", 1: "Diurno"},
        "Displaced": {0: "No", 1: "Sí"},
        "Educational special needs": {0: "No", 1: "Sí"},
        "Debtor": {0: "No", 1: "Sí"},
        "Tuition fees up to date": {0: "No", 1: "Sí"},
        "Gender": {0: "Masculino", 1: "Femenino"},
        "Scholarship holder": {0: "No", 1: "Sí"},
        "International": {0: "No", 1: "Sí"},
    }
    for col in meta["binarias"]:
        etiquetas[col] = [comunes.get(col, {}).get(v, str(v)) for v in opciones[col]]

    meta["rangos"] = rangos
    meta["opciones"] = opciones
    meta["etiquetas_binarias"] = etiquetas
    ruta.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("metadata.json actualizado:", len(rangos), "rangos,", len(opciones), "categóricas")


if __name__ == "__main__":
    main()
