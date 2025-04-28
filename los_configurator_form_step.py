import streamlit as st
import matplotlib.pyplot as plt
import os, json
from collections import UserDict

# ---------- Page config ----------
st.set_page_config(page_title="Level of Speed Configurator", layout="wide")

# ---------- Translations ----------
languages = {"en": "English", "ru": "Русский", "de": "Deutsch"}

translations = {
    "en": {"select_brand": "Select Brand","select_model": "Select Model","select_generation": "Select Generation","select_fuel": "Select Fuel","select_engine": "Select Engine","select_stage": "Select Stage","stage_power": "Power only","stage_options_only": "Options only","stage_full": "Full package","options": "Options","form_title": "Contact Us","name": "Name","email": "Email","vin": "VIN","message": "Message","send_copy": "Send me a copy","attach_pdf": "Attach PDF","upload_file": "Attach file","submit": "Submit","success": "Thank you! We will contact you soon.","error_name": "Please enter your name","error_email": "Please enter a valid email","error_select_options": "Select at least one option","difference": "Difference"},
    "ru": {"select_brand": "Выберите марку","select_model": "Выберите модель","select_generation": "Выберите поколение","select_fuel": "Выберите топливо","select_engine": "Выберите двигатель","select_stage": "Выберите Stage","stage_power": "Только мощность","stage_options_only": "Только опции","stage_full": "Полный пакет","options": "Опции","form_title": "Свяжитесь с нами","name": "Имя","email": "Email","vin": "VIN","message": "Сообщение","send_copy": "Отправить копию мне","attach_pdf": "Приложить PDF","upload_file": "Прикрепить файл","submit": "Отправить","success": "Спасибо! Мы скоро свяжемся.","error_name": "Введите имя","error_email": "Введите корректный email","error_select_options": "Выберите хотя бы одну опцию","difference": "Разница"},
    "de": {"select_brand": "Marke wählen","select_model": "Modell wählen","select_generation": "Generation wählen","select_fuel": "Kraftstoff wählen","select_engine": "Motor wählen","select_stage": "Stage wählen","stage_power": "Nur Leistung","stage_options_only": "Nur Optionen","stage_full": "Komplettpaket","options": "Optionen","form_title": "Kontakt","name": "Name","email": "E-Mail","vin": "VIN","message": "Nachricht","send_copy": "Kopie an mich senden","attach_pdf": "PDF anhängen","upload_file": "Datei anhängen","submit": "Senden","success": "Danke! Wir melden uns bald.","error_name": "Bitte Namen eingeben","error_email": "Bitte gültige E-Mail eingeben","error_select_options": "Wählen Sie mindestens eine Option","difference": "Differenz"}
}

class SafeTranslations(UserDict):
    def __missing__(self, key):
        return key

# ---------- Language selector ----------
_, col_lang = st.columns([10, 2])
with col_lang:
    language = st.selectbox("", list(languages.keys()), format_func=lambda x: languages[x])
_t = SafeTranslations(translations.get(language, translations["en"]))

# ---------- Logo (centered, bigger) ----------
logo_path = next((p for p in ("logo.png", "logo_white.png") if os.path.exists(p)), None)
if logo_path:
    _, col_logo, _ = st.columns([1, 2, 1])
    with col_logo:
        st.image(logo_path, width=180)

# ---------- Title ----------
st.title("Level of Speed Configurator 🚘")

# ---------- DB ----------
@st.cache_data
def load_db():
    with open(os.path.join("data", "full_database.json"), encoding="utf-8") as f:
        return json.load(f)

def _prune(n):
    return {k: _prune(v) for k, v in n.items() if v not in (None, {}, [], "")} if isinstance(n, dict) else n

database = _prune(load_db())

def _clear(*keys):
    for k in keys:
        st.session_state.pop(k, None)

# ---------- Selections ----------
brand = st.selectbox(_t["select_brand"], [""] + sorted(database.keys()), key="brand",
                     on_change=lambda: _clear("model", "generation", "fuel", "engine", "stage", "options"))
