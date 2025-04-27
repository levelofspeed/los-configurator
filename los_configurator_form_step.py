import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
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
        "select_fuel": "Select Fuel Type",
        "fuel_petrol": "Petrol",
        "fuel_diesel": "Diesel",
        "select_engine": "Select Engine",
        "select_stage": "Select Stage",
        "stage_power": "Power Increase Only",
        "stage_options_only": "Options Only",
        "stage_full": "Full Package",
        "original_hp": "Original HP",
        "tuned_hp": "Tuned HP",
        "original_torque": "Original Torque",
        "tuned_torque": "Tuned Torque",
        "options": "Options",
        "no_data": "No data available for selected combination.",
        "difference_hp": "Difference: +{hp} hp",
        "difference_torque": "Difference: +{torque} Nm",
        "form_title": "Contact Form",
        "name": "Name",
        "email": "Email",
        "vin": "VIN",
        "message": "Message",
        "upload_file": "Attach File",
        "send_copy": "Send me a copy",
        "attach_pdf": "PDF report",
        "submit": "Submit",
        "success_message": "✅ Your request has been submitted successfully.",
        "error_name": "Please enter your name.",
        "error_email": "Please enter a valid email."
    },
    "ru": {
        "select_language": "Выберите язык",
        "title": "Level of Speed Configurator",
        "select_brand": "Выберите марку",
        "select_model": "Выберите модель",
        "select_generation": "Выберите поколение",
        "select_fuel": "Выберите тип топлива",
        "fuel_petrol": "Бензин",
        "fuel_diesel": "Дизель",
        "select_engine": "Выберите двигатель",
        "select_stage": "Выберите этап",
        "stage_power": "Только увеличение мощности",
        "stage_options_only": "Только параметры",
        "stage_full": "Полный пакет",
        "original_hp": "Исходная мощность",
        "tuned_hp": "Тюнинговая мощность",
        "original_torque": "Исходный крутящий момент",
        "tuned_torque": "Тюнинговый крутящий момент",
        "options": "Параметры",
        "no_data": "Для выбранной комбинации нет данных.",
        "difference_hp": "Разница: +{hp} л.с.",
        "difference_torque": "Разница: +{torque} Н·м",
        "form_title": "Контактная форма",
        "name": "Имя",
        "email": "Эл. почта",
        "vin": "VIN",
        "message": "Сообщение",
        "upload_file": "Прикрепить файл",
        "send_copy": "Отправить копию себе",
        "attach_pdf": "Отчет в PDF",
        "submit": "Отправить",
        "success_message": "✅ Ваш запрос был успешно отправлен.",
        "error_name": "Пожалуйста, введите ваше имя.",
        "error_email": "Пожалуйста, введите корректную почту."
    },
    "de": {
        "select_language": "Sprache auswählen",
        "title": "Level of Speed Configurator",
        "select_brand": "Marke auswählen",
        "select_model": "Modell auswählen",
        "select_generation": "Generation auswählen",
        "select_fuel": "Kraftstoff auswählen",
        "fuel_petrol": "Benzin",
        "fuel_diesel": "Diesel",
        "select_engine": "Motor auswählen",
        "select_stage": "Stufe auswählen",
        "stage_power": "Nur Leistungssteigerung",
        "stage_options_only": "Nur Optionen",
        "stage_full": "Vollständiges Paket",
        "original_hp": "Originalleistung",
        "tuned_hp": "Leistung nach Tuning",
        "original_torque": "Originaldrehmoment",
        "tuned_torque": "Drehmoment nach Tuning",
        "options": "Optionen",
        "no_data": "Für die gewählte Kombination sind keine Daten verfügbar.",
        "difference_hp": "Differenz: +{hp} PS",
        "difference_torque": "Differenz: +{torque} Nm",
        "form_title": "Kontaktformular",
        "name": "Name",
        "email": "E-Mail",
        "vin": "VIN",
        "message": "Nachricht",
        "upload_file": "Datei anhängen",
        "send_copy": "Kopie an mich senden",
        "attach_pdf": "PDF-Bericht",
        "submit": "Absenden",
        "success_message": "✅ Ihre Anfrage wurde erfolgreich abgeschickt.",
        "error_name": "Bitte geben Sie Ihren Namen ein.",
        "error_email": "Bitte geben Sie eine gültige E-Mail ein."
    }
}

# Выбор языка
col1, col2, col3 = st.columns([6,1,1])
with col3:
    lang = st.selectbox(
        translations['en']['select_language'],
        list(languages.keys()),
        format_func=lambda code: languages[code]
    )
if not lang:
    st.stop()
t = translations[lang]

# Заголовок
st.markdown(f"<h1 style='text-align:center;color:white'>{t['title']}</h1>", unsafe_allow_html=True)

# Загрузка данных
df = pd.read_excel("configurator_template_fixed.xlsx")
# Используем единый лист как источник тюнинга
df_tune = df.copy()

# Селекторы
brand = st.selectbox(t['select_brand'], [""] + sorted(df_tune['Brand'].unique()))
if not brand: st.stop()
model = st.selectbox(t['select_model'], [""] + sorted(df_tune[df_tune['Brand']==brand]['Model'].unique()))
if not model: st.stop()
generation = st.selectbox(t['select_generation'], [""] + sorted(df_tune[(df_tune['Brand']==brand)&(df_tune['Model']==model)]['Generation'].unique()))
if not generation: st.stop()

