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

# Multilanguage support
languages = {"en": "English", "ru": "Русский", "de": "Deutsch"}
translations = {
    "en": { ... },  # as before
    "ru": { ... },
    "de": { ... }
}

dirs = list(languages.keys())

# Logo and title
cols = st.columns([1, 8, 1])
with cols[1]:
    logo_path = os.path.join(os.getcwd(), 'logo.png')
    if os.path.exists(logo_path):
        st.image(logo_path, use_column_width=True)

# Language selector and app title
langcols = st.columns([8, 1])
with langcols[1]:
    language = st.selectbox(
        '', dirs, index=dirs.index('en'),
        format_func=lambda c: languages[c], key='language', label_visibility='collapsed'
    )
with langcols[0]:
    st.title(translations[language]['title'])

# current translations
t = translations[language]

# load database
db_path = os.path.join(os.getcwd(), 'data', 'full_database.json')
@st.cache_data
def load_db():
    with open(db_path, encoding='utf-8') as f:
        return json.load(f)

database = load_db()

# Steps
brand = st.selectbox(t['select_brand'], [''] + list(database.keys()), key='brand')
if not brand: st.stop()
model = st.selectbox(t['select_model'], [''] + list(database[brand].keys()), key='model')
if not model: st.stop()
generation = st.selectbox(t['select_generation'], [''] + list(database[brand][model].keys()), key='generation')
if not generation: st.stop()

engines_data = database[brand][model][generation]
# fuel
fuels = sorted({d.get('Type') for d in engines_data.values() if isinstance(d, dict)})
fuel = st.selectbox(t['select_fuel'], [''] + fuels, key='fuel')
if not fuel: st.stop()
# engine
engines = [n for n, d in engines_data.items() if isinstance(d, dict) and d.get('Type') == fuel]
engine = st.selectbox(t['select_engine'], [''] + engines, key='engine')
if not engine: st.stop()
# stage and options
stage = st.selectbox(t['select_stage'], [t['stage_power'], t['stage_options_only'], t['stage_full']], key='stage')
opts_selected = []
if stage != t['stage_power']:
    st.markdown('----')
    opts_selected = st.multiselect(t['options'], engines_data[engine]['Options'], key='options')

st.write('')
# charts
data = engines_data[engine]
t0, t1 = data['Original HP'], data['Tuned HP']
tq0, tq1 = data['Original Torque'], data['Tuned Torque']
ym = max(t0, t1, tq0, tq1) * 1.2
fig, (ax1, ax2) = plt.subplots(1,2,figsize=(12,5),facecolor='black')
for ax, vals, diff_key, ylabel in [
    (ax1, [t0,t1], 'difference_hp', 'original_hp'),
    (ax2, [tq0,tq1], 'difference_torque', 'original_torque')]:
    ax.set_facecolor('black')
    ax.bar(['Stock','LoS'], vals, color=['#A0A0A0','#FF0000'])
    ax.set_ylim(0, ym)
    for i,v in enumerate(vals): ax.text(i, v*1.02, f"{v}{' hp' if ax is ax1 else ' Nm'}", ha='center', color='white')
    ax.text(0.5,-0.15, t[diff_key].format(hp=t1-t0 if ax is ax1 else '', torque=tq1-tq0 if ax is ax2 else ''), transform=ax.transAxes, ha='center', color='white')
    ax.set_ylabel(t[ylabel], color='white'); ax.tick_params(colors='white')
plt.tight_layout(); st.pyplot(fig); plt.close(fig)

# form
st.markdown('----'); st.markdown(f"### {t['form_title']}")
with st.form('form'):
    name = st.text_input(t['name'], key='name')
    email = st.text_input(t['email'], key='email')
    vin = st.text_input(t['vin'], key='vin')
    msg = st.text_area(t['message'], key='message')
    send_copy = st.checkbox(t['send_copy'], key='send_copy')
    attach_pdf = st.checkbox(t['attach_pdf'], key='attach_pdf')
    up = st.file_uploader(t['upload_file'], key='upload_file')
    ok = st.form_submit_button(t['submit'])
if ok:
    if not name: st.error(t['error_name']); st.stop()
    if not email or '@' not in email: st.error(t['error_email']); st.stop()
    if stage==t['stage_full'] and not opts_selected: st.error(t['error_select_options']); st.stop()
    opts = ', '.join(opts_selected) if opts_selected else 'N/A'
    msg_txt = (
        f"📩 LoS Config Request\n"
        f"Brand: {brand}\nModel: {model}\nGeneration: {generation}\n"
        f"Engine: {engine}\nStage: {stage}\nOptions: {opts}\n"
        f"Name: {name}\nEmail: {email}\nVIN: {vin}\nMessage: {msg}"
    )
    # Telegram
    try:
        bot=st.secrets['telegram']['token']; chat=st.secrets['telegram']['chat_id']
        requests.post(f"https://api.telegram.org/bot{bot}/sendMessage", data={"chat_id":chat,"text":msg_txt})
        if up: requests.post(f"https://api.telegram.org/bot{bot}/sendDocument", data={"chat_id":chat}, files={"document":(up.name,up.getvalue())})
    except: pass
    # email
    if send_copy:
        from email.message import EmailMessage; import smtplib
        conf=st.secrets['smtp']; em=EmailMessage()
        em['Subject']='Your LoS Config Copy'; em['From']=conf['sender_email']; em['To']=email; em.set_content(msg_txt)
        if attach_pdf:
            buf=io.BytesIO(); fig.savefig(buf,format='PNG'); buf.seek(0)
            tmp=tempfile.NamedTemporaryFile(delete=False,suffix='.png'); tmp.write(buf.getvalue()); tmp.close()
            pdf=FPDF(); pdf.add_page(); pdf.image(tmp.name,10,10,190); os.remove(tmp.name)
            em.add_attachment(pdf.output(dest='S').encode('latin-1'), maintype='application', subtype='pdf', filename='LoS_Report.pdf')
        with smtplib.SMTP_SSL(conf['server'],conf['port']) as s: s.login(conf['username'],conf['password']); s.send_message(em)
    # download
    if attach_pdf:
        buf=io.BytesIO(); fig.savefig(buf,format='PNG'); buf.seek(0)
        tmp=tempfile.NamedTemporaryFile(delete=False,suffix='.png'); tmp.write(buf.getvalue()); tmp.close()
        pdf=FPDF(); pdf.add_page(); pdf.image(tmp.name,10,10,190); os.remove(tmp.name)
        st.download_button(t['attach_pdf'], data=pdf.output(dest='S').encode('latin-1'), file_name='LoS_Report.pdf', mime='application/pdf')
    st.success(t['success_message'])
