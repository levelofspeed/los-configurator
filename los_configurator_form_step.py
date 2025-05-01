import streamlit as st
import matplotlib.pyplot as plt
import os
import json
import io
import textwrap
import requests
import smtplib
import email.message
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
            "Please note that all displayed values of power and torque gains are approximate and may vary "
            "depending on many factors, including fuel quality and the current condition of the vehicle. "
            "Level of Speed recommends taking these into account when evaluating results. By confirming receipt of the report, "
            "you agree that you have read this information."
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
            "Обращаем ваше внимание, что все отображаемые значения прироста мощности и крутящего момента являются ориентировочными "
            "и могут варьироваться в зависимости от множества факторов, включая качество топлива и текущее состояние автомобиля. "
            "Компания Level of Speed рекомендует учитывать эти условия при оценке результатов. Подтверждая получение отчёта, "
            "вы соглашаетесь с тем, что ознакомились с данной информацией."
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
            "Bitte beachten Sie, dass alle angezeigten Werte für Leistungs- und Drehmomentsteigerung Richtwerte sind "
            "und je nach verschiedenen Faktoren wie Kraftstoffqualität und dem aktuellen Zustand des Fahrzeugs variieren können. "
            "Level of Speed empfiehlt, diese Bedingungen bei der Beurteilung der Ergebnisse zu berücksichtigen. "
            "Mit der Bestätigung des Erhalts des Berichts erklären Sie sich damit einverstanden, diese Informationen gelesen zu haben."
        )
    }
}

class _T(UserDict):
    def __missing__(self, key):
        return key

# Language Selector
_, col_lang = st.columns([10,2])
with col_lang:
    lang = st.selectbox("", list(languages.keys()), format_func=lambda x: languages[x], label_visibility="collapsed")
_t = _T(translations.get(lang, translations["en"]))

# Logo & Title
logo = next((p for p in ("logo.png","logo_white.png") if os.path.exists(p)), None)
if logo:
    _, col, _ = st.columns([1,4,1])
    col.image(logo, width=160)
st.title("Level of Speed Configurator 🚘")

# Load Database
@st.cache_data
def load_db():
    with open(os.path.join("data","full_database.json"), encoding="utf-8") as f:
        return json.load(f)

def prune(node):
    if isinstance(node, dict):
        return {k: prune(v) for k, v in node.items() if v not in (None, [], {}, "")}
    return node

db = prune(load_db())
clear = lambda *keys: [st.session_state.pop(k, None) for k in keys]

# User Selections
brand = st.selectbox(_t["select_brand"], [""] + sorted(db), key="brand", on_change=lambda: clear("model","generation","fuel","engine","stage","options"))
if not brand: st.stop()
model = st.selectbox(_t["select_model"], [""] + sorted(db[brand]), key="model", on_change=lambda: clear("generation","fuel","engine","stage","options"))
if not model: st.stop()
generation = st.selectbox(_t["select_generation"], [""] + sorted(db[brand][model]), key="generation", on_change=lambda: clear("fuel","engine","stage","options"))
if not generation: st.stop()

data_node = db[brand][model][generation]

fuels = sorted({info.get("Type") for info in data_node.values() if isinstance(info, dict)})
fuel = st.selectbox(_t["select_fuel"], [""] + fuels, key="fuel", on_change=lambda: clear("engine","stage","options"))
if not fuel: st.stop()

engines = [k for k, info in data_node.items() if isinstance(info, dict) and info.get("Type") == fuel]
engine = st.selectbox(_t["select_engine"], [""] + engines, key="engine", on_change=lambda: clear("stage","options"))
if not engine: st.stop()

stage = st.selectbox(_t["select_stage"],[_t["stage_power"],_t["stage_options_only"],_t["stage_full"]], key="stage")
opts = []
if stage in (_t["stage_full"], _t["stage_options_only"]):
    opts = st.multiselect(_t["options"], data_node[engine].get("Options", []), key="options")
st.markdown("---")

