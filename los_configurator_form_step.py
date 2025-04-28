import streamlit as st
import matplotlib.pyplot as plt
import os, json
from collections import UserDict

# ---------- Page config ----------
st.set_page_config(page_title="Level of Speed Configurator", layout="wide")

# ---------- Translations ----------
languages = {"en": "English", "ru": "Русский", "de": "Deutsch"}

translations = {
    # ... (тот же словарь, не изменяем для краткости) ...
}

class SafeTranslations(UserDict):
    def __missing__(self, key):
        return key

# ---------- Language selector (top‑right) ----------
col_spacer, col_lang = st.columns([12, 1])
with col_lang:
    language = st.selectbox("", list(languages.keys()), format_func=lambda x: languages[x])
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

database = _prune_empty(load_db())

# ---------- Session helpers ----------
def _clear_state(*keys):
    for k in keys:
        st.session_state.pop(k, None)

# ---------- UI ----------
st.title("🚗 Level of Speed Configurator")

brand = st.selectbox(_t["select_brand"], [""] + sorted(database.keys()), key="brand", on_change=lambda: _clear_state("model", "generation", "fuel", "engine", "stage", "options"))
if not brand: st.stop()

model = st.selectbox(_t["select_model"], [""] + sorted(database[brand].keys()), key="model", on_change=lambda: _clear_state("generation", "fuel", "engine", "stage", "options"))
if not model: st.stop()

generation = st.selectbox(_t["select_generation"], [""] + sorted(database[brand][model].keys()), key="generation", on_change=lambda: _clear_state("fuel", "engine", "stage", "options"))
if not generation: st.stop()

engines_data = database[brand][model][generation]
fuels = sorted({d.get("Type") for d in engines_data.values() if isinstance(d, dict) and d})

fuel = st.selectbox(_t["select_fuel"], [""] + fuels, key="fuel", on_change=lambda: _clear_state("engine", "stage", "options"))
if not fuel: st.stop()

engines = [name for name, d in engines_data.items() if isinstance(d, dict) and d.get("Type") == fuel]
engine = st.selectbox(_t["select_engine"], [""] + engines, key="engine", on_change=lambda: _clear_state("stage", "options"))
if not engine: st.stop()

stage = st.selectbox(_t["select_stage"], [_t["stage_power"], _t["stage_options_only"], _t["stage_full"]], key="stage", on_change=lambda: _clear_state("options"))

# ---------- Options under Stage ----------
opts_selected: list[str] = []
if stage in (_t["stage_full"], _t["stage_options_only"]):
    opts_selected = st.multiselect(_t["options"], engines_data[engine].get("Options", []), key="options")

st.markdown("---")

# ---------- Charts (dark theme) ----------
try:
    rec = engines_data[engine]
    orig_hp, tuned_hp = rec["Original HP"], rec["Tuned HP"]
    orig_tq, tuned_tq = rec["Original Torque"], rec["Tuned Torque"]
    y_max = max(orig_hp, tuned_hp, orig_tq, tuned_tq) * 1.2

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4), facecolor="black")
    for ax in (ax1, ax2):
        ax.set_facecolor("black")
        ax.tick_params(colors="white")
        for spine in ax.spines.values():
            spine.set_color("white")

    ax1.bar(["Stock", "LoS"], [orig_hp, tuned_hp], color=["#808080", "#ff4136"])
    ax1.set_ylim(0, y_max); ax1.set_title("HP", color="white")
    for i, v in enumerate([orig_hp, tuned_hp]):
        ax1.text(i, v * 1.02, f"{v} hp", ha="center", color="white")

    ax2.bar(["Stock", "LoS"], [orig_tq, tuned_tq], color=["#808080", "#ff851b"])
    ax2.set_ylim(0, y_max); ax2.set_title("Torque", color="white")
    for i, v in enumerate([orig_tq, tuned_tq]):
        ax2.text(i, v * 1.02, f"{v} Nm", ha="center", color="white")

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

if not submit: st.stop()

if not name:
    st.error(_t["error_name"]); st.stop()
if not email or "@" not in email:
    st.error(_t["error_email"]); st.stop()
if stage == _t["stage_full"] and not opts_selected:
    st.error(_t["error_select_options"]); st.stop()

st.success(_t["success"])
