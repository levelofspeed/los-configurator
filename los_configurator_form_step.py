import streamlit as st
import matplotlib.pyplot as plt
import os
import json
import requests
import io
import tempfile
from fpdf import FPDF

# Page config
st.set_page_config(page_title="Level of Speed Configurator", layout="wide")

# Multilanguage support (оставил как в оригинале)
languages = {"en": "English", "ru": "Русский", "de": "Deutsch"}
translations = {
    "en": {
        # … полный словарь перевода из вашего исходника …
    },
    "ru": {
        # …
    },
    "de": {
        # …
    },
}

# --------- БАЗА ДАННЫХ ---------
@st.cache_data
def load_db():
    db_path = os.path.join(os.getcwd(), "data", "full_database.json")
    with open(db_path, encoding="utf-8") as f:
        return json.load(f)

# Удаляем пустые ветки, чтобы видны были только реально заполненные модели/двигатели

def _prune_empty(node):
    """Recursively remove keys that point to empty dicts/lists/None/''."""
    if isinstance(node, dict):
        cleaned = {k: _prune_empty(v) for k, v in node.items()}
        return {k: v for k, v in cleaned.items() if v not in (None, {}, [], "")}
    return node

# Загружаем и чистим базу
raw_database = load_db()
database = _prune_empty(raw_database)

# --------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---------

def _clear_state(*keys):
    """Удалить из session_state зависимые ключи, чтобы они переинициализировались."""
    for k in keys:
        if k in st.session_state:
            del st.session_state[k]

# --------- UI ---------

# Язык интерфейса
language = st.selectbox("🌐 Language / Язык / Sprache", list(languages.keys()), format_func=lambda x: languages[x])
_t = translations.get(language, translations["en"])

st.title("🚗 Level of Speed Configurator")

# --------- ШАГ 1. БРЕНД ---------
brand = st.selectbox(
    _t["select_brand"],
    [""] + list(database.keys()),
    key="brand",
    on_change=lambda: _clear_state("model", "generation", "fuel", "engine", "stage", "options"),
)
if not brand:
    st.stop()

# --------- ШАГ 2. МОДЕЛЬ ---------
model = st.selectbox(
    _t["select_model"],
    [""] + list(database[brand].keys()),
    key="model",
    on_change=lambda: _clear_state("generation", "fuel", "engine", "stage", "options"),
)
if not model:
    st.stop()

# --------- ШАГ 3. ПОКОЛЕНИЕ ---------
generation = st.selectbox(
    _t["select_generation"],
    [""] + list(database[brand][model].keys()),
    key="generation",
    on_change=lambda: _clear_state("fuel", "engine", "stage", "options"),
)
if not generation:
    st.stop()

# --------- ШАГ 4. ТИП ТОПЛИВА ---------
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

# --------- ШАГ 5. ДВИГАТЕЛЬ ---------
engines = [name for name, d in engines_data.items() if isinstance(d, dict) and d.get("Type") == fuel]
engine = st.selectbox(
    _t["select_engine"],
    [""] + engines,
    key="engine",
    on_change=lambda: _clear_state("stage", "options"),
)
if not engine:
    st.stop()

# --------- ШАГ 6. СЦЕНАРИЙ (Stage) ---------
stage = st.selectbox(
    _t["select_stage"],
    [_t["stage_power"], _t["stage_options_only"], _t["stage_full"]],
    key="stage",
    on_change=lambda: _clear_state("options"),
)
opts_selected = []

# --------- ДАННЫЕ ПО ДВИГАТЕЛЮ И ГРАФИК ---------
rec = engines_data[engine]
orig_hp, tuned_hp = rec["Original HP"], rec["Tuned HP"]
orig_tq, tuned_tq = rec["Original Torque"], rec["Tuned Torque"]

# Столбчатая диаграмма с одинаковым масштабом
st.markdown("---")
y_max = max(orig_hp, tuned_hp, orig_tq, tuned_tq) * 1.2
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), facecolor="white")

# HP
ax1.bar(["Stock", "LoS"], [orig_hp, tuned_hp])
ax1.set_ylim(0, y_max)
for i, v in enumerate([orig_hp, tuned_hp]):
    ax1.text(i, v * 1.02, f"{v} hp", ha="center")
ax1.set_title("Horsepower")

# Torque
ax2.bar(["Stock", "LoS"], [orig_tq, tuned_tq])
ax2.set_ylim(0, y_max)
for i, v in enumerate([orig_tq, tuned_tq]):
    ax2.text(i, v * 1.02, f"{v} Nm", ha="center")
ax2.set_title("Torque")

plt.tight_layout()
st.pyplot(fig)
plt.close(fig)

# --------- ОПЦИИ / Multiselect ---------
if stage in (_t["stage_full"], _t["stage_options_only"]):
    st.markdown("----")
    opts_selected = st.multiselect(
        _t["options"],
        rec.get("Options", []),
        key="options",
    )

st.write("")

# --------- КОНТАКТНАЯ ФОРМА ---------
with st.form("contact_form"):
    name = st.text_input(_t["name"])
    email = st.text_input(_t["email"])
    vin = st.text_input("VIN")
    message = st.text_area(_t["message"], height=100)
    send_copy = st.checkbox(_t["send_copy"])
    attach_pdf = st.checkbox(_t["attach_pdf"])
    uploaded_file = st.file_uploader(_t["upload_file"], type=["txt", "pdf", "jpg", "png"])

    submit = st.form_submit_button(_t["submit"])

if not submit:
    st.stop()

# Простейшая валидация
if not name:
    st.error(_t.get("error_name", "Name required"))
    st.stop()
if not email or "@" not in email:
    st.error(_t.get("error_email", "Invalid email"))
    st.stop()
if stage == _t.get("stage_full") and not opts_selected:
    st.error(_t.get("error_select_options", "Select at least one option"))
    st.stop()

# --------- ФОРМИРОВАНИЕ PDF, ОТПРАВКА В TG/EMAIL (оставил без изменений) ---------
# … ваш оригинальный код отправки Telegram и письма …
