import streamlit as st
import matplotlib.pyplot as plt
import os
import json
import requests
import io
import tempfile
from fpdf import FPDF

# Настройка страницы
st.set_page_config(page_title="Level of Speed Configurator", layout="wide")

# Мультиязычная поддержка
languages = {"en": "English", "ru": "Русский", "de": "Deutsch"}
translations = {
    "en": {
        "select_language": "Select Language",
        "title": "Level of Speed Configurator",
        "select_brand": "Select Brand",
        "select_model": "Select Model",
        "select_generation": "Select Generation",
        "select_fuel": "Select Fuel",
        "select_engine": "Select Engine",
        "select_stage": "Select Stage",
        "options": "Options",
        "form_title": "Contact Us",
        "name": "Name",
        "email": "Email",
        "vin": "VIN",
        "message": "Message",
        "send_copy": "Send me a copy",
        "attach_pdf": "Attach PDF",
        "upload_file": "Attach file",
        "submit": "Submit",
        "error_name": "Please enter your name.",
        "error_email": "Please enter a valid email.",
        "error_select_options": "Please select at least one option for full package.",
        "stage_power": "Power Increase Only",
        "stage_options_only": "Options Only",
        "stage_full": "Full Package",
        "difference_hp": "+{hp} hp",
        "difference_torque": "+{torque} Nm",
        "original_hp": "Original / Tuned HP",
        "original_torque": "Original / Tuned Torque",
        "no_data": "No data available for this selection.",
        "success_message": "Thank you! Your request has been submitted."
    },
    "ru": {
        "select_language": "Выбор языка",
        "title": "Конфигуратор Level of Speed",
        "select_brand": "Выберите марку",
        "select_model": "Выберите модель",
        "select_generation": "Выберите поколение",
        "select_fuel": "Выберите топливо",
        "select_engine": "Выберите двигатель",
        "select_stage": "Выберите стейдж",
        "options": "Опции",
        "form_title": "Контактная форма",
        "name": "Имя",
        "email": "Email",
        "vin": "VIN",
        "message": "Сообщение",
        "send_copy": "Отправить копию мне",
        "attach_pdf": "Прикрепить PDF",
        "upload_file": "Прикрепить файл",
        "submit": "Отправить",
        "error_name": "Пожалуйста, введите имя.",
        "error_email": "Пожалуйста, введите корректный Email.",
        "error_select_options": "Пожалуйста, выберите хотя бы одну опцию для полного пакета.",
        "stage_power": "Только мощность",
        "stage_options_only": "Только опции",
        "stage_full": "Полный пакет",
        "difference_hp": "+{hp} л.с.",
        "difference_torque": "+{torque} Нм",
        "original_hp": "Оригинал / Тюнинг л.с.",
        "original_torque": "Оригинал / Тюнинг Нм",
        "no_data": "Нет данных для выбранной конфигурации.",
        "success_message": "Спасибо! Ваша заявка отправлена."
    },
    "de": {
        "select_language": "Sprache wählen",
        "title": "Level of Speed Konfigurator",
        "select_brand": "Marke wählen",
        "select_model": "Modell wählen",
        "select_generation": "Generation wählen",
        "select_fuel": "Kraftstoff wählen",
        "select_engine": "Motor wählen",
        "select_stage": "Stufe wählen",
        "options": "Optionen",
        "form_title": "Kontaktformular",
        "name": "Name",
        "email": "E-Mail",
        "vin": "VIN",
        "message": "Nachricht",
        "send_copy": "Kopie an mich senden",
        "attach_pdf": "PDF-Bericht anhängen",
        "upload_file": "Datei anhängen",
        "submit": "Senden",
        "error_name": "Bitte geben Sie Ihren Namen ein.",
        "error_email": "Bitte geben Sie eine gültige E-Mail-Adresse ein.",
        "error_select_options": "Bitte wählen Sie mindestens eine Option für das vollständige Paket.",
        "stage_power": "Nur Leistung",
        "stage_options_only": "Nur Optionen",
        "stage_full": "Komplettpaket",
        "difference_hp": "+{hp} PS",
        "difference_torque": "+{torque} Nm",
        "original_hp": "Original / Getunte PS",
        "original_torque": "Original / Getunter Nm",
        "no_data": "Für diese Konfiguration sind keine Daten verfügbar.",
        "success_message": "Vielen Dank! Ihre Anfrage wurde gesendet."
    }
}
# Список языков для селектора
dirs = list(languages.keys())

