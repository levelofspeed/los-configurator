import streamlit as st
import matplotlib.pyplot as plt
import os, json, io, textwrap, requests, smtplib, email.message
from collections import UserDict
from fpdf import FPDF

# ---------------- Page Config -----------------
st.set_page_config(page_title="Level of Speed Configurator", layout="wide")

# ---------------- Translations ----------------
languages = {"en": "English", "ru": "Русский", "de": "Deutsch"}
_en = {"select_brand": "Select Brand", "select_model": "Select Model", "select_generation": "Select Generation", "select_fuel": "Select Fuel", "select_engine": "Select Engine", "select_stage": "Select Stage", "stage_power": "Power only", "stage_options_only": "Options only", "stage_full": "Full package", "options": "Options", "form_title": "Contact Us", "name": "Name", "email": "Email", "vin": "VIN", "message": "Message", "send_copy": "Send me a copy", "attach_pdf": "Attach PDF report", "upload_file": "Attach file", "submit": "Submit", "success": "Thank you! We will contact you soon.", "error_name": "Please enter your name", "error_email": "Please enter a valid email", "error_select_options": "Select at least one option", "difference": "Difference"}
translations = {"en": _en, "ru": _en, "de": _en}
class _T(UserDict):
    def __missing__(self, key):
        return key

# ---------------- Header ----------------------
_, col_lang = st.columns([10,2])
with col_lang:
    lang = st.selectbox("", list(languages.keys()), format_func=lambda x: languages[x], label_visibility="collapsed")
_t = _T(translations.get(lang, translations["en"]))

logo = next((p for p in ("logo.png","logo_white.png") if os.path.exists(p)), None)
if logo:
    _, c, _ = st.columns([1,2,1]); c.image(logo, width=180)

st.title("Level of Speed Configurator 🚘")

# ---------------- Load DB ---------------------
@st.cache_data
def load_db():
    with open(os.path.join("data","full_database.json"), encoding="utf-8") as f:
        return json.load(f)

def prune(node):
    return {k: prune(v) for k,v in node.items() if v not in (None,{},[],"")} if isinstance(node,dict) else node

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
chart_bytes=None
try:
    rec=engines_data[engine]; oh,th,ot,tt = rec["Original HP"],rec["Tuned HP"],rec["Original Torque"],rec["Tuned Torque"]
    ymax=max(oh,th,ot,tt)*1.2
    fig,(ax1,ax2)=plt.subplots(1,2,figsize=(10,4),facecolor="black")
    for ax in (ax1,ax2):
        ax.set_facecolor("black"); ax.tick_params(colors="white"); [s.set_color("white") for s in ax.spines.values()]
    ax1.bar(["Stock","LoS"],[oh,th],color=["#777","#e11"]); ax2.bar(["Stock","LoS"],[ot,tt],color=["#777","#e11"])
    ax1.set_ylim(0,ymax); ax2.set_ylim(0,ymax)
    for i,v in enumerate([oh,th]): ax1.text(i,v*1.02,f"{v} hp",color="white",ha="center")
    for i,v in enumerate([ot,tt]): ax2.text(i,v*1.02,f"{v} Nm",color="white",ha="center")
    ax1.text(0.5,-0.15,f"{_t['difference']} +{th-oh} hp",transform=ax1.transAxes,color="white",ha="center")
    ax2.text(0.5,-0.15,f"{_t['difference']} +{tt-ot} Nm",transform=ax2.transAxes,color="white",ha="center")
    ax1.set_title("HP",color="white"); ax2.set_title("Torque",color="white")
    plt.tight_layout(); st.pyplot(fig)
    buf=io.BytesIO(); fig.savefig(buf,format="png",dpi=150); buf.seek(0); chart_bytes=buf.getvalue(); plt.close(fig)
except Exception as e:
    st.warning(f"Chart error: {e}")

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

if not submit: st.stop()
if not name:
    st.error(_t["error_name"]); st.stop()
if "@" not in email_addr:
    st.error(_t["error_email"]); st.stop()

# ---------------- Telegram --------------------
TOKEN=os.getenv("TG_BOT_TOKEN"); CHAT=os.getenv("TG_CHAT_ID")
if TOKEN and CHAT:
    txt=f"Brand: {brand}\nModel: {model}\nGeneration: {gen}\nEngine: {engine}\nStage: {stage}\nOptions: {', '.join(opts_selected) or '-'}\nName: {name}\nEmail: {email_addr}\nVIN: {vin}\nMessage: {message}"
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT, "text": txt}, timeout=10)
        if uploaded_file is not None:
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendDocument",
                data={"chat_id": CHAT},
                files={"document": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type or "application/octet-stream")},
                timeout=20,
            )
    except Exception as e:
