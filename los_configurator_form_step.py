import streamlit as st
import matplotlib.pyplot as plt
import os, json, io, textwrap, requests, smtplib, email.message, tempfile
from collections import UserDict
from fpdf import FPDF

# ---------------- Page Config -----------------
st.set_page_config(page_title="Level of Speed Configurator", layout="wide")

# ---------------- Translations ----------------
languages = {"en": "English", "ru": "Русский", "de": "Deutsch"}
_en = {"select_brand": "Select Brand", "select_model": "Select Model", "select_generation": "Select Generation", "select_fuel": "Select Fuel", "select_engine": "Select Engine", "select_stage": "Select Stage", "stage_power": "Power only", "stage_options_only": "Options only", "stage_full": "Full package", "options": "Options", "form_title": "Contact Us", "name": "Name", "email": "Email", "vin": "VIN", "message": "Message", "send_copy": "Send me a copy", "attach_pdf": "Attach PDF report", "upload_file": "Attach file", "submit": "Submit", "success": "Thank you! We will contact you soon.", "error_name": "Please enter your name", "error_email": "Please enter a valid email", "error_select_options": "Select at least one option", "difference": "Difference"}
translations = {"en": _en, "ru": _en, "de": _en}  # TODO: add real RU / DE strings
class _T(UserDict):
    def __missing__(self, key):
        return key

# ---------------- Header ----------------------
_, col_lang = st.columns([10,2])
with col_lang:
    lang = st.selectbox("", list(languages.keys()), format_func=lambda x: languages[x], label_visibility="collapsed")
_t = _T(translations.get(lang, translations["en"]))

logo = next((p for p in ("logo.png", "logo_white.png") if os.path.exists(p)), None)
if logo:
    _, c, _ = st.columns([1,2,1]); c.image(logo, width=180)

st.title("Level of Speed Configurator 🚘")

# ---------------- Load DB ---------------------
@st.cache_data
def load_db():
    with open(os.path.join("data", "full_database.json"), encoding="utf-8") as f:
        return json.load(f)

def prune(node):
    return {k: prune(v) for k, v in node.items() if v not in (None, {}, [], "")} if isinstance(node, dict) else node

db = prune(load_db())
clear = lambda *k: [st.session_state.pop(x, None) for x in k]

# ---------------- Selection flow --------------
brand = st.selectbox(_t["select_brand"], [""]