if not brand: st.stop()
model = st.selectbox(_t["select_model"], [""] + sorted(database[brand].keys()), key="model",
                     on_change=lambda: _clear("generation", "fuel", "engine", "stage", "options"))
if not model: st.stop()
generation = st.selectbox(_t["select_generation"], [""] + sorted(database[brand][model].keys()), key="generation",
                          on_change=lambda: _clear("fuel", "engine", "stage", "options"))
if not generation: st.stop()
engines_data = database[brand][model][generation]
fuels = sorted({d.get("Type") for d in engines_data.values() if isinstance(d, dict) and d})
fuel = st.selectbox(_t["select_fuel"], [""] + fuels, key="fuel", on_change=lambda: _clear("engine", "stage", "options"))
if not fuel: st.stop()
engines = [n for n, d in engines_data.items() if isinstance(d, dict) and d.get("Type") == fuel]
engine = st.selectbox(_t["select_engine"], [""] + engines, key="engine", on_change=lambda: _clear("stage", "options"))
if not engine: st.stop()
stage = st.selectbox(_t["select_stage"], [_t["stage_power"], _t["stage_options_only"], _t["stage_full"]],
                     key="stage", on_change=lambda: _clear("options"))

# ---------- Options ----------
opts_selected = []
if stage in (_t["stage_full"], _t["stage_options_only"]):
    opts_selected = st.multiselect(_t["options"], engines_data[engine].get("Options", []), key="options")

st.markdown("---")

# ---------- Charts ----------
try:
    rec = engines_data[engine]
    orig_hp, tuned_hp = rec["Original HP"], rec["Tuned HP"]
    orig_tq, tuned_tq = rec["Original Torque"], rec["Tuned Torque"]
    stock_color, tuned_color = "#808080", "#FF0000"
    y_max = max(orig_hp, tuned_hp, orig_tq, tuned_tq) * 1.2

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4), facecolor="black")
    for ax in (ax1, ax2):
        ax.set_facecolor("black"); ax.tick_params(colors="white")
        for s in ax.spines.values(): s.set_color("white")

    ax1.bar(["Stock", "LoS"], [orig_hp, tuned_hp], color=[stock_color, tuned_color])
    ax2.bar(["Stock", "LoS"], [orig_tq, tuned_tq], color=[stock_color, tuned_color])
    ax1.set_ylim(0, y_max); ax2.set_ylim(0, y_max)
    ax1.set_title("HP", color="white"); ax2.set_title("Torque", color="white")

    for i, v in enumerate([orig_hp, tuned_hp]):
        ax1.text(i, v * 1.02, f"{v} hp", ha="center", color="white")
    for i, v in enumerate([orig_tq, tuned_tq]):
        ax2.text(i, v * 1.02, f"{v} Nm", ha="center", color="white")

    ax1.text(0.5, -0.15, f"{_t['difference']} +{tuned_hp - orig_hp} hp", ha="center", color="white", transform=ax1.transAxes)
    ax2.text(0.5, -0.15, f"{_t['difference']} +{tuned_tq - orig_tq} Nm", ha="center", color="white", transform=ax2.transAxes)

    plt.tight_layout(); st.pyplot(fig); plt.close(fig)
except Exception as e:
    st.exception(e)

# ---------- Contact form ----------
st.header(_t["form_title"])
with st.form("contact_form"):
    name = st.text_input(_t["name"])
    email = st.text_input(_t["email"])
    vin = st.text_input(_t["vin"])
    message = st.text_area(_t["message"], height=120)
    send_copy = st.checkbox(_t["send_copy"])
    attach_pdf = st.checkbox(_t["attach_pdf"])
    uploaded_file = st.file_uploader(_t["upload_file"], type=["txt", "pdf", "jpg", "png"])
    submit = st.form_submit_button(_t["submit"])

# ---------- Form validation ----------
if not submit:
    st.stop()
if not name:
    st.error(_t["error_name"]); st.stop()
if not email or "@" not in email:
    st.error(_t["error_email"]); st.stop()
if stage == _t["stage_full"] and not opts_selected:
    st.error(_t["error_select_options"]); st.stop()

st.success(_t["success"])
