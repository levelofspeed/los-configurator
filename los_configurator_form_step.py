import streamlit as st
import matplotlib.pyplot as plt
import os
import json
import io
import textwrap
import requests
import smtplib
from email.message import EmailMessage
from collections import UserDict
from fpdf import FPDF

# Page Config
st.set_page_config(page_title="Level of Speed Configurator", layout="wide")

# Translations
languages = {"en": "English", "ru": "Русский", "de": "Deutsch"}
translations = {
    "en": { ... },  # same as before
    "ru": { ... },
    "de": { ... }
}

class _T(UserDict):
    def __missing__(self, key): return key

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

# Load DB
@st.cache_data
def load_db():
    with open(os.path.join("data","full_database.json"), encoding="utf-8") as f:
        return json.load(f)

def prune(node):
    if isinstance(node, dict):
        return {k: prune(v) for k,v in node.items() if v not in (None, [], {}, "")}
    return node

db = prune(load_db())
clear = lambda *keys: [st.session_state.pop(k, None) for k in keys]

# User Selections (same as before)...
# Chart Rendering (same as before)...
# After rendering chart, we return png_bytes

# Contact Form
with st.form('contact_form'):
    # inputs ...
    submitted = st.form_submit_button(_t['submit'])

if not submitted: st.stop()

# validate inputs

# Submission
try:
    # Telegram sending (same as before)

    if send_copy and chart_bytes:
        smtp_cfg = st.secrets.get('smtp', {})
        msg_email = EmailMessage()
        msg_email['Subject'] = 'Your Level of Speed Report'
        msg_email['From'] = smtp_cfg.get('sender_email')
        msg_email['To'] = email_addr
        body = textwrap.dedent(f"""
Brand: {brand}
Model: {model}
Generation: {generation}
Engine: {engine}
Stage: {stage}
Options: {', '.join(opts) or '-'}

"""
        )
        msg_email.set_content(body)
        # build PDF
        pdf = FPDF(); pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page(); pdf.add_font('DejaVu', '', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', uni=True)
        pdf.set_font('DejaVu', size=12)
        pdf.cell(0, 10, txt="Level of Speed Configuration Report", ln=True)
        # save chart bytes to temp file
        tmp_png = 'chart.png'
        with open(tmp_png, 'wb') as f:
            f.write(chart_bytes)
        pdf.image(tmp_png, x=10, y=pdf.get_y()+5, w=pdf.w-20)
        pdf.ln(60)
        # note text
        note = _t['chart_note']
        for ln in textwrap.wrap(note, 80):
            pdf.cell(0, 8, txt=ln, ln=True)
        # remove temp
        os.remove(tmp_png)
        # export
        pdf_bytes = pdf.output(dest='S').encode('latin1')
        msg_email.add_attachment(pdf_bytes, maintype='application', subtype='pdf', filename='report.pdf')
        # send email
        server = smtplib.SMTP(smtp_cfg.get('server'), smtp_cfg.get('port'))
        server.starttls(); server.login(smtp_cfg.get('username'), smtp_cfg.get('password'))
        server.send_message(msg_email); server.quit()
    st.success(_t['success'])
except Exception as e:
    st.error(f"Submission error: {e}")
