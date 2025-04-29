import streamlit as st
import matplotlib.pyplot as plt
import os, json, textwrap, requests, smtplib, email.message
from collections import UserDict
from fpdf import FPDF

# ---------- Page config ----------
st.set_page_config(page_title="Level of Speed Configurator", layout="wide")

# ---------- Translations (compact) ----------
languages={"en":"English","ru":"Русский","de":"Deutsch"}
translations={
 "en":{"select_brand":"Select Brand","select_model":"Select Model","select_generation":"Select Generation","select_fuel":"Select Fuel","select_engine":"Select Engine","select_stage":"Select Stage","stage_power":"Power only","stage_options_only":"Options only","stage_full":"Full package","options":"Options","form_title":"Contact Us","name":"Name","email":"Email","vin":"VIN","message":"Message","send_copy":"Send me a copy","attach_pdf":"Attach PDF report","upload_file":"Attach file","submit":"Submit","success":"Thank you! We will contact you soon.","error_name":"Please enter your name","error_email":"Please enter a valid email","error_select_options":"Select at least one option","difference":"Difference"},
 "ru":{"select_brand":"Выберите марку","select_model":"Выберите модель","select_generation":"Выберите поколение","select_fuel":"Выберите топливо","select_engine":"Выберите двигатель","select_stage":"Выберите Stage","stage_power":"Только мощность","stage_options_only":"Только опции","stage_full":"Полный пакет","options":"Опции","form_title":"Свяжитесь с нами","name":"Имя","email":"Email","vin":"VIN","message":"Сообщение","send_copy":"Прислать копию","attach_pdf":"Приложить PDF отчёт","upload_file":"Прикрепить файл","submit":"Отправить","success":"Спасибо! Мы скоро свяжемся.","error_name":"Введите имя","error_email":"Введите корректный email","error_select_options":"Выберите хотя бы одну опцию","difference":"Разница"},
 "de":{"select_brand":"Marke wählen","select_model":"Modell wählen","select_generation":"Generation wählen","select_fuel":"Kraftstoff wählen","select_engine":"Motor wählen","select_stage":"Stage wählen","stage_power":"Nur Leistung","stage_options_only":"Nur Optionen","stage_full":"Komplettpaket","options":"Optionen","form_title":"Kontakt","name":"Name","email":"E‑Mail","vin":"VIN","message":"Nachricht","send_copy":"Kopie an mich senden","attach_pdf":"PDF Bericht anhängen","upload_file":"Datei anhängen","submit":"Senden","success":"Danke! Wir melden uns bald.","error_name":"Bitte Namen eingeben","error_email":"Bitte gültige E‑Mail eingeben","error_select_options":"Wählen Sie mindestens eine Option","difference":"Differenz"}}
class SafeTranslations(UserDict):
    def __missing__(self,key): return key

# ---------- Language selector ----------
_, col_lang = st.columns([10,2])
with col_lang:
    lang = st.selectbox("", list(languages.keys()), format_func=lambda x: languages[x])
_t = SafeTranslations(translations.get(lang, translations["en"]))

# ---------- Logo ----------
logo = next((p for p in ("logo.png","logo_white.png") if os.path.exists(p)), None)
if logo:
    _, c, _ = st.columns([1,2,1]); c.image(logo,width=180)

st.title("Level of Speed Configurator 🚘")

# ---------- Load DB ----------
@st.cache_data
def load_db():
    with open(os.path.join("data","full_database.json"),encoding="utf-8") as f:
        return json.load(f)

def prune(n):
    return {k:prune(v) for k,v in n.items() if v not in (None,{},[],"")} if isinstance(n,dict) else n

db = prune(load_db())
clear = lambda *k: [st.session_state.pop(x,None) for x in k]

# ---------- Selections ----------
brand = st.selectbox(_t["select_brand"],[""]+sorted(db.keys()),key="brand",on_change=lambda:clear("model","generation","fuel","engine","stage","options"))
if not brand: st.stop()
model = st.selectbox(_t["select_model"],[""]+sorted(db[brand].keys()),key="model",on_change=lambda:clear("generation","fuel","engine","stage","options"))
if not model: st.stop()
gen = st.selectbox(_t["select_generation"],[""]+sorted(db[brand][model].keys()),key="generation",on_change=lambda:clear("fuel","engine","stage","options"))
if not gen: st.stop()
engines_data = db[brand][model][gen]
fuels = sorted({d.get("Type") for d in engines_data.values() if isinstance(d,dict) and d})
fuel = st.selectbox(_t["select_fuel"],[""]+fuels,key="fuel",on_change=lambda:clear("engine","stage","options"))
if not fuel: st.stop()
engines=[n for n,d in engines_data.items() if isinstance(d,dict) and d.get("Type")==fuel]
engine = st.selectbox(_t["select_engine"],[""]+engines,key="engine",on_change=lambda:clear("stage","options"))
if not engine: st.stop()
stage = st.selectbox(_t["select_stage"],[_t["stage_power"],_t["stage_options_only"],_t["stage_full"]],key="stage",on_change=lambda:clear("options"))
opts_selected = st.multiselect(_t["options"], engines_data[engine].get("Options", []), key="options") if stage in (_t["stage_full"],_t["stage_options_only"]) else []

