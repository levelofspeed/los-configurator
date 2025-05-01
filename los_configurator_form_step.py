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

# Layout & Selector
_, col_lang = st.columns([10,2])
with col_lang:
    lang = st.selectbox("", list(languages.keys()), format_func=lambda x: languages[x], label_visibility="collapsed")
_t = _T(translations.get(lang, translations["en"]))

# Logo & Title
logo = next((p for p in ("logo.png","logo_white.png") if os.path.exists(p)), None)
if logo:
    _, c,_ = st.columns([1,4,1])
    c.image(logo, width=160)
st.title("Level of Speed Configurator 🚘")

# Load & Prune DB
@st.cache_data
def load_db():
    with open(os.path.join("data","full_database.json"), encoding="utf-8") as f:
        return json.load(f)

def prune(node):
    if isinstance(node,dict): return {k:prune(v) for k,v in node.items() if v not in (None,[],{},"")}
    return node

db=prune(load_db())
clear=lambda *k:[st.session_state.pop(x,None) for x in k]

# Selections
brand=st.selectbox(_t["select_brand"],[""]+sorted(db),key="brand",on_change=lambda:clear("model","generation","fuel","engine","stage","options"))
if not brand: st.stop()
model=st.selectbox(_t["select_model"],[""]+sorted(db[brand]),key="model",on_change=lambda:clear("generation","fuel","engine","stage","options"))
if not model: st.stop()
gen=st.selectbox(_t["select_generation"],[""]+sorted(db[brand][model]),key="generation",on_change=lambda:clear("fuel","engine","stage","options"))
if not gen: st.stop()

data=db[brand][model][gen]
fuels=sorted({d.get("Type") for d in data.values() if isinstance(d,dict)})
fuel=st.selectbox(_t["select_fuel"],[""]+fuels,key="fuel",on_change=lambda:clear("engine","stage","options"))
if not fuel: st.stop()
engines=[k for k,v in data.items() if isinstance(v,dict) and v.get("Type")==fuel]
engine=st.selectbox(_t["select_engine"],[""]+engines,key="engine",on_change=lambda:clear("stage","options"))
if not engine: st.stop()
stage=st.selectbox(_t["select_stage"],[_t["stage_power"],_t["stage_options_only"],_t["stage_full"]],key="stage")
opts=st.multiselect(_t["options"],data[engine].get("Options",[])) if stage in (_t["stage_full"],_t["stage_options_only"]) else []
st.markdown("---")

# Chart Renderer
def render_chart():
    rec=data[engine]
    oh,th=rec["Original HP"],rec["Tuned HP"]
    ot,tt=rec["Original Torque"],rec["Tuned Torque"]
    ymax=max(oh,th,ot,tt)*1.2
    fig,(a1,a2)=plt.subplots(1,2,figsize=(10,4),facecolor='black')
    for a in (a1,a2):
        a.set_facecolor('black'); a.tick_params(colors='white');
        for s in a.spines.values(): s.set_color('white')
    a1.bar(['Stock','LoS'],[oh,th],color=['#777','#E11D48'])
    a2.bar(['Stock','LoS'],[ot,tt],color=['#777','#E11D48'])
    a1.set_ylim(0,ymax); a2.set_ylim(0,ymax)
    for i,v in enumerate([oh,th]): a1.text(i,v*1.02,f"{v} hp",ha='center',color='white')
    for i,v in enumerate([ot,tt]): a2.text(i,v*1.02,f"{v} Nm",ha='center',color='white')
    a1.text(0.5,-0.15,f"{_t['difference']} +{th-oh} hp",transform=a1.transAxes,ha='center',color='white')
    a2.text(0.5,-0.15,f"{_t['difference']} +{tt-ot} Nm",transform=a2.transAxes,ha='center',color='white')
    a1.set_title('HP',color='white'); a2.set_title('Torque',color='white')
    st.pyplot(fig)
    st.markdown(f"> *{_t['chart_note']}*",unsafe_allow_html=True)
    buf=io.BytesIO(); fig.savefig(buf,format='png',dpi=150); buf.seek(0)
    data=buf.read(); plt.close(fig)
    return data

