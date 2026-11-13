"""
Alerta Temprana UPA · Aplicación de predicción de deserción escolar
==================================================================
Fase 4 de la Actividad 3.2.1 — Aprendizaje Automático Supervisado
Fundamentos de Inteligencia Artificial · Universidad Politécnica de Atlautla

Equipo G171:
  · Julissa Marin Flor
  · Erandy Naomy Rosas Toriz
  · Rogerio Aguilar Bello

Ejecutar:
    streamlit run app/app.py

La aplicación carga un pipeline serializado (preprocesador + modelo) y devuelve
la probabilidad de deserción junto con los factores que más pesan en la
predicción. No almacena datos personales.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import streamlit as st

BASE = Path(__file__).resolve().parent.parent
MODELO = BASE / "models" / "modelo_desercion.pkl"
META = BASE / "models" / "metadata.json"
FIG = BASE / "docs" / "figuras"
RES = BASE / "results"

# ---------------------------------------------------------------------------
# Identidad visual
# ---------------------------------------------------------------------------
INK = "#07182C"
NAVY = "#0B2745"
INDIGO = "#1D4E89"
BLUE = "#2563EB"
SKY = "#38BDF8"
MINT = "#10B981"
TEAL = "#14B8A6"
GOLD = "#F4C95D"
CORAL = "#F9735B"
RED = "#E14B4B"
AMBER = "#F59E0B"
GRAY = "#6B7C93"
LIGHT = "#F4F7FC"
BORDER = "#DCE5F0"
WHITE = "#FFFFFF"

EQUIPO = "Julissa Marin Flor · Erandy Naomy Rosas Toriz · Rogerio Aguilar Bello"
REF_IA = ("OpenCode. (2026). Big Pickle (versión 2026) "
          "[Modelo de lenguaje de gran escala]. https://opencode.ai")

st.set_page_config(
    page_title="Alerta Temprana UPA · Deserción escolar",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

  :root {
    --ink: __INK__; --navy: __NAVY__; --indigo: __INDIGO__; --blue: __BLUE__;
    --sky: __SKY__; --mint: __MINT__; --teal: __TEAL__; --gold: __GOLD__;
    --coral: __CORAL__; --red: __RED__; --amber: __AMBER__; --gray: __GRAY__;
    --light: __LIGHT__; --border: __BORDER__;
  }

  html, body, [class*="css"], .stApp {
    font-family: 'Montserrat', 'Manrope', 'Segoe UI', system-ui, sans-serif;
  }
  .stApp {
    background:
      radial-gradient(1100px 520px at 8% -10%, #E7F0FF 0%, transparent 55%),
      radial-gradient(900px 480px at 100% 0%, #E8FBF7 0%, transparent 50%),
      #F6F8FC;
  }
  .block-container {padding-top: 1.1rem; padding-bottom: 2.5rem; max-width: 1240px;}
  header[data-testid="stHeader"] {background: transparent;}
  #MainMenu, footer {visibility: hidden;}
  h1, h2, h3, h4 {color: var(--navy); letter-spacing: -0.35px;}

  /* ---------- HERO ---------- */
  .hero {
    position: relative; overflow: hidden; border-radius: 26px;
    padding: 2.15rem 2.4rem 1.95rem 2.4rem; color: white;
    background: linear-gradient(118deg, #061629 0%, #0E3157 48%, #1E5AA0 100%);
    box-shadow: 0 24px 60px -28px rgba(7, 24, 44, .75);
    margin-bottom: 1.15rem;
  }
  .hero::after {
    content: ""; position: absolute; inset: 0;
    background-image: linear-gradient(rgba(255,255,255,.045) 1px, transparent 1px),
                      linear-gradient(90deg, rgba(255,255,255,.045) 1px, transparent 1px);
    background-size: 42px 42px; pointer-events: none;
  }
  .orb {
    position: absolute; border-radius: 50%; filter: blur(2px); pointer-events: none;
    background: radial-gradient(circle at 30% 30%, rgba(56,189,248,.55), rgba(56,189,248,0) 68%);
  }
  .orb.a {width: 340px; height: 340px; right: -80px; top: -150px; animation: float1 13s ease-in-out infinite;}
  .orb.b {width: 220px; height: 220px; right: 190px; bottom: -130px; animation: float2 17s ease-in-out infinite;}
  .orb.c {width: 130px; height: 130px; left: 46%; top: -60px;
          background: radial-gradient(circle at 30% 30%, rgba(244,201,93,.45), rgba(244,201,93,0) 70%);
          animation: float1 11s ease-in-out infinite reverse;}
  @keyframes float1 {0%,100%{transform:translate3d(0,0,0)}50%{transform:translate3d(-18px,22px,0)}}
  @keyframes float2 {0%,100%{transform:translate3d(0,0,0)}50%{transform:translate3d(26px,-16px,0)}}

  .hero-content {position: relative; z-index: 2;}
  .pill {
    display: inline-block; background: rgba(255,255,255,.11); color: #DDEBFA;
    padding: .28rem .8rem; border-radius: 999px; font-size: .69rem;
    letter-spacing: .16em; text-transform: uppercase; font-weight: 700;
    border: 1px solid rgba(255,255,255,.22); margin-bottom: .8rem;
  }
  .hero h1 {color: white; font-size: 2.45rem; line-height: 1.04; margin: 0 0 .45rem 0; font-weight: 800;}
  .hero h1 span {color: var(--gold);}
  .hero p {color: #C7DBF2; margin: 0; font-size: .98rem; max-width: 790px; line-height: 1.55;}
  .hero-chips {display: flex; flex-wrap: wrap; gap: .5rem; margin-top: 1.15rem;}
  .chip {
    background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.17);
    color: #E7F2FC; border-radius: 10px; padding: .36rem .7rem;
    font-size: .74rem; font-weight: 600;
  }
  .chip b {color: var(--gold);}

  /* ---------- SIDEBAR ---------- */
  section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #061629 0%, #0A2543 58%, #0D3158 100%);
    border-right: 1px solid rgba(255,255,255,.06);
  }
  section[data-testid="stSidebar"] * {color: #E4EFFA !important;}
  section[data-testid="stSidebar"] h1,
  section[data-testid="stSidebar"] h2,
  section[data-testid="stSidebar"] h3,
  section[data-testid="stSidebar"] h4 {color: #FFFFFF !important; letter-spacing: -0.2px;}
  section[data-testid="stSidebar"] .stCaption,
  section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] * {color: #A9C3DE !important;}
  section[data-testid="stSidebar"] [data-testid="stMetricValue"] {color: #FFFFFF !important; font-size: 1.25rem;}
  section[data-testid="stSidebar"] [data-testid="stMetricLabel"] * {color: #A9C3DE !important;}
  section[data-testid="stSidebar"] hr {border-color: rgba(255,255,255,.12);}

  .side-brand {display: flex; align-items: center; gap: .7rem; margin: .1rem 0 1.1rem 0;}
  .side-brand .mark {
    width: 44px; height: 44px; border-radius: 13px; display: grid; place-items: center;
    background: linear-gradient(135deg, var(--sky), var(--blue));
    color: #061629; font-weight: 800; font-size: .82rem; letter-spacing: .02em;
    box-shadow: 0 8px 20px -8px rgba(56,189,248,.8);
  }
  .side-brand b {display: block; color: #fff; font-size: .95rem; line-height: 1.15;}
  .side-brand span {display: block; color: #9DBBD9; font-size: .7rem; letter-spacing: .08em; text-transform: uppercase;}

  .side-card {
    background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.12);
    border-radius: 16px; padding: .95rem 1rem; margin-bottom: .9rem;
  }
  .side-card .k {font-size: .64rem; letter-spacing: .15em; text-transform: uppercase; color: #9DBBD9; font-weight: 700;}
  .side-card .v {font-size: 1.05rem; font-weight: 800; color: #fff; margin-top: .1rem;}
  .side-card .s {font-size: .7rem; color: #9DBBD9; margin-top: .1rem;}
  .side-grid {display: grid; grid-template-columns: 1fr 1fr; gap: .55rem; margin-top: .75rem;}
  .side-grid div {background: rgba(255,255,255,.055); border-radius: 10px; padding: .45rem .55rem;}
  .side-grid span {display: block; font-size: .6rem; letter-spacing: .1em; text-transform: uppercase; color: #9DBBD9;}
  .side-grid b {display: block; font-size: .98rem; color: #fff;}

  /* ---------- TABS ---------- */
  div[data-testid="stTabs"] div[role="tablist"] {
    gap: 8px; background: transparent; border-bottom: none; margin-bottom: .35rem;
  }
  div[data-testid="stTabs"] [data-testid="stTab"][role="tab"] {
    background: #E9F0F9; border: 1px solid transparent; border-radius: 13px;
    padding: 9px 18px; height: auto; transition: all .18s ease; cursor: pointer;
  }
  div[data-testid="stTabs"] [data-testid="stTab"][role="tab"] p {
    font-weight: 700; font-size: .86rem; color: #3A5573;
  }
  div[data-testid="stTabs"] [data-testid="stTab"][role="tab"]:hover {background: #DCE9F8;}
  div[data-testid="stTabs"] [data-testid="stTab"][role="tab"][aria-selected="true"] {
    background: linear-gradient(120deg, var(--navy), var(--indigo));
    box-shadow: 0 8px 18px -10px rgba(11,39,69,.9);
  }
  div[data-testid="stTabs"] [data-testid="stTab"][role="tab"][aria-selected="true"] p {color: #FFFFFF;}
  div[data-testid="stTabs"] [data-baseweb="tab-highlight"] {display: none;}
  div[data-testid="stTabs"] [data-baseweb="tab-border"] {display: none;}

  /* ---------- SECCIONES Y TARJETAS ---------- */
  .sec {margin: .3rem 0 .9rem 0;}
  .sec .kicker {
    display: inline-block; font-size: .65rem; letter-spacing: .17em; text-transform: uppercase;
    color: var(--blue); font-weight: 800; margin-bottom: .22rem;
  }
  .sec h2 {font-size: 1.45rem; margin: 0; font-weight: 800;}
  .sec p {margin: .22rem 0 0 0; color: var(--gray); font-size: .88rem; max-width: 780px;}

  .panel {
    background: #FFFFFF; border: 1px solid var(--border); border-radius: 18px;
    padding: 1.15rem 1.25rem; box-shadow: 0 14px 34px -30px rgba(7,24,44,.55);
  }
  .soft {
    background: linear-gradient(145deg, #F7FAFF, #EDF4FE);
    border: 1px solid #DDE8F6; border-radius: 18px; padding: 1.1rem 1.2rem;
  }
  .note {
    background: #FFF9EA; border: 1px solid #F3DDAA; border-left: 4px solid var(--gold);
    border-radius: 12px; padding: .75rem .9rem; color: #6B5320; font-size: .82rem;
  }
  .warn {
    background: #FFF1EE; border: 1px solid #F7CFC6; border-left: 4px solid var(--coral);
    border-radius: 12px; padding: .75rem .9rem; color: #7C3A2E; font-size: .82rem;
  }
  .ok {
    background: #EAF9F2; border: 1px solid #BFEAD7; border-left: 4px solid var(--mint);
    border-radius: 12px; padding: .75rem .9rem; color: #186A4C; font-size: .82rem;
  }

  /* ---------- KPI ---------- */
  .kpi-grid {display: grid; grid-template-columns: repeat(auto-fit, minmax(155px, 1fr)); gap: 12px; margin: .6rem 0 1.1rem 0;}
  .kpi {
    background: #fff; border: 1px solid var(--border); border-top: 4px solid var(--accent);
    border-radius: 15px; padding: .85rem .95rem .8rem .95rem;
    box-shadow: 0 10px 26px -24px rgba(7,24,44,.7);
  }
  .kpi .v {display: block; font-size: 1.65rem; font-weight: 800; color: var(--accent); line-height: 1.05; letter-spacing: -.6px;}
  .kpi .l {display: block; font-size: .67rem; letter-spacing: .11em; text-transform: uppercase; color: var(--navy); font-weight: 800; margin-top: .28rem;}
  .kpi .n {display: block; font-size: .7rem; color: var(--gray); margin-top: .12rem;}

  /* ---------- RESULTADO ---------- */
  .risk {
    position: relative; overflow: hidden; border-radius: 22px; color: #fff;
    background: linear-gradient(135deg, #061629 0%, #0D2B4D 55%, #123C68 100%);
    padding: 1.25rem 1.35rem 1.35rem 1.35rem;
    box-shadow: 0 22px 48px -30px rgba(7,24,44,.95);
  }
  .risk::before {
    content: ""; position: absolute; width: 220px; height: 220px; border-radius: 50%;
    right: -70px; top: -90px; background: radial-gradient(circle, color-mix(in srgb, var(--ring) 45%, transparent), transparent 70%);
  }
  .risk-top {display: flex; align-items: center; justify-content: space-between; gap: .5rem; position: relative; z-index: 2;}
  .risk-top .t {font-size: .64rem; letter-spacing: .16em; text-transform: uppercase; color: #A9C3DE; font-weight: 800;}
  .risk-pill {font-size: .64rem; letter-spacing: .1em; text-transform: uppercase; font-weight: 800;
              padding: .25rem .55rem; border-radius: 999px; background: var(--ring); color: #061629;}
  .risk-body {display: flex; align-items: center; gap: 1.2rem; margin-top: .85rem; position: relative; z-index: 2;}
  .gauge {
    flex: 0 0 148px; width: 148px; height: 148px; border-radius: 50%;
    background: conic-gradient(var(--ring) calc(var(--pct) * 1%), rgba(255,255,255,.14) 0);
    display: grid; place-items: center; box-shadow: 0 0 0 6px rgba(255,255,255,.04);
  }
  .gauge-inner {
    width: 112px; height: 112px; border-radius: 50%; background: #07182C;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    border: 1px solid rgba(255,255,255,.08);
  }
  .gauge-inner b {font-size: 1.7rem; line-height: 1; color: #fff;}
  .gauge-inner small {font-size: .6rem; letter-spacing: .13em; text-transform: uppercase; color: #9DBBD9; margin-top: .18rem;}
  .risk-text h3 {color: #fff; margin: 0 0 .25rem 0; font-size: 1.3rem;}
  .risk-text p {color: #C7DBF2; margin: 0; font-size: .82rem; line-height: 1.5;}
  .risk-foot {display: flex; flex-wrap: wrap; gap: .45rem; margin-top: .9rem; position: relative; z-index: 2;}
  .risk-foot span {font-size: .67rem; color: #DCEBFA; background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.13); padding: .26rem .55rem; border-radius: 8px;}

  .factor {margin: .55rem 0;}
  .factor .top {display: flex; justify-content: space-between; font-size: .78rem; color: var(--navy); margin-bottom: .22rem;}
  .factor .top b {font-variant-numeric: tabular-nums;}
  .factor .track {height: 7px; background: #EDF2F9; border-radius: 999px; overflow: hidden;}
  .factor .fill {display: block; height: 100%; border-radius: 999px;}
  .fill.pos {background: linear-gradient(90deg, #F7A38F, var(--coral));}
  .fill.neg {background: linear-gradient(90deg, #7DE0CB, var(--teal));}
  .pos-t {color: var(--coral);} .neg-t {color: var(--teal);}

  /* ---------- TABLAS ---------- */
  .table-wrap {overflow-x: auto; border-radius: 14px; border: 1px solid var(--border);}
  table.modern {width: 100%; border-collapse: collapse; font-size: .79rem; background: #fff;}
  table.modern th {
    background: var(--navy); color: #fff; text-align: left; padding: .62rem .7rem;
    font-size: .64rem; letter-spacing: .1em; text-transform: uppercase; font-weight: 800;
  }
  table.modern td {padding: .55rem .7rem; border-bottom: 1px solid #EDF2F9; color: #24405F;}
  table.modern tr:nth-child(even) td {background: #F8FAFE;}
  table.modern tr.best td {background: #EEF7FF; font-weight: 700; color: var(--navy);}
  table.modern tr.best td:first-child {border-left: 4px solid var(--blue);}
  .tag {display: inline-block; background: var(--blue); color: #fff; font-size: .55rem;
        letter-spacing: .08em; text-transform: uppercase; padding: .13rem .4rem;
        border-radius: 999px; margin-left: .35rem; vertical-align: middle;}
  .bar-cell {display: flex; align-items: center; gap: .45rem;}
  .bar-cell .bar {height: 6px; border-radius: 999px; background: linear-gradient(90deg, #93C5FD, var(--blue)); min-width: 4px;}
  .bar-cell span {font-variant-numeric: tabular-nums;}

  /* ---------- MATRIZ ---------- */
  .cm-grid {display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: .4rem;}
  .cm-cell {border-radius: 12px; padding: .8rem; text-align: center; border: 1px solid var(--border);}
  .cm-cell b {display: block; font-size: 1.55rem; line-height: 1;}
  .cm-cell small {display: block; font-size: .64rem; margin-top: .25rem; color: #4D6580; line-height: 1.25;}
  .cm-good {background: #E9F8F1; border-color: #C6EBDD;} .cm-good b {color: #127A56;}
  .cm-bad {background: #FFF1ED; border-color: #F8D3C9;} .cm-bad b {color: #BF4A34;}
  .cm-legend {display: flex; gap: 1rem; margin-top: .55rem; font-size: .68rem; color: var(--gray);}

  /* ---------- EQUIDAD ---------- */
  .fair-grid {display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px; margin-top: .5rem;}
  .fair {background: #fff; border: 1px solid var(--border); border-radius: 15px; padding: .85rem .95rem;}
  .fair h4 {margin: 0 0 .55rem 0; font-size: .84rem;}
  .fair-row {margin: .45rem 0;}
  .fair-row .t {display: flex; justify-content: space-between; font-size: .7rem; color: var(--navy); margin-bottom: .18rem;}
  .fair-row .tr {height: 6px; background: #EDF2F9; border-radius: 999px; overflow: hidden;}
  .fair-row .fl {height: 100%; border-radius: 999px;}

  /* ---------- PIPELINE ---------- */
  .steps {display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-top: .4rem;}
  .step {background: #fff; border: 1px solid var(--border); border-radius: 14px; padding: .8rem .85rem; position: relative;}
  .step .n {width: 24px; height: 24px; border-radius: 8px; display: grid; place-items: center;
            background: linear-gradient(135deg, var(--sky), var(--blue)); color: #061629;
            font-size: .66rem; font-weight: 800; margin-bottom: .45rem;}
  .step b {display: block; font-size: .76rem; color: var(--navy); margin-bottom: .15rem;}
  .step span {font-size: .68rem; color: var(--gray); line-height: 1.35; display: block;}

  /* ---------- CATÁLOGO DE MODELOS ---------- */
  .models {display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 11px;}
  .model {background: #fff; border: 1px solid var(--border); border-radius: 14px; padding: .8rem .9rem;}
  .model .h {display: flex; align-items: center; justify-content: space-between; gap: .35rem;}
  .model b {font-size: .8rem; color: var(--navy);}
  .model .fam {font-size: .55rem; letter-spacing: .08em; text-transform: uppercase; color: var(--blue); font-weight: 800;}
  .model p {font-size: .68rem; color: var(--gray); margin: .35rem 0 0 0; line-height: 1.4;}

  /* ---------- ESCENARIOS ---------- */
  .scenario {border-radius: 18px; padding: 1rem 1.1rem; border: 1px solid var(--border); background: #fff;}
  .scenario.a {background: linear-gradient(135deg, #07182C, #12406E); border: none; color: #fff;}
  .scenario.a b, .scenario.a h3 {color: #fff;}
  .scenario .tagline {font-size: .58rem; letter-spacing: .15em; text-transform: uppercase; font-weight: 800; color: var(--gold);}
  .scenario h3 {font-size: 1.05rem; margin: .2rem 0 .3rem 0;}
  .scenario p {font-size: .75rem; line-height: 1.45; margin: 0;}
  .scenario.a p {color: #C7DBF2;}

  /* ---------- MISC ---------- */
  .pill-row {display: flex; flex-wrap: wrap; gap: .35rem; margin-top: .35rem;}
  .pill-row span {background: #EEF4FC; border: 1px solid #D9E6F6; color: #365579;
                  font-size: .66rem; padding: .24rem .5rem; border-radius: 8px;}
  .mini-title {font-size: .64rem; letter-spacing: .14em; text-transform: uppercase;
               color: var(--gray); font-weight: 800; margin: .2rem 0 .45rem 0;}
  .team {display: flex; flex-wrap: wrap; gap: .4rem;}
  .team span {background: #fff; border: 1px solid var(--border); border-radius: 10px;
              padding: .38rem .6rem; font-size: .72rem; color: var(--navy); font-weight: 700;}
  .team-list {display: flex; flex-direction: column; gap: .1rem;}
  .team-list > div {display: flex; align-items: center; gap: .7rem;
                    padding: .55rem 0; border-bottom: 1px dashed #E3EAF3;}
  .team-list > div:last-child {border-bottom: none;}
  .team-list .num {width: 28px; height: 28px; border-radius: 9px; display: grid;
                   place-items: center; background: linear-gradient(135deg, var(--sky), var(--blue));
                   color: #061629; font-size: .64rem; font-weight: 800; flex: 0 0 28px;}
  .team-list .dot {width: 9px; height: 9px; border-radius: 50%; background: var(--gold);
                   box-shadow: 0 0 0 4px rgba(244,201,93,.18); flex: 0 0 9px; margin: 0 .35rem 0 .25rem;}
  .team-list b {font-size: .82rem; color: var(--navy);}
  .team-list small {display: block; font-size: .66rem; color: var(--gray); font-weight: 500;}

  .footer {color: #71839B; font-size: .72rem; text-align: center; margin-top: 2rem;
           border-top: 1px solid #E3EAF3; padding-top: 1rem; line-height: 1.6;}

  /* ---------- CONTROLES ---------- */
  div[data-testid="stForm"] {background: #fff; border: 1px solid var(--border);
                             border-radius: 18px; padding: 1rem 1.05rem;}
  .stButton > button, .stFormSubmitButton > button {
    border-radius: 12px; font-weight: 800; border: 1px solid var(--border);
    transition: all .18s ease;
  }
  .stFormSubmitButton > button {
    background: linear-gradient(120deg, var(--blue), var(--indigo));
    color: #fff; border: none; padding: .6rem 1rem;
    box-shadow: 0 12px 24px -14px rgba(37,99,235,.85);
  }
  .stFormSubmitButton > button:hover {transform: translateY(-1px); color: #fff;}
  .stButton > button:hover {border-color: var(--blue); color: var(--blue);}
  div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
    border-radius: 10px; border-color: #D8E3F0;
  }
  .stSlider [data-baseweb="slider"] div[role="slider"] {background: var(--gold);}
  div[data-testid="stExpander"] {border: 1px solid var(--border); border-radius: 12px; background: #FBFCFE;}
  div[data-testid="stExpander"] summary p {font-weight: 700; color: var(--navy);}
  .stCodeBlock {border-radius: 12px;}
</style>
"""


