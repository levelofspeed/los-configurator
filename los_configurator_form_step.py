
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import tempfile
import os

st.set_page_config(page_title="Level of Speed Configurator", layout="wide")

# Переводы
translations = {
    "en": {
        "title": "Level of Speed Configurator",
        "select_brand": "Select Brand",
        "select_model": "Select Model",
        "select_generation": "Select Generation",
        "select_engine": "Select Engine",
        "performance": "Performance Overview",
        "power": "Power (HP)",
        "torque": "Torque (Nm)",
        "options": "Available Options",
        "form_title": "Request Your Tuning Offer",
        "name": "Your Name",
        "email": "Your Email",
        "vin": "VIN Number (optional)",
        "message": "Comment",
        "send_copy": "Send me PDF to my email",
        "submit": "Send Request"
    }
}

col1, col2, col3 = st.columns([6, 1, 1])
with col3:
    lang = st.selectbox("Language", ["en"], index=0)
t = translations[lang]

st.markdown(f"<h1 style='text-align: center;'>{t['title']}</h1>", unsafe_allow_html=True)

@st.cache_data
def load_data():
    return pd.read_excel("configurator_template_fixed.xlsx")

df = load_data()

brand = st.selectbox(t["select_brand"], [""] + sorted(df["Brand"].dropna().unique()))
if brand:
    df_brand = df[df["Brand"] == brand]
    model = st.selectbox(t["select_model"], [""] + sorted(df_brand["Model"].dropna().unique()))
    if model:
        df_model = df_brand[df_brand["Model"] == model]
        generation = st.selectbox(t["select_generation"], [""] + sorted(df_model["Generation"].dropna().unique()))
        if generation:
            df_gen = df_model[df_model["Generation"] == generation]
            engine = st.selectbox(t["select_engine"], [""] + sorted(df_gen["Engine"].dropna().unique()))
            if engine:
                selected = df_gen[df_gen["Engine"] == engine].iloc[0]

                # Графики
                hp_stock = int(selected["HP Original"])
                hp_tuned = int(selected["HP Tuned"])
                nm_stock = int(selected["Nm Original"])
                nm_tuned = int(selected["Nm Tuned"])
                hp_diff = hp_tuned - hp_stock
                nm_diff = nm_tuned - nm_stock
                y_max = max(hp_tuned, nm_tuned) * 1.15

                plt.style.use('dark_background')
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5), facecolor='black')
                fig.patch.set_facecolor('black')

                ax1.bar(['Stock', 'LoS Chiptuning'], [hp_stock, hp_tuned], color=['gray', 'red'])
                ax1.set_title(t["power"], color='white')
                ax1.set_ylim(0, y_max)
                ax1.set_facecolor('black')
                ax1.tick_params(colors='white')
                ax1.text(0, hp_stock + 10, f'{hp_stock} hp', ha='center', color='white')
                ax1.text(1, hp_tuned + 10, f'{hp_tuned} hp', ha='center', color='red')
                ax1.text(0.5, -0.28, f'Difference: +{hp_diff} hp', ha='center',
                         fontweight='bold', color='white', transform=ax1.transAxes)

                ax2.bar(['Stock', 'LoS Chiptuning'], [nm_stock, nm_tuned], color=['gray', 'red'])
                ax2.set_title(t["torque"], color='white')
                ax2.set_ylim(0, y_max)
                ax2.set_facecolor('black')
                ax2.tick_params(colors='white')
                ax2.text(0, nm_stock + 10, f'{nm_stock} Nm', ha='center', color='white')
                ax2.text(1, nm_tuned + 10, f'{nm_tuned} Nm', ha='center', color='red')
                ax2.text(0.5, -0.28, f'Difference: +{nm_diff} Nm', ha='center',
                         fontweight='bold', color='white', transform=ax2.transAxes)

                for ax in [ax1, ax2]:
                    for spine in ax.spines.values():
                        spine.set_visible(False)

                st.pyplot(fig)

                if "Options" in selected and pd.notna(selected["Options"]):
                    st.markdown(f"### {t['options']}")
                    st.markdown(f"{selected['Options']}")

                st.markdown("----")
                st.markdown(f"### {t['form_title']}")
                with st.form("contact_form"):
                    name = st.text_input(t["name"])
                    email = st.text_input(t["email"])
                    vin = st.text_input(t["vin"])
                    message = st.text_area(t["message"])
                    send_pdf = st.checkbox(t["send_copy"])
                    submitted = st.form_submit_button(t["submit"])

                    if submitted:
                        st.success("✅ Your request has been submitted successfully.")