# Селектор топлива
fuel = st.selectbox(
    t['select_fuel'], [""] + ['Petrol','Diesel'],
    format_func=lambda x: '' if x=='' else (t['fuel_petrol'] if x=='Petrol' else t['fuel_diesel'])
)
if not fuel: st.stop()

# Селектор двигателя
available_engines = df_tune[
    (df_tune['Brand']==brand)&
    (df_tune['Model']==model)&
    (df_tune['Generation']==generation)&
    (df_tune['Fuel']==fuel)
]['Engine'].dropna().unique().tolist()
engine = st.selectbox(t['select_engine'], [""] + sorted(available_engines))
if not engine: st.stop()

# Селектор этапа
stage = st.selectbox(
    t['select_stage'],
    [t['stage_power'], t['stage_options_only'], t['stage_full']]
)

# Поиск записи
rec = df_tune[
    (df_tune['Brand']==brand)&
    (df_tune['Model']==model)&
    (df_tune['Generation']==generation)&
    (df_tune['Fuel']==fuel)&
    (df_tune['Engine']==engine)
].iloc[0]
orig_hp, tuned_hp = rec['Original HP'], rec['Tuned HP']
orig_tq, tuned_tq = rec['Original Torque'], rec['Tuned Torque']
options = [o.strip() for o in str(rec['Options']).split(';') if o.strip()]

# Построение графиков
# Единый предел оси Y
max_val = max(orig_hp, tuned_hp, orig_tq, tuned_tq) * 1.2
fig, (ax1, ax2) = plt.subplots(1,2,figsize=(12,5), facecolor='black')
for ax in (ax1, ax2): ax.set_facecolor('black')
bars = ['Stock','LoS Chiptuning']
# Мощность
ax1.bar(bars, [orig_hp,tuned_hp], color=['#A0A0A0','#FF0000']); ax1.set_ylim(0, max_val)
for i, v in enumerate([orig_hp, tuned_hp]): ax1.text(i, v*1.02, f"{v} hp", ha='center', color='white')
ax1.text(0.5,-0.15,t['difference_hp'].format(hp=tuned_hp-orig_hp),transform=ax1.transAxes,ha='center',color='white',fontsize=14)
ax1.set_ylabel(f"{t['original_hp']} / {t['tuned_hp']}", color='white'); ax1.tick_params(colors='white')
# Крутящий момент
ax2.bar(bars, [orig_tq,tuned_tq], color=['#A0A0A0','#FF0000']); ax2.set_ylim(0, max_val)
for i, v in enumerate([orig_tq, tuned_tq]): ax2.text(i, v*1.02, f"{v} Nm", ha='center', color='white')
ax2.text(0.5,-0.15,t['difference_torque'].format(torque=tuned_tq-orig_tq),transform=ax2.transAxes,ha='center',color='white',fontsize=14)
ax2.set_ylabel(f"{t['original_torque']} / {t['tuned_torque']}", color='white'); ax2.tick_params(colors='white')
plt.tight_layout(); st.pyplot(fig)

# Опции
if stage != t['stage_power']:
    st.markdown('----'); sel_opts = st.multiselect(t['options'], options)
else:
    sel_opts = []

# Форма
st.markdown('----'); st.markdown(f"### {t['form_title']}")
with st.form('contact_form'):
    name = st.text_input(t['name']); email = st.text_input(t['email']); vin = st.text_input(t['vin'])
    message = st.text_area(t['message']); upl = st.file_uploader(t['upload_file'])
    c1,c2 = st.columns(2); send = c1.checkbox(t['send_copy']); pdf = c2.checkbox(t['attach_pdf'])
    submit = st.form_submit_button(t['submit'])
if submit:
    if not name: st.error(t['error_name'])
    elif not email or '@' not in email: st.error(t['error_email'])
    else:
        token, cid = st.secrets['telegram']['token'], st.secrets['telegram']['chat_id']
        msg = f"📩 New LoS Config Request\nName: {name}\nEmail: {email}\nVIN: {vin}\nBrand: {brand}\nModel: {model}\nGeneration: {generation}\nFuel: {fuel}\nEngine: {engine}\nStage: {stage}\nOptions: {', '.join(sel_opts) or 'N/A'}\nMessage: {message}"
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id':cid,'text':msg})
        if upl: requests.post(f"https://api.telegram.org/bot{token}/sendDocument",data={'chat_id':cid},files={'document':(upl.name,upl.getvalue())})
        if send:
            import smtplib
            from email.message import EmailMessage
            conf = st.secrets['smtp']; email_msg = EmailMessage()
            email_msg['Subject'] = 'Your LoS Configurator Request'; email_msg['From'] = conf['sender_email']; email_msg['To'] = email
            email_msg.set_content(msg)
            if pdf:
                buf = io.BytesIO(); fig.savefig(buf, format='PNG'); buf.seek(0)
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.png'); tmp.write(buf.getvalue()); tmp.close()
                fpdf = FPDF(); fpdf.add_page(); fpdf.image(tmp.name, 10,10,190); os.remove(tmp.name)
                pdf_data = fpdf.output(dest='S').encode('latin-1'); email_msg.add_attachment(pdf_data, maintype='application', subtype='pdf', filename='report.pdf')
            with smtplib.SMTP_SSL(conf['server'], conf['port']) as smtp: smtp.login(conf['username'], conf['password']); smtp.send_message(email_msg)
            st.success(t['success_message'])
