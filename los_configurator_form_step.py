import streamlit as st
import matplotlib.pyplot as plt
import os
import json
import io
import textwrap
import requests
import smtplib
import email.message
import tempfile
from collections import UserDict
from fpdf import FPDF

# ---------------- Page Config -----------------
st.set_page_config(page_title="Level of Speed Configurator", layout="wide")

# ---------------- Translations ----------------
languages = {"en": "English", "ru": "Русский", "de": "Deutsch"}
translations = {
    "en": {
        "select_brand": "Select Brand",
        "select_model": "Select Model",
        "select_generation": "Select Generation",
        "select_fuel": "Select Fuel",
        "select_engine": "Select Engine",
        "select_stage": "Select Stage",
        "stage_power": "Power only",
        "stage_options_only": "Options only",
        "stage_full": "Full package",
        "options": "Options",
        "form_title": "Contact Us",
        "name": "Name",
        "email": "Email",
        "vin": "VIN",
        "message": "Message",
        "send_copy": "Send me a copy",
        "attach_pdf": "Attach PDF report",
        "upload_file": "Attach file",
        "submit": "Submit",
        "success": "Thank you! We will contact you soon.",
        "error_name": "Please enter your name",
        "error_email": "Please enter a valid email",
        "difference": "Difference",
        "chart_note": (
            "Please note that all displayed values of power and torque gains "
            "are approximate and may vary depending on many factors, including "
            "fuel quality and the current condition of the vehicle. Level of "
            "Speed recommends taking these into account when evaluating results. "
            "By confirming receipt of the report, you agree that you have read this information."
        )
    },
    "ru": {
        "select_brand": "Выберите марку",
        "select_model": "Выберите модель",
        "select_generation": "Выберите поколение",
        "select_fuel": "Выберите топливо",
        "select_engine": "Выберите двигатель",
        "select_stage": "Выберите Stage",
        "stage_power": "Только мощность",
        "stage_options_only": "Только опции",
        "stage_full": "Полный пакет",
        "options": "Опции",
        "form_title": "Свяжитесь с нами",
        "name": "Имя",
        "email": "Email",
        "vin": "VIN",
        "message": "Сообщение",
        "send_copy": "Прислать копию",
        "attach_pdf": "Приложить PDF отчёт",
        "upload_file": "Прикрепить файл",
        "submit": "Отправить",
        "success": "Спасибо! Мы скоро свяжемся.",
        "error_name": "Введите имя",
        "error_email": "Введите корректный email",
        "difference": "Разница",
        "chart_note": (
            "Обращаем ваше внимание, что все отображаемые значения прироста мощности "
            "и крутящего момента являются ориентировочными и могут варьироваться "
            "в зависимости от множества факторов, включая качество топлива и текущее "
            "состояние автомобиля. Компания Level of Speed рекомендует учитывать эти "
            "условия при оценке результатов. Подтверждая получение отчёта, вы соглашаетесь "
            "с тем, что ознакомились с данной информацией."
        )
    },
    "de": {
        "select_brand": "Marke wählen",
        "select_model": "Modell wählen",
        "select_generation": "Generation wählen",
        "select_fuel": "Kraftstoff wählen",
        "select_engine": "Motor wählen",
        "select_stage": "Stage wählen",
        "stage_power": "Nur Leistung",
        "stage_options_only": "Nur Optionen",
        "stage_full": "Komplettpaket",
        "options": "Optionen",
        "form_title": "Kontakt",
        "name": "Name",
        "email": "E-Mail",
        "vin": "VIN",
        "message": "Nachricht",
        "send_copy": "Kopie an mich senden",
        "attach_pdf": "PDF Bericht anhängen",
        "upload_file": "Datei anhängen",
        "submit": "Senden",
        "success": "Danke! Wir melden uns bald.",
        "error_name": "Bitte Namen eingeben",
        "error_email": "Bitte gültige E-Mail eingeben",
        "difference": "Differenz",
        "chart_note": (
            "Bitte beachten Sie, dass alle angezeigten Werte für Leistungs- und Drehmomentsteigerung "
            "Richtwerte sind und je nach verschiedenen Faktoren wie Kraftstoffqualität und dem aktuellen "
            "Zustand des Fahrzeugs variieren können. Level of Speed empfiehlt, diese Bedingungen bei der "
            "Beurteilung der Ergebnisse zu berücksichtigen. Mit der Bestätigung des Erhalts des Berichts "
            "erklären Sie sich damit einverstanden, diese Informationen gelesen zu haben."
        )
    }
}

class _T(UserDict):
    def __missing__(self, key):
        return key

# Header & Language Selector
_, col_lang = st.columns([10, 2])
with col_lang:
    lang = st.selectbox("", list(languages.keys()), format_func=lambda x: languages[x], label_visibility="collapsed")
_t = _T(translations.get(lang, translations["en"]))

# Logo & Title
logo = next((p for p in ("logo.png", "logo_white.png") if os.path.exists(p)), None)
if logo:
    _, c, _ = st.columns([1, 4, 1])
    c.image(logo, width=200)
st.title("Level of Speed Configurator 🚘")

# Load DB and prune empty
@st.cache_data
def load_db():
    with open(os.path.join("data", "full_database.json"), encoding="utf-8") as f:
        return json.load(f)
def prune(node):
    if isinstance(node, dict):
        return {k: prune(v) for k, v in node.items() if v not in (None, {}, [], "")}

    return node
db = prune(load_db())
clear = lambda *keys: [st.session_state.pop(k, None) for k in keys]

# Selection Flow
brand = st.selectbox(_t["select_brand"], [""] + sorted(db.keys()), key="brand", on_change=lambda: clear("model", "generation", "fuel", "engine", "stage", "options"))
if not brand:
    st.stop()
model = st.selectbox(_t["select_model"], [""] + sorted(db[brand].keys()), key="model", on_change=lambda: clear("generation", "fuel", "engine", "stage", "options"))
if not model:
    st.stop()
gen = st.selectbox(_t["select_generation"], [""] + sorted(db[brand][model].keys()), key="generation", on_change=lambda: clear("fuel", "engine", "stage", "options"))
if not gen:
    st.stop()
engines_data = db[brand][model][gen]
fuels = sorted({d.get("Type") for d in engines_data.values() if isinstance(d, dict)})
fuel = st.selectbox(_t["select_fuel"], [""] + fuels, key="fuel", on_change=lambda: clear("engine", "stage", "options"))
if not fuel:
    st.stop()
engines = [name for name, d in engines_data.items() if isinstance(d, dict) and d.get("Type") == fuel]
engine = st.selectbox(_t["select_engine"], [""] + engines, key="engine")
