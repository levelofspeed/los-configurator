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
    c.image(logo, width=160)
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
brand = st.selectbox(_t["select_brand"], [""] + sorted(db.keys()), key="brand", on_change=lambda: clear("model","generation","fuel","engine","stage","options"))
if not brand: st.stop()
model = st.selectbox(_t["select_model"], [""] + sorted(db[brand].keys()), key="model", on_change=lambda: clear("generation","fuel","engine","stage","options"))
if not model: st.stop()
gen = st.selectbox(_t["select_generation"], [""] + sorted(db[brand][model].keys()), key="generation", on_change=lambda: clear("fuel","engine","stage","options"))
if not gen: st.stop()

engines_data = db[brand][model][gen]
fuels = sorted({d.get("Type") for d in engines_data.values() if isinstance(d, dict)})
fuel = st.selectbox(_t["select_fuel"], [""] + fuels, key="fuel", on_change=lambda: clear("engine","stage","options"))
if not fuel: st.stop()

engines = [nm for nm,d in engines_data.items() if isinstance(d, dict) and d.get("Type")==fuel]
engine = st.selectbox(_t["select_engine"], [""] + engines, key="engine", on_change=lambda: clear("stage","options"))
if not engine: st.stop()

stage = st.selectbox(_t["select_stage"],[_t["stage_power"],_t["stage_options_only"],_t["stage_full"]],key="stage")
opts = st.multiselect(_t["options"], engines_data[engine].get("Options",[])) if stage in (_t["stage_full"],_t["stage_options_only"]) else []
st.markdown("---")

# Chart Generation
chart_bytes = None
try:
    rec = engines_data[engine]
    oh = rec["Original HP"]
    th = rec["Tuned HP"]
    ot = rec["Original Torque"]
    tt = rec["Tuned Torque"]
    ymax = max(oh, th, ot, tt) * 1.2
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4), facecolor="black")
    for ax in (ax1, ax2):
        ax.set_facecolor("black")
        ax.tick_params(colors="white")
        for sp in ax.spines.values():
            sp.set_color("white")
    ax1.bar(["Stock", "LoS"], [oh, th], color=["#777777", "#E11D48"])
    ax2.bar(["Stock", "LoS"], [ot, tt], color=["#777777", "#E11D48"])
    ax1.set_ylim(0, ymax)
    ax2.set_ylim(0, ymax)
    for i, v in enumerate([oh, th]):
        ax1.text(i, v * 1.02, f"{v} hp", ha="center", color="white")
    for i, v in enumerate([ot, tt]):
        ax2.text(i, v * 1.02, f"{v} Nm", ha="center", color="white")
    ax1.text(0.5, -0.15, f"{_t['difference']} +{th - oh} hp", transform=ax1.transAxes, ha="center", color="white")
    ax2.text(0.5, -0.15, f"{_t['difference']} +{tt - ot} Nm", transform=ax2.transAxes, ha="center", color="white")
    ax1.set_title("HP", color="white")
    ax2.set_title("Torque", color="white")
    st.pyplot(fig)
    st.markdown(f"> *{_t['chart_note']}*")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    buf.seek(0)
    chart_bytes = buf.read()
    plt.close(fig)
except Exception as e:
    st.warning(f"Chart error: {e}")

# Contact Form
st.header(_t["form_title"])
with st.form("contact_form"):
    name=st.text_input(_t["name"])
    email_addr=st.text_input(_t["email"])
    vin=st.text_input(_t["vin"])
    message=st.text_area(_t["message"],height=120)
    uploaded_file=st.file_uploader(_t["upload_file"],type=["txt","pdf","jpg","png","rar","zip"])
    attach_pdf=st.checkbox(_t["attach_pdf"])
    send_copy=st.checkbox(_t["send_copy"])
    submitted=st.form_submit_button(_t["submit"])
if not submitted:st.stop()
if not name:st.error(_t["error_name"]);st.stop()
if "@" not in email_addr:st.error(_t["error_email"]);st.stop()

# Telegram
cfg = st.secrets.get("telegram", {})

if cfg.get("token") and cfg.get("chat_id"):
    tele = textwrap.dedent(f"""
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
"""
    )
    try:
        # Send text message
        resp_msg = requests.post(
            f"https://api.telegram.org/bot{cfg['token']}/sendMessage",
            data={"chat_id": cfg['chat_id'], "text": tele}
        )
        if not resp_msg.ok:
            st.warning(f"Telegram API error (message): {resp_msg.status_code} {resp_msg.text}")
        # Send document if provided
        if uploaded_file:
            resp_doc = requests.post(
                f"https://api.telegram.org/bot{cfg['token']}/sendDocument",
                data={"chat_id": cfg['chat_id']},
                files={"document": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type or "application/octet-stream")}
            )
            if not resp_doc.ok:
                st.warning(f"Telegram API error (document): {resp_doc.status_code} {resp_doc.text}")
    except Exception as e:
        st.warning(f"Telegram error: {e}")
else:
    st.warning("Telegram credentials are not set in secrets")
# Email
if send_copy:
    try:
        smtp_cfg = st.secrets.get("smtp", {})
        mail = textwrap.dedent(f"""
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
"""
        )
        # Create PDF with chart and note below
        pdf = FPDF()
        pdf.add_page()
        pdf.add_font('DejaVu', '', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', uni=True)
        pdf.set_font('DejaVu', size=12)
        # Write selection text
        for ln in mail.split("
")
"):
            pdf.cell(0, 8, ln, ln=True)
        # Embed chart image
        if chart_bytes:
            tmp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            tmp_img.write(chart_bytes)
            tmp_img.flush()
            pdf.image(tmp_img.name, x=10, y=pdf.get_y()+4, w=pdf.w-20)
        # Add space then note below chart
        pdf.ln(6)
        for note_line in _t['chart_note'].split("
")
"):
            pdf.multi_cell(0, 6, note_line)
        # Output PDF file
        tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        pdf.output(tmp_pdf.name)
        # Prepare email message
        msg = email.message.EmailMessage()
        msg["Subject"] = "Your Level of Speed Report"
        msg["From"] = smtp_cfg.get("sender_email")
        msg["To"] = email_addr
        msg.set_content(mail)
        if attach_pdf:
            with open(tmp_pdf.name, "rb") as f:
                msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename="report.pdf")
        # Send email via SMTP
        if smtp_cfg.get("port") == 465:
            srv = smtplib.SMTP_SSL(smtp_cfg.get("server"), smtp_cfg.get("port"))
        else:
            srv = smtplib.SMTP(smtp_cfg.get("server"), smtp_cfg.get("port"))
            srv.starttls()
        srv.login(smtp_cfg.get("username"), smtp_cfg.get("password"))
        srv.send_message(msg)
        srv.quit()
    except Exception as e:
        st.warning(f"Email error: {e}")

# Clear state and success
for k in ["name","email","vin","message","uploaded_file","attach_pdf","send_copy"]:
    st.session_state.pop(k,None)
st.success(_t["success"])
# Prevent re-submit crash
st.stop()
st.stop()