st.markdown("---")

# ---------- Charts ----------
try:
    rec=engines_data[engine]
    oh,th,ot,tt = rec["Original HP"], rec["Tuned HP"], rec["Original Torque"], rec["Tuned Torque"]
    ymax=max(oh,th,ot,tt)*1.2
    fig,(ax1,ax2)=plt.subplots(1,2,figsize=(10,4),facecolor="black")
    for ax in (ax1,ax2):
        ax.set_facecolor("black"); ax.tick_params(colors="white")
        for s in ax.spines.values(): s.set_color("white")
    ax1.bar(["Stock","LoS"],[oh,th],color=["#808080","#FF0000"])
    ax2.bar(["Stock","LoS"],[ot,tt],color=["#808080","#FF0000"])
    ax1.set_ylim(0,ymax); ax2.set_ylim(0,ymax)
    ax1.set_title("HP",color="white"); ax2.set_title("Torque",color="white")
    for i,v in enumerate([oh,th]): ax1.text(i,v*1.02,f"{v} hp",ha="center",color="white")
    for i,v in enumerate([ot,tt]): ax2.text(i,v*1.02,f"{v} Nm",ha="center",color="white")
    ax1.text(0.5,-0.15,f"{_t['difference']} +{th-oh} hp",ha="center",color="white",transform=ax1.transAxes)
    ax2.text(0.5,-0.15,f"{_t['difference']} +{tt-ot} Nm",ha="center",color="white",transform=ax2.transAxes)
    st.pyplot(fig); plt.close(fig)
except Exception as e:
    st.warning(f"Chart error: {e}")

# ---------- Contact form ----------
st.header(_t["form_title"])
with st.form("contact_form"):
    name = st.text_input(_t["name"])
    email_addr = st.text_input(_t["email"])
    vin = st.text_input(_t["vin"])
    message = st.text_area(_t["message"],height=120)
    send_copy = st.checkbox(_t["send_copy"])
    attach_pdf = st.checkbox(_t["attach_pdf"])
    uploaded_file = st.file_uploader(_t["upload_file"],type=["txt","pdf","jpg","png","rar","zip"])
    submit = st.form_submit_button(_t["submit"])

if not submit: st.stop()
if not name: st.error(_t["error_name"]); st.stop()
if "@" not in email_addr: st.error(_t["error_email"]); st.stop()
if stage==_t["stage_full"] and not opts_selected: st.error(_t["error_select_options"]); st.stop()

# ---------- Telegram send ----------
TOKEN, CHAT_ID = os.getenv("TG_BOT_TOKEN"), os.getenv("TG_CHAT_ID")
if TOKEN and CHAT_ID:
    tg_text = textwrap.dedent(f"""\
🏎 Level of Speed
Brand / Model / Gen: {brand} / {model} / {gen}
Fuel: {fuel}   Engine: {engine}
Stage: {stage}
Options: {', '.join(opts_selected) or '-'}
Name: {name}
Email: {email_addr}
VIN: {vin}
Message: {message}
""")
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": tg_text}, timeout=10
        )
        if uploaded_file is not None:
            uploaded_file.seek(0)
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendDocument",
                data={"chat_id": CHAT_ID},
                files={"document": (uploaded_file.name, uploaded_file.read(), uploaded_file.type or "application/octet-stream")},
                timeout=20,
            )
    except Exception as err:
        st.warning(f"Telegram error: {err}")

# ---------- Email copy to client ----------
if send_copy:
    host, user, pwd = os.getenv("SMTP_HOST"), os.getenv("SMTP_USER"), os.getenv("SMTP_PASS")
    port = int(os.getenv("SMTP_PORT", "587"))
    if all([host, user, pwd]):
        body = textwrap.dedent(
            f"""Hello {name},

Thank you for your request. Summary:

"
            f"Brand / Model / Gen: {brand} / {model} / {gen}
"
            f"Fuel: {fuel}
Engine: {engine}
Stage: {stage}
"
            f"Options: {', '.join(opts_selected) if opts_selected else '-'}
VIN: {vin}

"
            f"Message: {message}

Best regards, Level of Speed team"""
        )
        msg = email.message.EmailMessage()
        msg["Subject"] = "Level of Speed Configurator – Your Request"
        msg["From"] = user
        msg["To"] = email_addr
        msg.set_content(body)
        if attach_pdf:
            pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", size=12)
            for ln in body.split("
"):
                pdf.multi_cell(0, 10, ln)
            msg.add_attachment(pdf.output(dest="S").encode("latin-1"), maintype="application", subtype="pdf", filename="LoS_report.pdf")
        try:
            with smtplib.SMTP(host, port) as s:
                s.starttls(); s.login(user, pwd); s.send_message(msg)
        except Exception as smtp_err:
            st.warning(f"Email error: {smtp_err}")
    else:
        st.info("Send-copy checked, but SMTP credentials are missing.")

st.success(_t["success"])