def inyectar_css() -> None:
    css = (CSS
           .replace("__INK__", INK).replace("__NAVY__", NAVY)
           .replace("__INDIGO__", INDIGO).replace("__BLUE__", BLUE)
           .replace("__SKY__", SKY).replace("__MINT__", MINT)
           .replace("__TEAL__", TEAL).replace("__GOLD__", GOLD)
           .replace("__CORAL__", CORAL).replace("__RED__", RED)
           .replace("__AMBER__", AMBER).replace("__GRAY__", GRAY)
           .replace("__LIGHT__", LIGHT).replace("__BORDER__", BORDER))
    st.markdown(css, unsafe_allow_html=True)


inyectar_css()


# ---------------------------------------------------------------------------
# Datos y modelo
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def cargar_modelo():
    if not MODELO.exists():
        st.error("No se encontró `models/modelo_desercion.pkl`. "
                 "Ejecuta primero `python src/train.py`.")
        st.stop()
    return joblib.load(MODELO), json.loads(META.read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def cargar_resultados():
    datos = {}
    for nombre in ("metricas_ajustadas", "equidad", "importancia", "cv_resumen"):
        ruta = RES / f"{nombre}.csv"
        datos[nombre] = pd.read_csv(ruta) if ruta.exists() else pd.DataFrame()
    ruta_pred = RES / "predicciones_test.csv"
    datos["predicciones"] = pd.read_csv(ruta_pred) if ruta_pred.exists() else pd.DataFrame()
    return datos


modelo, meta = cargar_modelo()
RESULTADOS = cargar_resultados()

ETIQUETAS = {
    "Marital status": "Estado civil",
    "Application mode": "Vía de admisión",
    "Application order": "Orden de preferencia de la carrera",
    "Course": "Programa académico",
    "Previous qualification": "Titulación previa",
    "Previous qualification (grade)": "Nota de la titulación previa",
    "Admission grade": "Nota de admisión",
    "Mother's qualification": "Titulación de la madre",
    "Father's qualification": "Titulación del padre",
    "Mother's occupation": "Ocupación de la madre",
    "Father's occupation": "Ocupación del padre",
    "Age at enrollment": "Edad al ingresar",
    "Unemployment rate": "Tasa de desempleo (%)",
    "Inflation rate": "Inflación (%)",
    "GDP": "Crecimiento del PIB (%)",
    "Curricular units 1st sem (credited)": "Unidades acreditadas · 1.er semestre",
    "Curricular units 1st sem (enrolled)": "Unidades inscritas · 1.er semestre",
    "Curricular units 1st sem (evaluations)": "Evaluaciones presentadas · 1.er semestre",
    "Curricular units 1st sem (approved)": "Unidades aprobadas · 1.er semestre",
    "Curricular units 1st sem (grade)": "Calificación media · 1.er semestre",
    "Curricular units 1st sem (without evaluations)": "Unidades sin evaluar · 1.er semestre",
    "Tuition fees up to date": "Colegiatura al corriente",
    "Scholarship holder": "Beca",
    "Daytime/evening attendance": "Turno",
    "Displaced": "Estudiante desplazado",
    "Educational special needs": "Necesidades educativas especiales",
    "International": "Estudiante internacional",
    "Gender": "Sexo",
    "tasa_aprobacion_1s": "Tasa de aprobación · 1.er semestre",
    "evaluaciones_por_inscrita_1s": "Evaluaciones por unidad inscrita",
    "reprobadas_1s": "Unidades reprobadas · 1.er semestre",
    "sin_evaluar_1s": "Unidades sin evaluar · 1.er semestre",
}

CURSOS = {
    33: "Biofuel Production Technologies", 171: "Animation and Multimedia Design",
    8014: "Social Service (evening)", 9003: "Agronomy", 9070: "Communication Design",
    9085: "Veterinary Nursing", 9119: "Informatics Engineering", 9130: "Equinculture",
    9147: "Management", 9238: "Social Service", 9254: "Tourism",
    9500: "Nursing", 9556: "Oral Hygiene", 9670: "Advertising and Marketing",
    9773: "Journalism and Communication", 9853: "Basic Education",
    9991: "Management (evening)",
}

PERFILES = {
    "Perfil con apoyo y buen rendimiento": {
        "Edad al ingresar": 19, "Nota de admisión": 145.0,
        "Unidades inscritas · 1.er semestre": 6, "Unidades aprobadas · 1.er semestre": 6,
        "Calificación media · 1.er semestre": 15.0, "Beca": 1, "Deuda": 0,
        "Colegiatura al corriente": 1,
    },
    "Perfil con riesgo académico": {
        "Edad al ingresar": 23, "Nota de admisión": 126.0,
        "Unidades inscritas · 1.er semestre": 6, "Unidades aprobadas · 1.er semestre": 4,
        "Calificación media · 1.er semestre": 10.5, "Beca": 0, "Deuda": 0,
        "Colegiatura al corriente": 0,
    },
}


def etiqueta(col: str) -> str:
    return ETIQUETAS.get(col, col)


def kpis(items):
    tarjetas = "".join(
        f'<div class="kpi" style="--accent:{c}">'
        f'<span class="v">{v}</span><span class="l">{l}</span>'
        f'<span class="n">{n}</span></div>'
        for v, l, n, c in items)
    st.markdown(f'<div class="kpi-grid">{tarjetas}</div>', unsafe_allow_html=True)


def seccion(kicker, titulo, desc=""):
    extra = f"<p>{desc}</p>" if desc else ""
    st.markdown(
        f'<div class="sec"><span class="kicker">{kicker}</span>'
        f'<h2>{titulo}</h2>{extra}</div>', unsafe_allow_html=True)


def factor_rows(factores):
    if not factores:
        return
    mayor = max(abs(v) for _, v, _ in factores) or 1.0
    filas = []
    for nombre, valor, etq in factores:
        clase = "pos" if valor > 0 else "neg"
        ancho = max(abs(valor) / mayor * 100, 4)
        signo = "+" if valor > 0 else ""
        color = "pos-t" if valor > 0 else "neg-t"
        filas.append(
            f'<div class="factor">'
            f'<div class="top"><span>{html.escape(etq)}</span>'
            f'<b class="{color}">{signo}{valor:.2f}</b></div>'
            f'<div class="track"><span class="fill {clase}" style="width:{ancho:.0f}%"></span></div>'
            f'</div>')
    st.markdown("".join(filas), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Encabezado
# ---------------------------------------------------------------------------
st.markdown(f"""
<div class="hero">
  <div class="orb a"></div><div class="orb b"></div><div class="orb c"></div>
  <div class="hero-content">
    <span class="pill">Actividad 3.2.1 · Aprendizaje automático supervisado</span>
    <h1>Alerta Temprana <span>UPA</span></h1>
    <p>Un sistema que convierte los datos del primer semestre en tiempo para actuar.
       Estima el riesgo de deserción, explica sus razones y recuerda siempre que la
       decisión final es humana.</p>
    <div class="hero-chips">
      <span class="chip"><b>4 424</b> estudiantes</span>
      <span class="chip"><b>7</b> modelos comparados</span>
      <span class="chip"><b>0.912</b> AUC-ROC</span>
      <span class="chip"><b>79 %</b> de desertores detectados</span>
      <span class="chip">Grupo <b>G171</b></span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

if "form_key" not in st.session_state:
    st.session_state.form_key = 0
if "perfil_activo" not in st.session_state:
    st.session_state.perfil_activo = "Ninguno"

# Enlace directo a un caso de ejemplo: ?perfil=riesgo o ?perfil=apoyo
_param_perfil = (st.query_params.get("perfil") or "").strip().lower()
if _param_perfil and st.session_state.get("perfil_param") != _param_perfil:
    _coincidencia = next(
        (n for n in PERFILES if _param_perfil in n.lower()), None)
    if _coincidencia:
        st.session_state.perfil_activo = _coincidencia
        st.session_state.form_key += 1
    st.session_state.perfil_param = _param_perfil

# ---------------------------------------------------------------------------
# Barra lateral
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div class="side-brand">
      <div class="mark">UPA</div>
      <div><b>Alerta Temprana</b><span>Grupo G171</span></div>
    </div>
    """, unsafe_allow_html=True)

    m = meta["metricas_test"]
    st.markdown(f"""
    <div class="side-card">
      <div class="k">Modelo desplegado</div>
      <div class="v">{meta['modelo']}</div>
      <div class="s">Escenario temprano · inscripción + 1.er semestre</div>
      <div class="side-grid">
        <div><span>AUC-ROC</span><b>{m['roc_auc']:.3f}</b></div>
        <div><span>F1</span><b>{m['f1']:.3f}</b></div>
        <div><span>Recall</span><b>{m['recall']:.3f}</b></div>
        <div><span>Precisión</span><b>{m['precision']:.3f}</b></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("##### Umbral de decisión")
    umbral = st.slider(
        "Probabilidad mínima para activar la alerta", 0.20, 0.80,
        float(meta["umbral"]), 0.01,
        help="Bajarlo detecta más estudiantes en riesgo (más recall) a cambio de "
             "generar más alertas preventivas.",
    )
    st.caption(
        f"Umbral entrenado: **{meta['umbral']:.3f}**. Moverlo cambia el punto de "
        "operación, no el modelo."
    )

    st.markdown("---")
    st.markdown("##### Casos de ejemplo")
    _opciones_perfil = ["Ninguno"] + list(PERFILES.keys())
    _indice_perfil = (_opciones_perfil.index(st.session_state.perfil_activo)
                      if st.session_state.perfil_activo in _opciones_perfil else 0)
    perfil_sel = st.selectbox(
        "Cargar un caso precargado", _opciones_perfil,
        index=_indice_perfil, key="perfil_selector",
        placeholder="Selecciona un perfil", label_visibility="collapsed")
    if st.button("Aplicar perfil al formulario", width="stretch"):
        st.session_state.perfil_activo = perfil_sel
        st.session_state.form_key += 1
        st.rerun()
    st.caption(f"Entrenado con {meta['n_train']:,} casos · evaluado con "
               f"{meta['n_test']:,}.")

# Pestañas
tab_pred, tab_eval, tab_metodo = st.tabs(
    ["◎  Predicción", "▣  Evaluación", "❖  Metodología y datos"])

# ===========================================================================
# PREDICCIÓN
# ===========================================================================
with tab_pred:
    seccion("Paso 1 de 3", "Construye el perfil del estudiante",
            "Completa solo la información disponible. Los valores precargados son "
            "típicos de la institución: ajústalos al caso real.")
    st.markdown("""
    <div class="steps" style="margin-bottom:.9rem;">
      <div class="step"><div class="n">1</div><b>Completa el perfil</b><span>Datos académicos, apoyos y contexto.</span></div>
      <div class="step"><div class="n">2</div><b>Calcula el riesgo</b><span>El modelo devuelve una probabilidad de 0 a 100 %.</span></div>
      <div class="step"><div class="n">3</div><b>Lee la explicación</b><span>Revisa qué factores suben o bajan el riesgo.</span></div>
      <div class="step"><div class="n">4</div><b>Actúa con criterio</b><span>La alerta abre una conversación, no una sanción.</span></div>
    </div>
    """, unsafe_allow_html=True)

    prefs = PERFILES.get(st.session_state.perfil_activo, {})
    col_form, col_res = st.columns([1.12, 1.0], gap="large")

    with col_form:
        with st.form(f"formulario_{st.session_state.form_key}"):
            st.markdown("##### Contexto del estudiante")
            a, b, c = st.columns(3)
            with a:
                edad = st.number_input(
                    "Edad al ingresar", 17, 70,
                    int(prefs.get("Edad al ingresar",
                                  meta["valores_defecto"]["Age at enrollment"])))
            with b:
                genero = st.selectbox(
                    "Sexo", [0, 1],
                    format_func=lambda v: "Masculino" if v == 0 else "Femenino")
            with c:
                curso = st.selectbox(
                    "Programa académico", sorted(CURSOS),
                    index=sorted(CURSOS).index(9500),
                    format_func=lambda v: CURSOS.get(v, str(v)))

            st.markdown("##### Rendimiento del primer semestre")
            d, e, f = st.columns(3)
            with d:
                inscritas = st.number_input(
                    "Unidades inscritas", 0, 20,
                    int(prefs.get("Unidades inscritas · 1.er semestre", 6)))
            with e:
                aprobadas = st.number_input(
                    "Unidades aprobadas", 0, 20,
                    int(prefs.get("Unidades aprobadas · 1.er semestre", 5)))
            with f:
                nota_sem = st.number_input(
                    "Calificación media (0–20)", 0.0, 20.0,
                    float(prefs.get("Calificación media · 1.er semestre", 12.0)), 0.1)
            g, h = st.columns(2)
            with g:
                nota_adm = st.number_input(
                    "Nota de admisión (0–200)", 0.0, 200.0,
                    float(prefs.get("Nota de admisión",
                                    meta["valores_defecto"]["Admission grade"])), 0.5)
            with h:
                evaluaciones = st.number_input(
                    "Evaluaciones presentadas", 0, 40, int(min(inscritas * 2, 20)))

            st.markdown("##### Apoyos y situación socioeconómica")
            i1, i2, i3 = st.columns(3)
            with i1:
                beca = st.selectbox(
                    "¿Tiene beca?", [0, 1], index=int(prefs.get("Beca", 0)),
                    format_func=lambda v: "Sí" if v else "No")
                deuda = st.selectbox(
                    "¿Tiene deuda institucional?", [0, 1], index=int(prefs.get("Deuda", 0)),
                    format_func=lambda v: "Sí" if v else "No")
            with i2:
                colegiatura = st.selectbox(
                    "¿Colegiatura al corriente?", [1, 0],
                    index=0 if prefs.get("Colegiatura al corriente", 1) else 1,
                    format_func=lambda v: "Sí" if v else "No")
                turno = st.selectbox(
                    "Turno", [1, 0], format_func=lambda v: "Diurno" if v else "Nocturno")
            with i3:
                desplazado = st.selectbox(
                    "¿Estudiante desplazado?", [0, 1],
                    format_func=lambda v: "Sí" if v else "No")
                internacional = st.selectbox(
                    "¿Estudiante internacional?", [0, 1],
                    format_func=lambda v: "Sí" if v else "No")

            with st.expander("Ajustes avanzados (familia, necesidades y unidades sin evaluar)"):
                j1, j2 = st.columns(2)
                with j1:
                    sin_eval = st.number_input("Unidades sin evaluar", 0, 20, 0)
                    necesidades = st.selectbox(
                        "¿Necesidades educativas especiales?", [0, 1],
                        format_func=lambda v: "Sí" if v else "No")
                with j2:
                    st.caption("Las variables familiares y la vía de admisión se toman "
                               "del valor típico del dataset para mantener el formulario breve.")

            enviado = st.form_submit_button(
                "Calcular riesgo de deserción", type="primary", width="stretch")

        if enviado:
            fila = dict(meta["valores_defecto"])
            fila.update({
                "Age at enrollment": edad, "Gender": genero, "Course": curso,
                "Admission grade": nota_adm, "Scholarship holder": beca, "Debtor": deuda,
                "Tuition fees up to date": colegiatura,
                "Curricular units 1st sem (enrolled)": inscritas,
                "Curricular units 1st sem (approved)": aprobadas,
                "Curricular units 1st sem (grade)": nota_sem,
                "Curricular units 1st sem (evaluations)": evaluaciones,
                "Curricular units 1st sem (without evaluations)": sin_eval,
                "Displaced": desplazado, "Educational special needs": necesidades,
                "Daytime/evening attendance": turno, "International": internacional,
            })
            fila["tasa_aprobacion_1s"] = aprobadas / inscritas if inscritas else 0.0
            fila["evaluaciones_por_inscrita_1s"] = (
                evaluaciones / inscritas if inscritas else 0.0)
            fila["reprobadas_1s"] = max(inscritas - aprobadas, 0)
            fila["sin_evaluar_1s"] = sin_eval

            X = pd.DataFrame([fila])[meta["columnas"]]
            prob = float(modelo.predict_proba(X)[0, 1])

            factores = []
            try:
                prep = modelo.named_steps["prep"]
                clf = modelo.named_steps["modelo"]
                nombres = prep.get_feature_names_out()
                aportes = clf.coef_[0] * prep.transform(X)[0]
                serie = pd.Series(aportes, index=nombres)
                base_cols = set(meta["columnas"])

                def base(nombre_col: str) -> str:
                    if nombre_col in base_cols:
                        return nombre_col
                    prefijo = nombre_col.rsplit("_", 1)[0]
                    return prefijo if prefijo in base_cols else nombre_col

                serie = serie.groupby(serie.index.map(base)).sum()
                serie = serie.reindex(serie.abs().sort_values(ascending=False).index)
                for nombre, valor in serie.head(6).items():
                    factores.append((nombre, float(valor), etiqueta(nombre)))
            except Exception:
                factores = []

            st.session_state.resultado = {
                "prob": prob, "factores": factores,
                "aprobadas": aprobadas, "inscritas": inscritas,
                "tasa": fila["tasa_aprobacion_1s"],
                "evaluaciones": evaluaciones,
            }

    with col_res:
        res = st.session_state.get("resultado")
        if not res:
            st.markdown("""
            <div class="risk" style="--ring:#38BDF8; --pct:0;">
              <div class="risk-top"><span class="t">Vista previa</span>
                <span class="risk-pill" style="background:rgba(255,255,255,.14);color:#DDEBFA;">Sin calcular</span></div>
              <div class="risk-body">
                <div class="gauge"><div class="gauge-inner"><b>—</b><small>riesgo</small></div></div>
                <div class="risk-text">
                  <h3>Tu resultado aparecerá aquí</h3>
                  <p>Completa el formulario y presiona <b>Calcular riesgo</b>. Verás la
                     probabilidad estimada, el nivel de alerta y los factores que más
                     influyen en este caso.</p>
                </div>
              </div>
              <div class="risk-foot"><span>Explicación local</span><span>Umbral ajustable</span><span>Sin guardar datos</span></div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("""
            <div class="note" style="margin-top:.8rem;">
            <b>¿Cómo leer el resultado?</b> El porcentaje no es una sentencia: es una señal
            para priorizar una conversación. Un 60 % significa que el modelo encontró un
            patrón de riesgo, no que el estudiante vaya a abandonar.
            </div>
            """, unsafe_allow_html=True)
        else:
            prob = res["prob"]
            low_cut = min(0.30, umbral * 0.55)
            if prob < low_cut:
                nivel, color, icono = "Riesgo bajo", MINT, "●"
                lectura = ("El perfil se parece al de estudiantes que permanecen. "
                           "Mantén el acompañamiento habitual.")
                consejo = "Seguimiento ordinario. Refuerza hábitos de estudio y pertenencia."
                clase = "ok"
            elif prob < umbral:
                nivel, color, icono = "Riesgo medio", AMBER, "●"
                lectura = ("Conviene un seguimiento preventivo: tutoría breve y revisión "
                           "de condiciones económicas.")
                consejo = "Tutoría preventiva y revisión de apoyos antes de que el riesgo crezca."
                clase = "note"
            else:
                nivel, color, icono = "Riesgo alto", CORAL, "●"
                lectura = ("Se recomienda contacto prioritario de bienestar estudiantil "
                           "en los próximos días.")
                consejo = "Contacto prioritario, plan de acompañamiento y revisión de beca o deuda."
                clase = "warn"

            alerta = prob >= umbral
            st.markdown(f"""
            <div class="risk" style="--ring:{color}; --pct:{prob*100:.1f};">
              <div class="risk-top">
                <span class="t">Resultado del modelo</span>
                <span class="risk-pill">{icono} {nivel}</span>
              </div>
              <div class="risk-body">
                <div class="gauge"><div class="gauge-inner">
                  <b>{prob*100:.1f}%</b><small>riesgo</small>
                </div></div>
                <div class="risk-text">
                  <h3>{nivel}</h3>
                  <p>{lectura}</p>
                </div>
              </div>
              <div class="risk-foot">
                <span>Umbral {umbral*100:.0f} %</span>
                <span>{'Alerta activada' if alerta else 'Alerta no activada'}</span>
                <span>{res['aprobadas']}/{res['inscritas']} unidades aprobadas</span>
              </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f'<div class="{clase}" style="margin-top:.75rem;">'
                        f'<b>Recomendación.</b> {consejo}</div>',
                        unsafe_allow_html=True)

            st.markdown('<div class="mini-title" style="margin-top:1rem;">'
                        'Factores que más pesan en este caso</div>',
                        unsafe_allow_html=True)
            factor_rows(res["factores"])
            st.caption("Aporte aproximado de cada variable al puntaje: coeficiente × "
                       "valor estandarizado. Las barras coral suben el riesgo; las verdes "
                       "lo reducen.")
            st.markdown("""
            <div class="note" style="margin-top:.7rem;">
            <b>Uso responsable.</b> Esta señal no debe usarse para negar servicios,
            becas o inscripción. La decisión y el acompañamiento corresponden a una persona.
            </div>
            """, unsafe_allow_html=True)

# ===========================================================================
# EVALUACIÓN
# ===========================================================================
with tab_eval:
    m = meta["metricas_test"]
    cm = np.array(meta["matriz_confusion"])
    seccion("Evidencia del modelo", "¿Qué tan bien funciona y dónde falla?",
            "Métricas calculadas sobre el 20 % de prueba (885 estudiantes) con el "
            "umbral de operación elegido.")
    kpis([
        (f"{m['accuracy']:.3f}", "Accuracy", "885 casos de prueba", BLUE),
        (f"{m['recall']:.3f}", "Recall", "224 de 284 desertores", CORAL),
        (f"{m['f1']:.3f}", "F1-score", f"precisión {m['precision']:.3f}", GOLD),
        (f"{m['roc_auc']:.3f}", "AUC-ROC", f"PR-AUC {m['pr_auc']:.3f}", TEAL),
    ])

    e1, e2 = st.columns([1.18, 1], gap="large")
    with e1:
        st.markdown('<div class="mini-title">Comparación de los siete modelos · escenario temprano</div>',
                    unsafe_allow_html=True)
        tabla = RESULTADOS["metricas_ajustadas"]
        if not tabla.empty:
            tabla = tabla[tabla.escenario == "temprano"].sort_values("f1", ascending=False)
            filas = []
            for _, r in tabla.iterrows():
                mejor = r["modelo"] == meta["modelo"]
                filas.append(
                    f'<tr class="{"best" if mejor else ""}">'
                    f'<td>{html.escape(r["modelo"])}'
                    f'{"<span class=\"tag\">desplegado</span>" if mejor else ""}</td>'
                    f'<td><div class="bar-cell"><div class="bar" style="width:{r["f1"]*100:.0f}%"></div>'
                    f'<span>{r["f1"]:.3f}</span></div></td>'
                    f'<td>{r["recall"]:.3f}</td><td>{r["roc_auc"]:.3f}</td></tr>')
            st.markdown(
                '<div class="table-wrap"><table class="modern">'
                '<thead><tr><th>Modelo</th><th>F1</th><th>Recall</th><th>AUC-ROC</th></tr></thead>'
                f'<tbody>{"".join(filas)}</tbody></table></div>',
                unsafe_allow_html=True)
            st.caption("La regresión logística lidera F1 y recall con la menor brecha "
                       "train-test. Random Forest empata en AUC pero sobreajusta.")
        else:
            st.info("No se encontró results/metricas_ajustadas.csv.")

        st.markdown('<div class="mini-title" style="margin-top:1rem;">Matriz de confusión · umbral 0.595</div>',
                    unsafe_allow_html=True)
        st.markdown(f"""
        <div class="panel" style="padding:.85rem;">
          <div style="display:flex;justify-content:space-between;font-size:.64rem;color:#6B7C93;text-transform:uppercase;letter-spacing:.1em;font-weight:800;">
            <span>Predicción: permanece</span><span>Predicción: deserta</span>
          </div>
          <div class="cm-grid">
            <div class="cm-cell cm-good"><b>{cm[0,0]}</b><small>Verdaderos negativos<br>acertó que permanece</small></div>
            <div class="cm-cell cm-bad"><b>{cm[0,1]}</b><small>Falsas alarmas<br>alerta innecesaria</small></div>
            <div class="cm-cell cm-bad"><b>{cm[1,0]}</b><small>Falsos negativos<br>desertor no detectado</small></div>
            <div class="cm-cell cm-good"><b>{cm[1,1]}</b><small>Verdaderos positivos<br>desertor detectado</small></div>
          </div>
          <div class="cm-legend"><span>Real: permanece (fila superior)</span><span>Real: deserta (fila inferior)</span></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="warn" style="margin-top:.7rem;">
        <b>El error que más importa.</b> {cm[1,0]} estudiantes desertores no fueron
        detectados. Cada falso negativo es una oportunidad de acompañamiento que se pierde;
        por eso el umbral prioriza el recall sobre la precisión perfecta.
        </div>
        """, unsafe_allow_html=True)

    with e2:
        st.markdown('<div class="mini-title">Curvas de desempeño</div>',
                    unsafe_allow_html=True)
        roc = FIG / "fig_10_roc.png"
        pr = FIG / "fig_11_precision_recall.png"
        if roc.exists():
            st.image(str(roc), width="stretch")
        if pr.exists():
            st.image(str(pr), width="stretch")

    st.markdown("---")
    seccion("Equidad", "Un modelo que funciona mejor para unos que para otros",
            "El desempeño se audita por subgrupo. Reportar la brecha es el primer paso "
            "para mitigarla; ocultarla sería parte del problema.")
    eq = RESULTADOS["equidad"]
    if not eq.empty:
        grupos = [("Sexo", "Género", BLUE), ("Beca", "Beca", GOLD), ("Edad", "Edad", TEAL)]
        tarjetas = []
        for variable, titulo, color in grupos:
            sub = eq[eq.variable == variable]
            filas = []
            for _, r in sub.iterrows():
                recall = r["recall"]
                if recall < 0.70:
                    c, etiqueta_riesgo = CORAL, "brecha alta"
                elif recall < 0.80:
                    c, etiqueta_riesgo = AMBER, "brecha media"
                else:
                    c, etiqueta_riesgo = MINT, "sin alerta"
                filas.append(
                    f'<div class="fair-row">'
                    f'<div class="t"><span>{html.escape(str(r["grupo"]))} · n={int(r["n"])}</span>'
                    f'<b style="color:{c};">{recall:.3f} <span style="font-weight:600;font-size:.6rem;color:#6B7C93;">{etiqueta_riesgo}</span></b></div>'
                    f'<div class="tr"><span class="fl" style="width:{recall*100:.0f}%;background:{c};"></span></div>'
                    f'</div>')
            tarjetas.append(
                f'<div class="fair"><h4>{titulo}</h4>{"".join(filas)}'
                f'<div style="font-size:.62rem;color:#6B7C93;margin-top:.45rem;">'
                f'Recall por grupo · tasa real de deserción en la etiqueta</div></div>')
        st.markdown(f'<div class="fair-grid">{"".join(tarjetas)}</div>',
                    unsafe_allow_html=True)
        st.markdown("""
        <div class="warn" style="margin-top:.8rem;">
        <b>Hallazgo incómodo.</b> El recall cae a <b>0.517</b> en estudiantes con beca
        frente a <b>0.820</b> sin beca, y a <b>0.667</b> en menores de 20 años. El modelo
        reconoce mejor al perfil dominante. La app lo declara, el informe lo discute y el
        sistema se plantea como apoyo, nunca como filtro automático.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No se encontró results/equidad.csv.")

    st.markdown("---")
    f1, f2 = st.columns([1.1, 1], gap="large")
    with f1:
        seccion("Interpretabilidad", "¿Qué variables mueven la decisión?",
                "Importancia por permutación sobre el conjunto de prueba: cuánto empeora "
                "el modelo cuando se rompe una variable.")
        imp = FIG / "fig_13_importancia.png"
        if imp.exists():
            st.image(str(imp), width="stretch")
    with f2:
        st.markdown('<div class="mini-title">Lecturas que importan</div>',
                    unsafe_allow_html=True)
        st.markdown("""
        <div class="panel">
          <p style="font-size:.82rem;color:#3A5573;line-height:1.55;margin-top:0;">
          <b>1. El rendimiento temprano manda.</b> Unidades reprobadas y aprobadas del
          primer semestre concentran la señal. Son variables accionables: se pueden
          intervenir con tutoría.</p>
          <p style="font-size:.82rem;color:#3A5573;line-height:1.55;">
          <b>2. La economía pesa.</b> Colegiatura al corriente, deuda y desempleo aparecen
          entre los factores principales. El apoyo financiero no es un adorno.</p>
          <p style="font-size:.82rem;color:#3A5573;line-height:1.55;margin-bottom:0;">
          <b>3. La complejidad no ayudó.</b> Random Forest y la red neuronal no superaron
          a la regresión logística. Con datos tabulares y 3 500 casos, la simplicidad
          gana en desempeño y en auditoría.</p>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("Ver sobreajuste, umbral y validación cruzada"):
            for nombre, pie in [
                ("fig_07_brecha_overfitting.png", "Brecha F1 entre entrenamiento y prueba."),
                ("fig_12_umbral.png", "F1, precisión y recall según el umbral."),
                ("fig_15_validacion_cruzada.png", "Estabilidad entre pliegues."),
            ]:
                ruta = FIG / nombre
                if ruta.exists():
                    st.image(str(ruta), caption=pie, width="stretch")

# ===========================================================================
# METODOLOGÍA Y DATOS
# ===========================================================================
with tab_metodo:
    seccion("Ficha del proyecto", "Del dato abierto a una decisión responsable",
            "Todo lo que sostiene la aplicación: el problema, el dataset, el método, "
            "los modelos y las reglas de uso.")
    kpis([
        ("4 424", "estudiantes", "36 variables + objetivo", BLUE),
        ("32.1 %", "deserción", "1 421 de 4 424", CORAL),
        ("7", "algoritmos", "GridSearchCV + CV 5", TEAL),
        ("2", "escenarios", "temprano y completo", GOLD),
        ("0.912", "AUC-ROC", "modelo desplegado", INDIGO),
        ("0", "valores nulos", "0 duplicados", MINT),
    ])

    # --- Problema + dataset ---
    p1, p2 = st.columns([1, 1], gap="large")
    with p1:
        st.markdown("""
        <div class="panel">
          <div class="pill-row" style="margin-bottom:.55rem;"><span>Problema</span><span>Impacto social</span></div>
          <h3 style="margin:.1rem 0 .4rem 0;font-size:1.08rem;">Una silla vacía que se ve demasiado tarde</h3>
          <p style="font-size:.82rem;color:#3A5573;line-height:1.6;margin:0;">
          La deserción no ocurre en un día: es una sucesión de señales que la institución
          suele advertir cuando el estudiante ya se fue. Abandonar reduce ingresos,
          movilidad y participación social, y golpea con más fuerza a los hogares de
          menores recursos. Este proyecto no pretende predecir por predecir: busca
          <b>comprar tiempo</b> para una tutoría, una beca o una flexibilidad académica.
          </p>
          <div class="pill-row" style="margin-top:.7rem;">
            <span>+ deuda: 57.8 % deserta</span>
            <span>+25 años: 58.6 %</span>
            <span>≤ 20 años: 19.9 %</span>
          </div>
        </div>
        """, unsafe_allow_html=True)
    with p2:
        st.markdown(f"""
        <div class="panel">
          <div class="pill-row" style="margin-bottom:.55rem;"><span>Dataset abierto</span><span>UCI 697</span><span>CC BY 4.0</span></div>
          <h3 style="margin:.1rem 0 .4rem 0;font-size:1.08rem;">Predict Students' Dropout and Academic Success</h3>
          <p style="font-size:.8rem;color:#3A5573;line-height:1.55;margin:0 0 .55rem 0;">
          Realinho, Vieira, Neto y Costa (2021). 4 424 estudiantes de una institución de
          educación superior, con variables académicas, demográficas y socioeconómicas.
          </p>
          <div style="font-size:.72rem;color:#3A5573;line-height:1.7;">
            <b>DOI:</b> 10.24432/C5MC89<br>
            <b>Fuente:</b> UCI Machine Learning Repository · ID 697<br>
            <b>Objetivo original:</b> Graduate 2 209 · Enrolled 794 · Dropout 1 421
          </div>
          <div style="margin-top:.7rem;">
            <div style="display:flex;justify-content:space-between;font-size:.64rem;color:#6B7C93;font-weight:700;">
              <span>No deserta 67.9 %</span><span>Deserta 32.1 %</span>
            </div>
            <div style="display:flex;height:10px;border-radius:999px;overflow:hidden;margin-top:.25rem;">
              <span style="width:67.9%;background:linear-gradient(90deg,#7DE0CB,{TEAL});"></span>
              <span style="width:32.1%;background:linear-gradient(90deg,{CORAL},#E14B4B);"></span>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # --- Escenarios ---
    st.markdown('<div class="mini-title" style="margin-top:1rem;">Dos escenarios para no hacer trampa con el tiempo</div>',
                unsafe_allow_html=True)
    s1, s2 = st.columns(2, gap="large")
    with s1:
        st.markdown("""
        <div class="scenario a">
          <div class="tagline">Escenario A · desplegado</div>
          <h3>Inscripción + primer semestre</h3>
          <p>82 columnas tras el preprocesamiento. Es el único escenario honesto para
             intervenir: la alerta llega al inicio del segundo semestre, cuando todavía
             se puede cambiar el desenlace.</p>
          <div class="pill-row" style="margin-top:.7rem;">
            <span style="background:rgba(255,255,255,.1);border-color:rgba(255,255,255,.18);color:#E7F2FC;">F1 0.799</span>
            <span style="background:rgba(255,255,255,.1);border-color:rgba(255,255,255,.18);color:#E7F2FC;">AUC 0.912</span>
            <span style="background:rgba(255,255,255,.1);border-color:rgba(255,255,255,.18);color:#E7F2FC;">desplegable</span>
          </div>
        </div>
        """, unsafe_allow_html=True)
    with s2:
        st.markdown("""
        <div class="scenario">
          <div class="tagline" style="color:#2563EB;">Escenario B · solo diagnóstico</div>
          <h3>Añade el segundo semestre</h3>
          <p>107 columnas. Mejora el AUC en unas dos centésimas, pero predice un desenlace
             que ya ocurrió. Un modelo tardío y preciso es un modelo inútil para prevenir.</p>
          <div class="pill-row" style="margin-top:.7rem;">
            <span>AUC 0.932</span><span>+0.020 vs. A</span><span>no desplegable</span>
          </div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("""
    <div class="note" style="margin-top:.75rem;">
    <b>La decisión clave.</b> Preferimos perder dos centésimas de AUC antes que predecir
    el pasado. La utilidad de un sistema de alerta se mide por lo que permite hacer a tiempo.
    </div>
    """, unsafe_allow_html=True)

    # --- Pipeline ---
    st.markdown("---")
    seccion("Método", "Un pipeline reproducible, sin fuga de información",
            "Cada transformación se ajusta solo con el conjunto de entrenamiento y se "
            "aplica después al de prueba.")
    st.markdown("""
    <div class="steps">
      <div class="step"><div class="n">01</div><b>Limpieza</b><span>Nombres normalizados, sin nulos ni duplicados.</span></div>
      <div class="step"><div class="n">02</div><b>Ingeniería</b><span>Tasa de aprobación, reprobadas y evaluaciones por unidad.</span></div>
      <div class="step"><div class="n">03</div><b>Codificación</b><span>One-Hot para categorías y variables binarias.</span></div>
      <div class="step"><div class="n">04</div><b>Escalado</b><span>StandardScaler dentro del Pipeline, solo con train.</span></div>
      <div class="step"><div class="n">05</div><b>Búsqueda</b><span>7 modelos con GridSearchCV y F1 como criterio.</span></div>
      <div class="step"><div class="n">06</div><b>Umbral</b><span>Punto de operación elegido para priorizar recall.</span></div>
    </div>
    """, unsafe_allow_html=True)

    # --- Modelos ---
    st.markdown('<div class="mini-title" style="margin-top:1rem;">Los siete algoritmos comparados</div>',
                unsafe_allow_html=True)
    MODELOS = [
        ("Regresión Logística", "Lineal", "Ganador: interpretable, estable y con la menor brecha train-test.", BLUE),
        ("KNN", "Instancias", "Sensible a la escala y a la dimensionalidad; el más débil del comparativo.", GRAY),
        ("SVM (RBF)", "Margen", "Buena frontera no lineal, pero más costoso y menos transparente.", TEAL),
        ("Árbol de Decisión", "Árbol", "Muy interpretable; sin poda memoriza el entrenamiento.", AMBER),
        ("Random Forest", "Ensamble", "Empata en AUC, pero sobreajusta y pierde interpretabilidad.", CORAL),
        ("Red Neuronal (MLP)", "Red", "Capacidad extra que se vuelve ruido con 3 500 casos tabulares.", INDIGO),
        ("Naive Bayes", "Probabilístico", "Referencia ingenua: rápido, pero con supuestos fuertes.", GOLD),
    ]
    tarjetas = "".join(
        f'<div class="model"><div class="h"><b>{n}</b></div>'
        f'<div class="fam" style="color:{c};">{f}</div>'
        f'<p>{d}</p></div>' for n, f, d, c in MODELOS)
    st.markdown(f'<div class="models">{tarjetas}</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="ok" style="margin-top:.8rem;">
    <b>Modelo final:</b> regresión logística con <b>C = 10</b>, ponderación de clases y
    umbral <b>0.595</b>. Lidera F1 y recall, su desviación entre pliegues es la más baja
    (0.006) y sus coeficientes se pueden explicar a un comité académico.
    </div>
    """, unsafe_allow_html=True)

    # --- Diccionario de datos ---
    st.markdown("---")
    d1, d2 = st.columns([1, 1], gap="large")
    with d1:
        seccion("Datos", "Qué entra al modelo",
                "La app usa las 33 variables del escenario temprano; el resto se mantiene "
                "con valores típicos para acortar el formulario.")
        grupos = [
            ("Numéricas continuas", meta.get("numericas", []), BLUE),
            ("Categóricas codificadas", meta.get("categoricas", []), TEAL),
            ("Binarias", meta.get("binarias", []), GOLD),
        ]
        for titulo, cols, color in grupos:
            with st.expander(f"{titulo} · {len(cols)} variables"):
                chips = "".join(
                    f'<span>{html.escape(etiqueta(c))}</span>' for c in cols)
                st.markdown(f'<div class="pill-row">{chips}</div>',
                            unsafe_allow_html=True)
    with d2:
        seccion("Métricas", "Cómo se evalúa",
                "Accuracy sola engaña cuando las clases están desbalanceadas. Por eso se "
                "reportan seis métricas y la matriz de confusión.")
        METRICAS = [
            ("Accuracy", "Proporción total de aciertos. Útil como foto general, insuficiente sola."),
            ("Precision", "De las alertas emitidas, cuántas corresponden a desertores reales."),
            ("Recall", "De los desertores reales, cuántos fueron detectados. Métrica prioritaria."),
            ("F1-score", "Media armónica entre precisión y recall; equilibra ambas."),
            ("AUC-ROC", "Capacidad de ordenar el riesgo entre 0.5 (azar) y 1 (perfecto)."),
            ("PR-AUC", "Desempeño en la clase positiva cuando la prevalencia es baja."),
        ]
        filas = "".join(
            f'<div style="display:flex;gap:.6rem;padding:.42rem 0;border-bottom:1px dashed #E3EAF3;">'
            f'<b style="min-width:78px;font-size:.72rem;color:{BLUE};">{n}</b>'
            f'<span style="font-size:.71rem;color:#4D6580;line-height:1.4;">{d}</span></div>'
            for n, d in METRICAS)
        st.markdown(f'<div class="panel">{filas}</div>', unsafe_allow_html=True)

    # --- Equipo y transparencia ---
    st.markdown("---")
    r1, r2 = st.columns([0.86, 1.14], gap="large")
    with r1:
        seccion("Equipo", "Quiénes lo hicieron",
                "Grupo G171 · Universidad Politécnica de Atlautla.")
        st.markdown("""
        <div class="panel" style="padding:.95rem 1.15rem;">
          <div class="team-list">
            <div><span class="num">01</span><b>Julissa Marin Flor</b></div>
            <div><span class="num">02</span><b>Erandy Naomy Rosas Toriz</b></div>
            <div><span class="num">03</span><b>Rogerio Aguilar Bello</b></div>
          </div>
        </div>
        """, unsafe_allow_html=True)
    with r2:
        seccion("Transparencia", "Cómo se construyó",
                "Decisiones verificables y uso de IA declarado.")
        st.markdown(f"""
        <div class="panel">
          <div class="mini-title">Declaración de uso de IA</div>
          <p style="font-size:.76rem;color:#3A5573;line-height:1.55;margin:0;">
          Se utilizó <b>OpenCode · Big Pickle (versión 2026)</b> como copiloto de
          programación, revisión de redacción y maquetación. Todo el código fue ejecutado
          y verificado; las métricas provienen de <code>results/</code> y son reproducibles
          con <code>src/train.py</code>. Las decisiones de diseño son responsabilidad del
          equipo.
          </p>
          <p style="font-size:.66rem;color:#6B7C93;margin:.5rem 0 0 0;line-height:1.4;">
          <b>Referencia APA 7:</b> {REF_IA}
          </p>
        </div>
        <div class="note" style="margin-top:.7rem;">
        <b>Privacidad.</b> La aplicación no almacena ni transmite datos personales:
        cada cálculo ocurre en memoria y desaparece al cerrar la sesión.
        </div>
        """, unsafe_allow_html=True)

st.markdown(f"""
<div class="footer">
Universidad Politécnica de Atlautla · Fundamentos de Inteligencia Artificial · Grupo G171<br>
{EQUIPO}<br>
Prototipo académico · 2026 · Los datos personales no se almacenan ni se transmiten.
</div>
""", unsafe_allow_html=True)