# Chart Rendering
def render_chart():
    rec = data_node[engine]
    orig_hp = rec.get("Original HP", 0)
    tuned_hp = rec.get("Tuned HP", 0)
    orig_tq = rec.get("Original Torque", 0)
    tuned_tq = rec.get("Tuned Torque", 0)
    ymax = max(orig_hp, tuned_hp, orig_tq, tuned_tq) * 1.2 if any([orig_hp, tuned_hp, orig_tq, tuned_tq]) else 1

    fig, axes = plt.subplots(1, 2, figsize=(10, 4), facecolor='black')
    for ax in axes:
        ax.set_facecolor('black')
        ax.tick_params(colors='white')
        for spine in ax.spines.values():
            spine.set_color('white')

    axes[0].bar(['Stock','LoS'], [orig_hp, tuned_hp], color=['#777','#E11D48'])
    axes[1].bar(['Stock','LoS'], [orig_tq, tuned_tq], color=['#777','#E11D48'])
    for ax in axes:
        ax.set_ylim(0, ymax)
    
    for i, v in enumerate([orig_hp, tuned_hp]):
        axes[0].text(i, v * 1.02, f"{v} hp", ha='center', color='white')
    for i, v in enumerate([orig_tq, tuned_tq]):
        axes[1].text(i, v * 1.02, f"{v} Nm", ha='center', color='white')

    # Differences
    axes[0].text(0.5, -0.15, f"{_t['difference']} +{tuned_hp-orig_hp} hp", transform=axes[0].transAxes, ha='center', color='white')
    axes[1].text(0.5, -0.15, f"{_t['difference']} +{tuned_tq-orig_tq} Nm", transform=axes[1].transAxes, ha='center', color='white')

    axes[0].set_title('HP', color='white')
    axes[1].set_title('Torque', color='white')

    st.pyplot(fig)
    st.markdown(f"> *{_t['chart_note']}*", unsafe_allow_html=True)

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150)
    buf.seek(0)
    png_bytes = buf.read()
    plt.close(fig)
    return png_bytes

chart_bytes = None
try:
    chart_bytes = render_chart()
except Exception as e:
    st.warning(f"Chart error: {e}")

# Contact Form
st.header(_t['form_title'])
with st.form('contact_form'):
    name = st.text_input(_t['name'], key='name')
    email = st.text_input(_t['email'], key='email')
    vin = st.text_input(_t['vin'], key='vin')
    msg = st.text_area(_t['message'], height=120, key='message')
    uploaded_file = st.file_uploader(_t['upload_file'], type=['txt','pdf','jpg','png','rar','zip'], key='file')
    attach_pdf = st.checkbox(_t['attach_pdf'], key='attach_pdf')
    send_copy = st.checkbox(_t['send_copy'], key='send_copy')
    submitted = st.form_submit_button(_t['submit'])

if not submitted:
    st.stop()
if not name:
    st.error(_t['error_name']); st.stop()
if '@' not in email:
    st.error(_t['error_email']); st.stop()

# Submission
try:
    # Telegram Notification
    tg_cfg = st.secrets.get('telegram', {})
    if tg_cfg.get('token') and tg_cfg.get('chat_id'):
        telegram_text = textwrap.dedent(f"""
Brand: {brand}
Model: {model}
Generation: {generation}
Engine: {engine}
Stage: {stage}
Options: {', '.join(opts) or '-'}
Name: {name}
Email: {email}
VIN: {vin}
Message: {msg}
"""
        )
        resp = requests.post(
            f"https://api.telegram.org/bot{tg_cfg['token']}/sendMessage",
            data={'chat_id': tg_cfg['chat_id'], 'text': telegram_text}
        )
        if not resp.ok:
            st.warning(f"Telegram error: {resp.text}")
        if uploaded_file:
            resp2 = requests.post(
                f"https://api.telegram.org/bot{tg_cfg['token']}/sendDocument",
                data={'chat_id': tg_cfg['chat_id']},
                files={'document': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            )
            if not resp2.ok:
                st.warning(f"Telegram document error: {resp2.text}")
    else:
        st.warning("Telegram credentials not configured")

    # Email + PDF Report
    if send_copy:
        smtp_cfg = st.secrets.get('smtp', {})
        msg_email = email.message.EmailMessage()
        msg_email['Subject'] = "Your Level of Speed Report"
        msg_email['From'] = smtp_cfg.get('sender_email')
        msg_email['To'] = email
        body_text = textwrap.dedent(f"""
Brand: {brand}
Model: {model}
Generation: {generation}
Engine: {engine}
Stage: {stage}
Options: {', '.join(opts) or '-'}

"""
        )
        msg_email.set_content(body_text)

        # Attach PDF with chart and note
        if attach_pdf and chart_bytes:
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            pdf.add_font('DejaVu', '', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', uni=True)
            pdf.set_font('DejaVu', size=12)
            pdf.cell(0, 10, txt="Level of Speed Configuration Report", ln=True)
            tmp_img = io.BytesIO(chart_bytes)
            pdf.image(tmp_img, x=10, y=pdf.get_y()+5, w=pdf.w-20)
            pdf.ln(60)
            # Chart note under image
            note = _t['chart_note']
            for line in textwrap.wrap(note, 80):
                pdf.cell(0, 8, txt=line, ln=True)
            tmp_pdf = io.BytesIO()
            pdf_output = pdf.output(dest='S').encode('latin1')
            msg_email.add_attachment(pdf_output, maintype='application', subtype='pdf', filename='report.pdf')

        # Send email
        server = smtplib.SMTP(smtp_cfg.get('server'), smtp_cfg.get('port'))
        server.starttls()
        server.login(smtp_cfg.get('username'), smtp_cfg.get('password'))
        server.send_message(msg_email)
        server.quit()

    st.success(_t['success'])

except Exception as e:
    st.error(f"Submission error: {e}")