chart_bytes=None
try: chart_bytes=render_chart()
except Exception as e: st.warning(f"Chart error: {e}")

# Contact Form
st.header(_t['form_title'])
with st.form('contact_form'):
    name=st.text_input(_t['name'],key='name')
    email=st.text_input(_t['email'],key='email')
    vin=st.text_input(_t['vin'],key='vin')
    msg=st.text_area(_t['message'],height=120,key='message')
    file=st.file_uploader(_t['upload_file'],type=['txt','pdf','jpg','png','rar','zip'],key='file')
    pdf_attach=st.checkbox(_t['attach_pdf'],key='attach_pdf')
    copy=st.checkbox(_t['send_copy'],key='send_copy')
    go=st.form_submit_button(_t['submit'])

if not go: st.stop()
if not name: st.error(_t['error_name']);st.stop()
if '@' not in email: st.error(_t['error_email']);st.stop()

# Submission
try:
    # Telegram
    cfg=st.secrets.get('telegram',{})
    if cfg.get('token') and cfg.get('chat_id'):
        ttext=textwrap.dedent(f"""
Brand: {brand}
Model: {model}
Generation: {gen}
Engine: {engine}
Stage: {stage}
Options: {', '.join(opts) or '-'}
Name: {name}
Email: {email}
VIN: {vin}
Message: {msg}
"""
        )
        r=requests.post(f"https://api.telegram.org/bot{cfg['token']}/sendMessage",data={'chat_id':cfg['chat_id'],'text':ttext})
        if not r.ok: st.warning(f"Telegram error: {r.text}")
        if file:
            r2=requests.post(f"https://api.telegram.org/bot{cfg['token']}/sendDocument",data={'chat_id':cfg['chat_id']},files={'document':(file.name,file.getvalue(),file.type)})
            if not r2.ok: st.warning(f"Telegram document error: {r2.text}")
    else: st.warning('Telegram credentials not found')

    # Email + PDF
    if copy:
        sc=st.secrets.get('smtp',{})
        mb=textwrap.dedent(f"""
Brand: {brand}
Model: {model}
Generation: {gen}
Engine: {engine}
Stage: {stage}
Options: {', '.join(opts) or '-'}
Name: {name}
Email: {email}
VIN: {vin}
Message: {msg}
"""
        )
        pdf=FPDF(); pdf.add_page(); pdf.add_font('DejaVu','','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',uni=True);pdf.set_font('DejaVu',size=12)
        for ln in mb.split('\n'): pdf.cell(0,8,ln,ln=True)
        if chart_bytes and pdf_attach:
            img=tempfile.NamedTemporaryFile(delete=False,suffix='.png');img.write(chart_bytes);img.flush()
            pdf.image(img.name,x=10,y=pdf.get_y()+4,w=pdf.w-20)
            pdf.ln(8)
            pdf.set_font('DejaVu',size=10)
            pdf.multi_cell(0,6,_t['chart_note'])
        tmp=tempfile.NamedTemporaryFile(delete=False,suffix='.pdf');pdf.output(tmp.name)
        msg_email=email.message.EmailMessage();msg_email['Subject']='Level of Speed Configurator Report';msg_email['From']=sc.get('sender_email');msg_email['To']=email;msg_email.set_content(mb)
        if pdf_attach:
            with open(tmp.name,'rb') as f:msg_email.add_attachment(f.read(),maintype='application',subtype='pdf',filename='report.pdf')
        with smtplib.SMTP(sc['server'],sc['port']) as s:
            s.starttls();s.login(sc['username'],sc['password']);s.send_message(msg_email)
    st.success(_t['success'])
except Exception as e:
    st.error(f"Submission error: {e}")
st.stop()
