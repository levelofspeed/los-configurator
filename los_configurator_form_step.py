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
translations = {
    "en": { ... },
    "ru": { ... },
    "de": { ... }
}

# Logo
cols = st.columns([1, 8, 1])
with cols[1]:
    logo = os.path.join(os.getcwd(), "logo.png")
    if os.path.exists(logo):
        try:
            st.image(logo, use_container_width=True)
        except TypeError:
            st.image(logo, use_column_width=True)

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
    st.title(translations[lang_code]['title'])(translations[lang_code]['title'])

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
if not brand: st.stop()
model = st.selectbox(t['select_model'], [''] + list(db[brand].keys()), key='model')
if not model: st.stop()
gen = st.selectbox(t['select_generation'], [''] + list(db[brand][model].keys()), key='generation')
if not gen: st.stop()

engines = db[brand][model][gen]
fuels = sorted(set(v['Type'] for v in engines.values()))
fuel = st.selectbox(t['select_fuel'], [''] + fuels, key='fuel')
if not fuel: st.stop()
list_eng = [k for k,v in engines.items() if v['Type']==fuel]
engine = st.selectbox(t['select_engine'], [''] + list_eng, key='engine')
if not engine: st.stop()
stage = st.selectbox(t['select_stage'], [t['stage_power'], t['stage_options_only'], t['stage_full']], key='stage')

opts = []
if stage != t['stage_power']:
    st.markdown('----')
    opts = st.multiselect(t['options'], engines[engine]['Options'], key='options')

# Charts
rec = engines[engine]
orig_hp, tuned_hp = rec['Original HP'], rec['Tuned HP']
orig_tq, tuned_tq = rec['Original Torque'], rec['Tuned Torque']
ymax = max(orig_hp, tuned_hp, orig_tq, tuned_tq) * 1.2
fig, (ax1, ax2) = plt.subplots(1,2,figsize=(12,5), facecolor='black')
fig.patch.set_facecolor('black')
for ax, vals, lbl_key, diff_key in [
    (ax1, [orig_hp, tuned_hp], 'original_hp', 'difference_hp'),
    (ax2, [orig_tq, tuned_tq], 'original_torque', 'difference_torque')]:
    ax.set_facecolor('black')
    ax.bar(['Stock','LoS'], vals, color=['#A0A0A0','#FF0000'])
    ax.set_ylim(0, ymax)
    for i,v in enumerate(vals):
        ax.text(i, v*1.02, f"{v}{' hp' if lbl_key=='original_hp' else ' Nm'}", ha='center', color='white')
    ax.text(0.5, -0.15, t[diff_key].format(hp=tuned_hp-orig_hp, torque=tuned_tq-orig_tq), transform=ax.transAxes, ha='center', color='white')
    ax.set_ylabel(t[lbl_key], color='white')
    ax.tick_params(colors='white')
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
    st.success("✅ Форма отправлена (минимальный режим)")
