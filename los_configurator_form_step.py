import streamlit as st
import matplotlib.pyplot as plt
import os, json, io, tempfile, requests
from fpdf import FPDF
from collections import UserDict

# ---------- Page config ----------
st.set_page_config(page_title="Level of Speed Configurator", layout="wide")

# ---------- Translations ----------
languages = {"en": "English", "ru": "Русский", "de": "Deutsch"}

# Вставьте свой полный словарь, я оставляю минимальный набор, остальные ключи подхватятся как fallback
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
        "message": "Message",
        "send_copy": "Send me a copy",
        "attach_pdf": "Attach PDF",
        "upload_file": "Attach file",
        "submit": "Submit",
        "error_name": "Please enter your name",
        "error_email": "Please enter a valid email",
        "error_select_options": "Select at least one option"
    },
    "ru": {
        "select_brand": "Выберите марку",
        "select_model": "Выберите модель",
        "select_generation": "Выберите поколение",
        "select_fuel": "Выберите тип топлива",
        "select_engine": "Выберите двигатель",
        "select_stage": "Выберите Stage",
        "stage_power": "Только мощность",
        "stage_options_only": "Только опции",
        "stage_full": "Полный пакет",
        "options": "Опции",
        "form_title": "Свяжитесь с нами",
        "name": "Имя",
        "email": "Email",
        "message": "Сообщение",
        "send_copy": "Прислать копию",
        "attach_pdf": "Приложить PDF",
        "upload_file": "Загрузить файл",
        "submit": "Отправить",
        "error_name": "Введите имя",
        "error_email": "Введите корректный email",
        "error_select_options": "Выберите хотя бы одну опцию"
    },
    "de": {
        "select_brand": "Marke auswählen",
        "select_model": "Modell auswählen",
        "select_generation": "Generation auswählen",
        "select_fuel": "Kraftstoff auswählen",
        "select_engine": "Motor auswählen",
        "select_stage": "Stage auswählen",
        "stage_power": "Nur Leistung",
        "stage_options_only": "Nur Optionen",
        "stage_full": "Komplettpaket",
        "options": "Optionen",
        "form_title": "Kontakt",
        "name": "Name",
        "email": "E-Mail",
        "message": "Nachricht",
        "send_copy": "Kopie an mich senden",
        "attach_pdf": "PDF anhängen",
        "upload_file": "Datei anhängen",
        "submit": "Senden",
        "error_name": "Bitte Namen eingeben",
        "error_email": "Bitte gültige E‑Mail eingeben",
        "error_select_options": "Wählen Sie mindestens eine Option"
    }
}

class SafeTranslations(UserDict):
    def __missing__(self, key):
        return key

# ---------- Load selected language ----------
language = st.selectbox("🌐 Language / Язык / Sprache", list(languages.keys()), format_func=lambda x: languages[x])
_t = SafeTranslations(translations.get(language, translations["en"]))

# ---------- DB helpers ----------
@st.cache_data
def load_db():
    db_path = os.path.join(os.getcwd(), "data", "full_database.json")
    with open(db_path, encoding="utf-8") as f:
        return json.load(f)

def _prune_empty(node):
    if isinstance(node, dict):
        cleaned = {k: _prune_empty(v) for k, v in node.items()}
        return {k: v for k, v in cleaned.items() if v not in (None, {}, [], "")}
    return node

raw_database = load_db()
database = _prune_empty(raw_database)

# ---------- Session helpers ----------

def _clear_state(*keys):
    for k in keys:
        st.session_state.pop(k, None)

# ---------- UI ----------
st.title("🚗 Level of Speed Configurator")

brand = st.selectbox(
    _t["select_brand"],
    [""] + list(database.keys()),
    key="brand",
    on_change=lambda: _clear_state("model", "generation", "fuel", "engine", "stage", "options"),
)
if not brand:
    st.stop()

model = st.selectbox(
    _t["select_model"],
    [""] + list(database[brand].keys()),
    key="model",
    on_change=lambda: _clear_state("generation", "fuel", "engine", "stage", "options"),
)
if not model:
    st.stop()

generation = st.selectbox(
    _t["select_generation"],
    [""] + list(database[brand][model].keys()),
    key="generation",
    on_change=lambda: _clear_state("fuel", "engine", "stage", "options"),
)
if not generation:
    st.stop()

engines_data = database[brand][model][generation]
fuels = sorted({d.get("Type") for d in engines_data.values() if isinstance(d, dict) and d})

fuel = st.selectbox(
    _t["select_fuel"],
    [""] + fuels,
    key="fuel",
    on_change=lambda: _clear_state("engine", "stage", "options"),
)
if not fuel:
    st.stop()

engines = [name for name, d in engines_data.items() if isinstance(d, dict) and d.get("Type") == fuel]
engine = st.selectbox(
    _t["select_engine"],
    [""] + engines,
    key="engine",
    on_change=lambda: _clear_state("stage", "options"),
)
if not engine:
    st.stop()

stage = st.selectbox(
    _t["select_stage"],
    [_t["stage_power"], _t["stage_options_only"], _t["stage_full"]],
    key="stage",
    on_change=lambda: _clear_state("options"),
)
opts_selected = []

# ---------- Charts ----------
rec = engines_data[engine]
orig_hp, tuned_hp = rec["Original HP"], rec["Tuned HP"]
orig_tq, tuned_tq = rec["Original Torque"], rec["Tuned Torque"]
y_max = max(orig_hp, tuned_hp, orig_tq, tuned_tq) * 1.2

st.markdown("---")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
ax1.bar(["Stock", "LoS"], [orig_hp, tuned_hp]); ax1.set_ylim(0, y_max); ax1.set_title("HP")
for i, v in enumerate([orig_hp, tuned_hp]): ax1.text(i, v * 1.02, f"{v} hp", ha="center")
ax2.bar(["Stock", "LoS"], [orig_tq, tuned_tq]); ax2.set_ylim(0, y_max); ax2.set_title("Torque")
for i, v in enumerate([orig_tq, tuned_tq]): ax2.text(i, v * 1.02, f"{v} Nm", ha="center")
plt.tight_layout(); st.pyplot(fig); plt.close(fig)

# ---------- Options ----------
if stage in (_t["stage_full"], _t["stage_options_only"]):
    st.markdown("----")
    opts_selected = st.multiselect(_t["options"], rec.get("Options", []), key="options")

st.write("")

# ---------- Contact form ----------
with st.form("contact_form"):
    name = st.text_input(_t["name"])
    email = st.text_input(_t["email"])
    vin = st.text_input("VIN")
    message = st.text
