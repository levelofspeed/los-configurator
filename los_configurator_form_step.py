import streamlit as st
import matplotlib.pyplot as plt
import os, json, io, textwrap, requests, smtplib, email.message
from collections import UserDict
from fpdf import FPDF

# ---------------- Page Config -----------------
st.set_page_config(page_title="Level of Speed Configurator", layout="wide")

# ---------------- Translations ----------------
languages = {"en": "English", "ru": "Русский", "de": "Deutsch"}
translations = {...}
class _T(UserDict):
    def __missing__(self,key):
        return key

# ---------------- UI Header -------------------
col_lang, _ = st.columns([2,10])
with col_lang:
    lang = st.selectbox("", list(languages.keys()), format_func=lambda x: languages[x], label_visibility="collapsed")
_t = _T(translations.get(lang, translations["en"]))

logo = next((p for p in ("logo.png","logo_white.png") if os.path.exists(p)), None)
if logo:
    _, c, _ = st.columns([1,2,1]); c.image(logo, width=180)

st.title("Level of Speed Configurator 🚘")

# ---------------- Load database ---------------
@st.cache_data
def load_db():
    with open(os.path.join("data","full_database.json"), encoding="utf-8") as f:
        return json.load(f)

def prune(n):
    return {k: prune(v) for k,v in n.items() if v not in (None,{},[],"")} if isinstance(n,dict) else n

db = prune(load_db())
clear = lambda *k: [st.session_state.pop(x, None) for x in k]

# ---------------- Selection flow --------------
brand = st.selectbox(_t["select_brand"], [""]+sorted(db.keys()), key="brand", on_change=lambda: clear("model","generation","fuel","engine","stage","options"))
if not brand: st.stop()
model = st.selectbox(_t["select_model"], [""]+sorted(db[brand].keys()), key="model", on_change=lambda: clear("generation","fuel","engine","stage","options"))
if not model: st.stop()
gen = st.selectbox(_t["select_generation"], [""]+sorted(db[brand][model].keys()), key="generation", on_change=lambda: clear("fuel","engine","stage","options"))
if not gen: st.stop()
engines_data = db[brand][model][gen]
fuels = sorted({d.get("Type") for d in engines_data.values() if isinstance(d,dict) and d})
fuel = st.selectbox(_t["select_fuel"], [""]+fuels, key="fuel", on_change=lambda: clear("engine","stage","options"))
if not fuel: st.stop()
engines = [n for n,d in engines_data.items() if isinstance(d,dict) and d.get("Type")==fuel]
engine = st.selectbox(_t["select_engine"], [""]+engines, key="engine", on_change=lambda: clear("stage","options"))
if not engine: st.stop()
stage = st.selectbox(_t["select_stage"], [_t["stage_power"], _t["stage_options_only"], _t["stage_full"]], key="stage")
opts_selected = st.multiselect(_t["options"], engines_data[engine].get("Options", [])) if stage in (_t["stage_full"], _t["stage_options_only"]) else []

st.markdown("---")

# ---------------- Chart -----------------------
# (same as before) ...

# ---------------- Contact Form ---------------
st.header(_t["form_title"])
with st.form("contact_form"):
    name = st.text_input(_t["name"])
    email_addr = st.text_input(_t["email"])
    vin = st.text_input(_t["vin"])
    message = st.text_area(_t["message"], height=120)
    uploaded_file = st.file_uploader(_t["upload_file"], type=["txt","pdf","jpg","png","rar","zip"])
    attach_pdf = st.checkbox(_t["attach_pdf"])
    send_copy = st.checkbox(_t["send_copy"])
    submit = st.form_submit_button(_t["submit"])

if not submit:
    st.stop()
if not name:
    st.error(_t["error_name"]); st.stop()
if "@" not in email_addr:
    st.error(_t["error_email"]); st.stop()

# --- Telegram send (simplified placeholder) ---
TOKEN = os.getenv("TG_BOT_TOKEN"); CHAT = os.getenv("TG_CHAT_ID")
try:
    if TOKEN and CHAT:
        txt = f"Brand: {brand}\nModel: {model}\nGen: {gen}\nEngine: {engine}\nStage: {stage}\nOpts: {', '.join(opts_selected) or '-'}\nName: {name}\nEmail: {email_addr}\nVIN: {vin}\nMsg: {message}"
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT, "text": txt}, timeout=10)
except Exception as e:
    st.warning(f"Telegram error: {e}")

st.success(_t["success"])
st.stop()
