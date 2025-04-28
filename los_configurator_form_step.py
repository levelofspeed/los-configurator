import streamlit as st
import os
import json
import matplotlib.pyplot as plt
import io
import requests
import tempfile
from fpdf import FPDF

# Page configuration
st.set_page_config(page_title="Level of Speed Configurator", layout="wide")

# Multilanguage support
directories = {"en": "English", "ru": "Русский", "de": "Deutsch"}
en = {
    "select_language": "Select language",
    "title": "Level of Speed Configurator",
    "select_brand": "Select Brand",
    "select_model": "Select Model",
    "select_generation": "Select Generation",
    "select_fuel": "Select Fuel Type",
    "select_engine": "Select Engine",
    "select_stage": "Select Stage",
    "stage_power": "Power Only",
    "stage_options_only": "Options Only",
    "stage_full": "Full Package",
    "options": "Select Options",
    "original_hp": "Engine Power (HP)",
    "difference_hp": "Gain: +{hp} HP",
    "original_torque": "Engine Torque (Nm)",
    "difference_torque": "Gain: +{torque} Nm",
    "form_title": "Contact Us",
    "name": "Your Name",
    "email": "Your Email",
    "vin": "VIN",
    "message": "Message",
    "upload_file": "Upload File",
    "send_copy": "Send me a copy",
    "attach_pdf": "Attach PDF Report",
    "submit": "Submit",
    "error_name": "Please enter your name",
    "error_email": "Please enter a valid email",
    "error_select_options": "Please select at least one option",
    "success_message": "Thank you! Your request has been sent."
}
translations = {"en": en, "ru": en, "de": en}

# Logo
top_cols = st.columns([1, 8, 1])
with top_cols[1]:
    logo_path = os.path.join(os.getcwd(), "logo.png")
    if os.path.exists(logo_path):
        try:
            st.image(logo_path, use_container_width=True)
        except TypeError:
            st.image(logo_path, use_column_width=True)

# Language selector and title
langs = ["en", "ru", "de"]
lang_cols = st.columns([8, 1])
with lang_cols[1]:
    lang_code = st.selectbox(
        translations['en']['select_language'],
        langs,
        index=langs.index('en'),
        format_func=lambda x: directories[x],
        key='language',
        label_visibility='collapsed'
    )
with lang_cols[0]:
    st.title(translations[lang_code]['title'])

t = translations[lang_code]

# Load database
@st.cache_data
def load_database():
    path = os.path.join(os.getcwd(), 'data', 'full_database.json')
    with open(path, encoding='utf-8') as f:
        return json.load(f)

db = load_database()

# Selections
brand = st.selectbox(t['select_brand'], [''] + list(db.keys()), key='brand')
if not brand:
    st.stop()
model = st.selectbox(t['select_model'], [''] + list(db[brand].keys()), key='model')
if not model:
    st.stop()
gen = st.selectbox(t['select_generation'], [''] + list(db[brand][model].keys()), key='generation')
if not gen:
    st.stop()

engines = db[brand][model][gen]
fuels = sorted(set(v['Type'] for v in engines.values()))
fuel = st.selectbox(t['select_fuel'], [''] + fuels, key='fuel')
if not fuel:
    st.stop()
list_engines = [k for k, v in engines.items() if v['Type'] == fuel]
engine = st.selectbox(t['select_engine'], [''] + list_engines, key='engine')
if not engine:
    st.stop()
stage = st.selectbox(
    t['select_stage'],
    [t['stage_power'], t['stage_options_only'], t['stage_full']],
    key='stage'
)

# Options selection
opts = []
if stage != t['stage_power']:
    st.markdown('----')
    opts = st.multiselect(t['options'], engines[engine]['Options'], key='options')

# Charts
rec = engines[engine]
orig_hp, tuned_hp = rec['Original HP'], rec['Tuned HP']
orig_tq, tuned_tq = rec['Original Torque'], rec['Tuned Torque']
ymax = max(orig_hp, tuned_hp, orig_tq, tuned_tq) * 1.2
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), facecolor='black')
fig.patch.set_facecolor('black')

# HP chart
ax1.set_facecolor('black')
ax1.bar(['Stock', 'LoS'], [orig_hp, tuned_hp], color=['#A0A0A0', '#FF0000'])
ax1.set_ylim(0, ymax)
for i, v in enumerate([orig_hp, tuned_hp]):
    ax1.text(i, v * 1.02, f"{v} hp", ha='center', color='white')
ax1.text(0.5, -0.15, t['difference_hp'].format(hp=tuned_hp - orig_hp), transform=ax1.transAxes, ha='center', color='white')
ax1.set_ylabel(t['original_hp'], color='white')
ax1.tick_params(colors='white')

# Torque chart
ax2.set_facecolor('black')
ax2.bar(['Stock', 'LoS'], [orig_tq, tuned_tq], color=['#A0A0A0', '#FF0000'])
ax2.set_ylim(0, ymax)
for i, v in enumerate([orig_tq, tuned_tq]):
    ax2.text(i, v * 1.02, f"{v} Nm", ha='center', color='white')
ax2.text(0.5, -0.15, t['difference_torque'].format(torque=tuned_tq - orig_tq), transform=ax2.transAxes, ha='center', color='white')
ax2.set_ylabel(t['original_torque'], color='white')
ax2.tick_params(colors='white')

plt.tight_layout()
st.pyplot(fig)

# Minimal contact form for debugging
st.markdown('----')
with st.form('contact'):
    name = st.text_input(t['name'], key='name')
    email = st.text_input(t['email'], key='email')
    submit = st.form_submit_button(t['submit'])

if submit:
    if not name:
        st.error(t['error_name'])
        st.stop()
    if not email or '@' not in email:
        st.error(t['error_email'])
        st.stop()
    st.success(t['success_message'])
