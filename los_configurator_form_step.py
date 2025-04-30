import streamlit as st
import matplotlib.pyplot as plt
import os, json, io, textwrap, requests, smtplib, email.message, tempfile
from collections import UserDict
from fpdf import FPDF

# ---------------- Page Config -----------------
st.set_page_config(page_title="Level of Speed Configurator", layout="wide")

# ---------------- Translations ----------------
languages = {"en": "English", "ru": "Русский", "de": "Deutsch"}
translations = {
    "en": {
        "select_brand": "Select Brand", "select_model": "Select Model", "select_generation": "Select Generation", "select_fuel": "Select Fuel",
        "select_engine": "Select Engine", "select_stage": "Select Stage",
        "stage_power": "Power only", "stage_options_only": "Options only", "stage_full": "Full package",
        "options": "Options", "form_title": "Contact Us",
        "name": "Name", "email": "Email", "vin": "VIN", "message": "Message",
        "send_copy": "Send me a copy", "attach_pdf": "Attach PDF report",
        "upload_file": "Attach file", "submit": "Submit", "success": "Thank you! We will contact you soon.",
        "error_name": "Please enter your name", "error_email": "Please enter a valid email",
        "error_select_options": "Select at least one option", "difference": "Difference",
        "chart_note": (
            "Please note that all displayed values of power and torque gains "
            "are approximate and may vary depending on many factors, including "
            "fuel quality and the current condition of the vehicle. Level of "
            "Speed recommends taking these into account when evaluating results. "
            "By confirming receipt of the report, you agree that you have read this information."
        )
    },
    "ru": {
        "select_brand": "Выберите марку", "select_model": "Выберите модель", "select_generation": "Выберите поколение", "select_fuel": "Выберите топливо",
        "select_engine": "Выберите двигатель", "select_stage": "Выберите Stage",
        "stage_power": "Только мощность", "stage_options_only": "Только опции", "stage_full": "Полный пакет",
        "options": "Опции", "form_title": "Свяжитесь с нами",
        "name": "Имя", "email": "Email", "vin": "VIN", "message": "Сообщение",
        "send_copy": "Прислать копию", "attach_pdf": "Приложить PDF отчёт",
        "upload_file": "Прикрепить файл", "submit": "Отправить", "success": "Спасибо! Мы скоро свяжемся.",
        "error_name": "Введите имя", "error_email": "Введите корректный email",
        "error_select_options": "Выберите хотя бы одну опцию", "difference": "Разница",
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
        "select_brand": "Marke wählen", "select_model": "Modell wählen", "select_generation": "Generation wählen", "select_fuel": "Kraftstoff wählen",
        "select_engine": "Motor wählen", "select_stage": "Stage wählen",
        "stage_power": "Nur Leistung", "stage_options_only": "Nur Optionen", "stage_full": "Komplettpaket",
        "options": "Optionen", "form_title": "Kontakt",
        "name": "Name", "email": "E-Mail", "vin": "VIN", "message": "Nachricht",
        "send_copy": "Kopie an mich senden", "attach_pdf": "PDF Bericht anhängen",
        "upload_file": "Datei anhängen", "submit": "Senden", "success": "Danke! Wir melden uns bald.",
        "error_name": "Bitte Namen eingeben", "error_email": "Bitte gültige E-Mail eingeben",
        "error_select_options": "Wählen Sie mindestens eine Option", "difference": "Differenz",
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
    def __missing__(self, key): return key

# ---------------- Header ----------------------
_, col_lang = st.columns([10, 2])
with col_lang:
    lang = st.selectbox("", list(languages.keys()), format_func=lambda x: languages[x], label_visibility="collapsed")
_t = _T(translations.get(lang, translations["en"]))

# ---------------- Logo ------------------------
logo = next((p for p in ("logo.png","logo_white.png") if os.path.exists(p)), None)
if logo:
    _, c, _ = st.columns([1, 4, 1])
    c.image(logo, width=200)

# ---------------- Page Title ----------------
st.title("Level of Speed Configurator 🚘")

# ---------------- Load DB ---------------------
@st.cache_data
def load_db():
    with open(os.path.join("data","full_database.json"), encoding="utf-8") as f:
        return json.load(f)

def prune(node):
    return {k: prune(v) for k,v in node.items() if v not in (None,{},[],"")} if isinstance(node,dict) else node

db = prune(load_db())
clear = lambda *keys: [st.session_state.pop(k,None) for k in keys]

# ---------------- Selection flow --------------
brand = st.selectbox(_t["select_brand"], [""]+sorted(db.keys()), key="brand", on_change=lambda: clear("model","generation","fuel","engine","stage","options"))
if not brand: st.stop()
model=st.selectbox(_t["select_model"],[""]+sorted(db[brand].keys()), key="model", on_change=lambda: clear("generation","fuel","engine","stage","options"))
if not model: st.stop()
gen=st.selectbox(_t["select_generation"],[""]+sorted(db[brand][model].keys()), key="generation", on_change=lambda: clear("fuel","engine","stage","options"))
if not gen: st.stop()
engines_data = db[brand][model][gen]
fuels = sorted({d.get("Type") for d in engines_data.values() if isinstance(d,dict) and d})
fuel=st.selectbox(_t["select_fuel"],[""]+fuels, key="fuel", on_change=lambda: clear("engine","stage","options"))
if not fuel: st.stop()
engines=[n for n,d in engines_data.items() if isinstance(d,dict) and d.get("Type")==fuel]
engine=st.selectbox(_t["select_engine"],[""]+engines, key="engine", on_change=lambda: clear("stage","options"))
if not engine: st.stop()
stage=st.selectbox(_t["select_stage"],[_t["stage_power"],_t["stage_options_only"],_t["stage_full"]], key="stage")
opts=st.multiselect(_t["options"], engines_data[engine].get("Options", [])) if stage in (_t["stage_full"],_t["stage_options_only"]) else []

st.markdown("---")

# ---------------- Chart -----------------------
chart_bytes=None
try:
    rec=engines_data[engine]; oh,th,ot,tt = rec["Original HP"], rec["Tuned HP"], rec["Original Torque"], rec["Tuned Torque"]
    ymax=max(oh,th,ot,tt)*1.2
    fig,(ax1,ax2) = plt.subplots(1,2, figsize=(10,4), facecolor="black")
    for ax in (ax1,ax2):
        ax.set_facecolor("black"); ax.tick_params(colors="white"); [spine.set_color("white") for spine in ax.spines.values()]
    ax1.bar(["Stock","LoS"],[oh,th],color=["#777777","#E11D48"])
    ax2.bar(["Stock","LoS"],[ot,tt],color=["#777777","#E11D48"])
    ax1.set_ylim(0,ymax); ax2.set_ylim(0,ymax)
    for i,v in enumerate([oh,th]): ax1.text(i, v*1.02, f"{v} hp", ha="center", color="white")
    for i,v in enumerate([ot,tt]): ax2.text(i, v*1.02, f"{v} Nm", ha="center", color="white")
    ax1.text(0.5, -0.15, f"{_t['difference']} +{th-oh} hp", transform=ax1.transAxes, ha="center", color="white")
    ax2.text(0.5, -0.15, f"{_t['difference']} +{tt-ot} Nm", transform=ax2.transAxes, ha="center", color="white")
    ax1.set_title("HP", color="white"); ax2.set_title("Torque", color="white")
    plt.tight_layout(); st.pyplot(fig)
    # ---------------- Chart Note ----------------
    st.markdown(f"> *{_t['chart_note']}*")
    buf=io.BytesIO(); fig.savefig(buf, format="png", dpi=150); buf.seek(0); chart_bytes=buf.getvalue(); plt.close(fig)
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
if not name: st.error(_t["error_name"]); st.stop()
if "@" not in email_addr: st.error(_t["error_email"]); st.stop()

# ---------------- Telegram --------------------
telegram_cfg = st.secrets.get("telegram", {}) if hasattr(st, 'secrets') else {}
TOKEN = telegram_cfg.get("token") or os.getenv("TG_BOT_TOKEN")
CHAT = telegram_cfg.get("chat_id") or os.getenv("TG_CHAT_ID")
if TOKEN and CHAT:
    txt = textwrap.dedent(f"""
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
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT, "text": txt}, timeout=10)
        if uploaded_file:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendDocument", data={"chat_id": CHAT}, files={"document": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type or "application/octet-stream")}, timeout=20)
    except Exception as e:
        st.warning(f"Telegram error: {e}")

# ---------------- Email -----------------------
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
    msg["Subject"] = "Your LOS Configuration Report"
    smtp_cfg = st.secrets.get("smtp", {})
    host = smtp_cfg.get("server")
    port = int(smtp_cfg.get("port", 587))
    user = smtp_cfg.get("username")
    pwd = smtp_cfg.get("password")
    sender = smtp_cfg.get("sender_email", user)
    msg["From"] = sender; msg["To"] = email_addr
    msg.set_content(selection_text)
    pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", size=12)
    for line in selection_text.strip().split("\n"):
        safe = line.encode('latin-1','ignore').decode('latin-1')
        pdf.cell(0, 8, txt=safe, ln=True)
    pdf.ln(4)
    # ---------------- PDF Chart Note ----------------
    note_text = _t["chart_note"]
    for note_line in note_text.strip().split("
"):
        safe_note = note_line.encode('latin-1','ignore').decode('latin-1')
        pdf.cell(0, 8, txt=safe_note, ln=True)
    pdf.ln(4)
    if chart_bytes:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
            tmp_img.write(chart_bytes); tmp_img.flush()
            pdf.image(tmp_img.name, x=10, y=pdf.get_y(), w=pdf.w-20)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
        pdf.output(tmp_pdf.name); tmp_pdf.seek(0)
        msg.add_attachment(tmp_pdf.read(), maintype="application", subtype="pdf", filename="report.pdf")
    try:
        if port == 465:
            server = smtplib.SMTP_SSL(host, port)
        else:
            server = smtplib.SMTP(host, port); server.ehlo(); server.starttls(); server.ehlo()
        server.login(user, pwd); server.send_message(msg); server.quit()
    except Exception as e:
        st.warning(f"Email error: {e}")

# ---------------- Completion ----------------
st.success(_t["success"])
st.stop()