# Верхняя панель: логотип, переключатель языка и заголовок
logo_cols = st.columns([1, 2, 1])
with logo_cols[1]:
    logo_path = os.path.join(os.path.dirname(__file__), 'logo.png')
    if os.path.exists(logo_path):
        st.image(logo_path, use_column_width=True)

# Выбор языка и заголовок приложения
top_cols = st.columns([8, 1])
with top_cols[1]:
    language = st.selectbox(
        label='',
        options=dirs,
        index=dirs.index('en'),  # English default
        format_func=lambda code: languages[code],
        key='language',
        label_visibility='collapsed'
    )
with top_cols[0]:
    st.title(translations[language]['title'])

# Основной словарь переводов для текущего языка
t = translations[language]

# Загрузка базы данных
@st.cache_data
def load_database():
    path = os.path.join(os.path.dirname(__file__), 'data', 'full_database.json')
    if not os.path.exists(path):
        st.error(f"Database file not found: {path}")
        st.stop()
    with open(path, encoding='utf-8') as f:
        return json.load(f)

database = load_database()

# Этапы выбора
brand = st.selectbox(t['select_brand'], [''] + list(database.keys()), key='brand')
if not brand:
    st.stop()
model = st.selectbox(t['select_model'], [''] + list(database[brand].keys()), key='model')
if not model:
    st.stop()
generation = st.selectbox(t['select_generation'], [''] + list(database[brand][model].keys()), key='generation')
if not generation:
    st.stop()

# Выбор топлива
engines_data = database[brand][model][generation]
fuels = sorted({d['Type'] for d in engines_data.values() if isinstance(d, dict)})
fuel = st.selectbox(t['select_fuel'], [''] + fuels, key='fuel')
if not fuel:
    st.stop()

# Выбор двигателя по топливу
filtered_engines = [name for name, d in engines_data.items() if isinstance(d, dict) and d['Type'] == fuel]
engine = st.selectbox(t['select_engine'], [''] + filtered_engines, key='engine')
if not engine:
    st.stop()

# Стейдж и опции
stage = st.selectbox(t['select_stage'], [t['stage_power'], t['stage_options_only'], t['stage_full']], key='stage')
selected_options = []
if stage != t['stage_power']:
    st.markdown('----')
    selected_options = st.multiselect(t['options'], engines_data[engine]['Options'], key='options')

# Отступ перед графиками
st.write('')

# Построение графиков с едиными осями
rec = engines_data[engine]
orig_hp, tuned_hp = rec['Original HP'], rec['Tuned HP']
orig_tq, tuned_tq = rec['Original Torque'], rec['Tuned Torque']
y_max = max(orig_hp, tuned_hp, orig_tq, tuned_tq) * 1.2
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), facecolor='black')
bars = ['Stock', 'LoS Chiptuning']
colors = ['#A0A0A0', '#FF0000']
# HP
ax1.set_facecolor('black')
ax1.bar(bars, [orig_hp, tuned_hp], color=colors)
ax1.set_ylim(0, y_max)
for i, v in enumerate([orig_hp, tuned_hp]):
    ax1.text(i, v*1.02, f"{v} hp", ha='center', color='white')
ax1.text(0.5, -0.15, t['difference_hp'].format(hp=tuned_hp-orig_hp), transform=ax1.transAxes, ha='center', color='white')
ax1.set_ylabel(t['original_hp'], color='white')
ax1.tick_params(colors='white')
# Torque
ax2.set_facecolor('black')
ax2.bar(bars, [orig_tq, tuned_tq], color=colors)
ax2.set_ylim(0, y_max)
for i, v in enumerate([orig_tq, tuned_tq]):
    ax2.text(i, v*1.02, f"{v} Nm", ha='center', color='white')
