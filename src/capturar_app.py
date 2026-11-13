#!/usr/bin/env python3
"""
Captura las pantallas de la aplicación Streamlit para el informe y el GIF.

Requiere la app corriendo en http://localhost:8501.

Salida:
  docs/figuras/fig_app_inicio.png
  docs/figuras/fig_app_prediccion.png
  docs/figuras/fig_app_evaluacion.png
  docs/figuras/fig_app_metodologia.png
"""
from __future__ import annotations

import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

BASE = Path(__file__).resolve().parent.parent
FIG = BASE / "docs" / "figuras"
FIG.mkdir(parents=True, exist_ok=True)

URL = "http://localhost:8501"


def nuevo_driver(alto: int = 1060, url: str = URL):
    opts = Options()
    opts.binary_location = "/usr/bin/chromium-browser"
    for arg in ("--headless=new", "--no-sandbox", "--disable-dev-shm-usage",
                "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1"):
        opts.add_argument(arg)
    d = webdriver.Chrome(options=opts)
    d.set_window_size(1480, alto)
    d.get(url)
    return d


def esperar_app(d):
    WebDriverWait(d, 30).until(
        lambda x: len(x.find_elements(By.CSS_SELECTOR,
                                      "[data-testid='stTab'][role='tab']")) >= 3)
    time.sleep(2.2)


def ir_al_inicio(d):
    d.execute_script("window.scrollTo(0, 0);")
    time.sleep(0.8)


def ir_a_tab(d, texto: str):
    botones = d.find_elements(By.CSS_SELECTOR, "[data-testid='stTab'][role='tab']")
    objetivo = next(b for b in botones if texto.lower() in b.text.lower())
    d.execute_script("arguments[0].click();", objetivo)
    time.sleep(1.6)
    tabs = d.find_element(By.CSS_SELECTOR, 'div[data-testid="stTabs"]')
    y = tabs.location["y"]
    d.execute_script(f"window.scrollTo(0, {max(y - 24, 0)});")
    time.sleep(0.7)


def main() -> None:
    d = nuevo_driver(1060)
    esperar_app(d)

    # 1. Portada / inicio
    ir_al_inicio(d)
    d.save_screenshot(str(FIG / "fig_app_inicio.png"))
    print("inicio")

    # 2. Predicción con resultado visible (perfil de riesgo vía URL)
    d.get(URL + "/?perfil=riesgo")
    esperar_app(d)
    d.execute_script("window.scrollTo(0, 0);")
    time.sleep(0.4)
    boton = d.find_element(
        By.XPATH, "//button[contains(., 'Calcular riesgo de deserción')]")
    d.execute_script("arguments[0].scrollIntoView({block: 'center'});", boton)
    time.sleep(0.3)
    d.execute_script("arguments[0].click();", boton)
    WebDriverWait(d, 30).until(
        lambda x: "Resultado del modelo" in x.page_source)
    time.sleep(1.6)
    riesgo = d.find_element(By.CSS_SELECTOR, ".risk")
    d.execute_script("arguments[0].scrollIntoView({block: 'start'});", riesgo)
    d.execute_script("window.scrollBy(0, -70);")
    time.sleep(0.8)
    d.save_screenshot(str(FIG / "fig_app_prediccion.png"))
    print("prediccion")

    # 3. Evaluación del modelo
    ir_a_tab(d, "Evaluación")
    d.save_screenshot(str(FIG / "fig_app_evaluacion.png"))
    print("evaluación")

    # 4. Metodología y datos (captura alta)
    d.set_window_size(1480, 2600)
    time.sleep(0.8)
    ir_a_tab(d, "Metodología")
    d.save_screenshot(str(FIG / "fig_app_metodologia.png"))
    print("metodología")

    d.quit()
    for nombre in ("fig_app_inicio.png", "fig_app_prediccion.png",
                   "fig_app_evaluacion.png", "fig_app_metodologia.png"):
        p = FIG / nombre
        print(nombre, p.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
