import streamlit as st
import matplotlib.pyplot as plt
import os, json, io, textwrap, requests, smtplib, email.message, tempfile
from collections import UserDict
from fpdf import FPDF

# ---------------- Page Config -----------------
st.set_page_config(page_title="Level of Speed Configurator", layout="wide")

# ---------------- Translations ----------------
languages = {"en": "English", "ru": "Русский", "de": "Deutsch"}
# Full translations for supported languages
_en = {
    "select_brand": "Select Brand", "select_model": "Select Model", "select_generation": "Select Generation", "select_fuel": "Select Fuel",
    "select_engine": "Select Engine", "select_stage": "Select Stage",
    "stage_power": "Power only", "stage_options_only": "Options only", "stage_full": "Full package",
    "options": "Options", "form_title": "Contact Us",
    "name": "Name", "email": "Email", "vin": "VIN", "message": "Message",
    "send_copy": "Send me a copy", "attach_pdf": "Attach PDF report",
    "upload_file": "Attach file", "submit": "Submit", "success": "Thank you! We will contact you soon.",
    "error_name": "Please enter your name", "error_email": "Please enter a valid email",
    "error_select_options": "Select at least one option", "difference": "Difference"
}
# For now, reuse English translations for Russian and German
translations = {"en": _en, "ru": _en, "de": _en}
class _T(UserDict):(UserDict):
    def __missing__(self, key):
        return key

# ---------------- Header ----------------------
_, col_lang = st.columns([10,2])
with col_lang:
    lang = st.selectbox("", list(languages.keys()), format_func=lambda x: languages[x], label_visibility="collapsed")
_t = _T(translations.get(lang, translations["en"]))

# ---------------- Logo ------------------------
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
clear = lambda *k: [st.session_state.pop(x,None) for x in k]

# ---------------- Selection flow --------------
brand = st.selectbox(_t["select_brand"], [""]+sorted(db.keys()), key="brand", on_change=lambda: clear("model","generation","fuel","engine","stage","options"))
if not brand: st.stop()
model = st.selectbox(_t["select_model"], [""]+sorted(db[brand].keys()), key="model", on_change=lambda: clear("generation","fuel","engine","stage","options"))
if not model: st.stop()
gen = st.selectbox(_t["select_generation"], [""]+sorted(db[brand][model].keys()), key="generation", on_change=lambda: clear("fuel","engine","stage","options"))
if not gen: st.stop()
engines = db[brand][model][gen]
fuel_opts = sorted({d.get("Type") for d in engines.values() if isinstance(d,dict)})
fuel = st.selectbox(_t["select_fuel"], [""]+fuel_opts, key="fuel", on_change=lambda: clear("engine","stage","options"))
if not fuel: st.stop()
engine = st.selectbox(_t["select_engine"], [""]+[k for k,v in engines.items() if isinstance(v,dict) and v.get("Type")==fuel], key="engine", on_change=lambda: clear("stage","options"))
if not engine: st.stop()
stage = st.selectbox(_t["select_stage"], [_t["stage_power"],_t["stage_options_only"],_t["stage_full"]], key="stage")
opts = st.multiselect(_t["options"], engines[engine].get("Options",[])) if stage in (_t["stage_full"],_t["stage_options_only"]) else []

st.markdown("---")
# Chart code omitted for brevity
# Contact form
st.header(_t["form_title"])
with st.form("contact_form"):
    name = st.text_input(_t["name"])
    email_addr = st.text_input(_t["email"])
    vin = st.text_input(_t["vin"])
    message = st.text_area(_t["message"],height=120)
    uploaded_file = st.file_uploader(_t["upload_file"], type=["txt","pdf","jpg","png","rar","zip"])
    attach_pdf = st.checkbox(_t["attach_pdf"])
    send_copy = st.checkbox(_t["send_copy"])
    submit = st.form_submit_button(_t["submit"])
if not submit: st.stop()
# Validation omitted
# Telegram omitted
# Email block
if send_copy:
    selection_text = textwrap.dedent(f"""
Brand: {brand}
Model: {model}
Generation: {gen}
Engine: {engine}
Stage: {stage}
Options: {', '.join(opts) or '-'}
Name: {name}
Email: {email_addr}
VIN: {vin}
Message: {message}
""")
    msg = email.message.EmailMessage()
    msg["Subject"]="Your LOS Configuration Report"
    msg["From"]=os.getenv("SMTP_SENDER")
    msg["To"]=email_addr
    msg.set_content(selection_text)
    pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", size=12)
    for line in selection_text.strip().split("\n"):
        pdf.cell(0,8,txt=line,ln=True)
    pdf.ln(4)
    if chart_bytes:
        with tempfile.NamedTemporaryFile(delete=False,suffix=".png") as tmp:
            tmp.write(chart_bytes); tmp.flush()
            pdf.image(tmp.name,x=10,y=pdf.get_y(),w=pdf.w-20)
    with tempfile.NamedTemporaryFile(delete=False,suffix=".pdf") as tmp:
        pdf.output(tmp.name); tmp.seek(0)
        msg.add_attachment(tmp.read(),maintype="application",subtype="pdf",filename="report.pdf")
    host=os.getenv("SMTP_HOST"); port=int(os.getenv("SMTP_PORT","587")); user=os.getenv("SMTP_USER"); pwd=os.getenv("SMTP_PASS")
    try:
        if port==465: server=smtplib.SMTP_SSL(host,port)
        else: server=smtplib.SMTP(host,port);server.ehlo();server.starttls()
        server.login(user,pwd); server.send_message(msg); server.quit()
    except Exception as e: st.warning(f"Email error: {e}")
st.success(_t["success"])
st.stop()
