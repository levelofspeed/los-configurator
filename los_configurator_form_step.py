import streamlit as st
import matplotlib.pyplot as plt
import os
import json
import requests
import io
import tempfile
from fpdf import FPDF

# Page configuration
st.set_page_config(page_title="Level of Speed Configurator", layout="wide")

# Multilanguage support
directories = {"en": "English", "ru": "Русский", "de": "Deutsch"}
translations = {
    "en": {"select_language": "Select Language", "title": "Level of Speed Configurator", "select_brand": "Select Brand", "select_model": "Select Model", "select_generation": "Select Generation", "select_fuel": "Select Fuel", "select_engine": "Select Engine", "select_stage": "Select Stage", "options": "Options", "form_title": "Contact Us", "name": "Name", "email": "Email", "vin": "VIN", "message": "Message", "send_copy": "Send me a copy", "attach_pdf": "Attach PDF", "upload_file": "Attach file", "submit": "Submit", "error_name": "Please enter your name.", "error_email": "Please enter a valid email.", "error_select_options": "Please select at least one option for full package.", "stage_power": "Power Increase Only", "stage_options_only": "Options Only", "stage_full": "Full Package", "difference_hp": "+{hp} hp", "difference_torque": "+{torque} Nm", "original_hp": "Original / Tuned HP", "original_torque": "Original / Tuned Torque", "no_data": "No data available for this selection.", "success_message": "Thank you! Your request has been submitted."},
    "ru": {"select_language": "Выбор языка", "title": "Конфигуратор Level of Speed", "select_brand": "Выберите марку", "select_model": "Выберите модель", "select_generation": "Выберите поколение", "select_fuel": "Выберите топливо", "select_engine": "Выберите двигатель", "select_stage": "Выберите стейдж", "options": "Опции", "form_title": "Контактная форма", "name": "Имя", "email": "Email", "vin": "VIN", "message": "Сообщение", "send_copy": "Отправить копию мне", "attach_pdf": "Прикрепить PDF", "upload_file": "Прикрепить файл", "submit": "Отправить", "error_name": "Пожалуйста, введите имя.", "error_email": "Пожалуйста, введите корректный Email.", "error_select_options": "Пожалуйста, выберите опции для полного пакета.", "stage_power": "Только мощность", "stage_options_only": "Только опции", "stage_full": "Полный пакет", "difference_hp": "+{hp} л.с.", "difference_torque": "+{torque} Нм", "original_hp": "Оригинал / Тюнинг л.с.", "original_torque": "Оригинал / Тюнинг Нм", "no_data": "Нет данных для выбранной конфигурации.", "success_message": "Спасибо! Ваша заявка отправлена."},
    "de": {"select_language": "Sprache wählen", "title": "Level of Speed Konfigurator", "select_brand": "Marke wählen", "select_model": "Modell wählen", "select_generation": "Generation wählen", "select_fuel": "Kraftstoff wählen", "select_engine": "Motor wählen", "select_stage": "Stufe wählen", "options": "Optionen", "form_title": "Kontaktformular", "name": "Name", "email": "E-Mail", "vin": "VIN", "message": "Nachricht", "send_copy": "Kopie an mich senden", "attach_pdf": "PDF anhängen", "upload_file": "Datei anhängen", "submit": "Senden", "error_name": "Bitte geben Sie Ihren Namen ein.", "error_email": "Bitte geben Sie eine gültige E-Mail-Adresse ein.", "error_select_options": "Bitte wählen Sie mindestens eine Option.", "stage_power": "Nur Leistung", "stage_options_only": "Nur Optionen", "stage_full": "Komplettpaket", "difference_hp": "+{hp} PS", "difference_torque": "+{torque} Nm", "original_hp": "Original / Getunte PS", "original_torque": "Original / Getunter Nm", "no_data": "Keine Daten verfügbar.", "success_message": "Vielen Dank! Ihre Anfrage wurde gesendet."}
}

# Logo
cols = st.columns([1, 8, 1])
with cols[1]:
    logo = os.path.join(os.getcwd(), "logo.png")
    if os.path.exists(logo):
        try:
            # use_container_width is preferred in newer Streamlit versions
            st.image(logo, use_container_width=True)
        except TypeError:
            # fallback for older versions
            st.image(logo, use_column_width=True)

# Language selector and title
lang_cols = st.columns([8, 1])
with lang_cols[1]:
    lang_code = st.selectbox(
        translations['en']['select_language'],
        list(directories.keys()),
        index=list(directories.keys()).index('en'),
        format_func=lambda x: directories[x],
        key='language',
        label_visibility='collapsed'
    )
with lang_cols[0]:
    st.title(translations[lang_code]['title'])

t = translations[lang_code]

# Load database
@st.cache_data
def load_database():
    path = os.path.join(os.getcwd(), 'data', 'full_database.json')
    with open(path, encoding='utf-8') as f:
        return json.load(f)

db = load_database()

# Selections
brand = st.selectbox(t['select_brand'], [''] + list(db.keys()), key='brand')
if not brand: st.stop()
model = st.selectbox(t['select_model'], [''] + list(db[brand].keys()), key='model')
if not model: st.stop()
gen = st.selectbox(t['select_generation'], [''] + list(db[brand][model].keys()), key='generation')
if not gen: st.stop()

engines = db[brand][model][gen]
fuels = sorted(set(v['Type'] for v in engines.values()))
fuel = st.selectbox(t['select_fuel'], [''] + fuels, key='fuel')
if not fuel: st.stop()
list_eng = [k for k,v in engines.items() if v['Type']==fuel]
engine = st.selectbox(t['select_engine'], [''] + list_eng, key='engine')
if not engine: st.stop()
stage = st.selectbox(t['select_stage'], [t['stage_power'], t['stage_options_only'], t['stage_full']], key='stage')
opts = []
if stage != t['stage_power']:
    st.markdown('----')
    opts = st.multiselect(t['options'], engines[engine]['Options'], key='options')

# Charts and form temporarily disabled for debugging
st.write("DEBUG: Stage=", stage)
st.write("DEBUG: Options selected=", opts)
st.stop()