ax2.text(0.5, -0.15, t['difference_torque'].format(torque=tuned_tq-orig_tq), transform=ax2.transAxes, ha='center', color='white')
ax2.set_ylabel(t['original_torque'], color='white')
ax2.tick_params(colors='white')
plt.tight_layout()
st.pyplot(fig)
plt.close(fig)

# Форма
st.markdown('----')
st.markdown(f"### {t['form_title']}")
with st.form('contact_form'):
    name = st.text_input(t['name'], key='name')
    email = st.text_input(t['email'], key='email')
    vin = st.text_input(t['vin'], key='vin')
    message = st.text_area(t['message'], key='message')
    send_copy = st.checkbox(t['send_copy'], key='send_copy')
    attach_pdf = st.checkbox(t['attach_pdf'], key='attach_pdf')
    uploaded_file = st.file_uploader(t['upload_file'], key='upload_file')
    submitted = st.form_submit_button(t['submit'])

if submitted:
    if not name: st.error(t['error_name']); st.stop()
    if not email or '@' not in email: st.error(t['error_email']); st.stop()
    if stage == t['stage_full'] and not selected_options: st.error(t['error_select_options']); st.stop()
    opts = ', '.join(selected_options) if selected_options else 'N/A'
    msg_text = f"""📩 New LoS Config Request
Brand: {brand}
Model: {model}
Generation: {generation}
Engine: {engine}
Stage: {stage}
Options: {opts}
Name: {name}
Email: {email}
VIN: {vin}
Message: {message}"""
    # Telegram
    try:
        bot, chat = st.secrets['telegram']['token'], st.secrets['telegram']['chat_id']
        requests.post(f"https://api.telegram.org/bot{bot}/sendMessage", data={"chat_id": chat, "text": msg_text})
        if uploaded_file:
            requests.post(f"https://api.telegram.org/bot{bot}/sendDocument", data={"chat_id": chat}, files={"document": (uploaded_file.name, uploaded_file.getvalue())})
    except Exception as e:
        st.warning(f"Telegram error: {e}")
    # Email
    if send_copy:
        try:
            from email.message import EmailMessage
            import smtplib
            smtp_conf = st.secrets['smtp']
            email_msg = EmailMessage()
            email_msg['Subject'] = 'Your LoS Config Copy'
            email_msg['From'] = smtp_conf['sender_email']
            email_msg['To'] = email
            email_msg.set_content(msg_text)
            if attach_pdf:
                buf = io.BytesIO()
                fig.savefig(buf, format='PNG')
                buf.seek(0)
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.png'); tmp.write(buf.getvalue()); tmp.close()
                pdf = FPDF(); pdf.add_page(); pdf.image(tmp.name, x=10, y=10, w=190); os.remove(tmp.name)
                pdf_bytes = pdf.output(dest='S').encode('latin-1')
                email_msg.add_attachment(pdf_bytes, maintype='application', subtype='pdf', filename='LoS_Report.pdf')
            with smtplib.SMTP_SSL(smtp_conf['server'], smtp_conf['port']) as server:
                server.login(smtp_conf['username'], smtp_conf['password'])
                server.send_message(email_msg)
        except Exception as ee:
            st.warning(f"Email error: {ee}")
        # Скачать PDF
    if attach_pdf:
        buf = io.BytesIO()
        fig.savefig(buf, format='PNG')
        buf.seek(0)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        tmp.write(buf.getvalue())
        tmp.close()
        pdf = FPDF(); pdf.add_page(); pdf.image(tmp.name, x=10, y=10, w=190)
        os.remove(tmp.name)
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        st.download_button(
            t['attach_pdf'],
            data=pdf_bytes,
            file_name="LoS_Report.pdf",
            mime="application/pdf"
        )
    # Успешное завершение
    st.success(t['success_message'])
