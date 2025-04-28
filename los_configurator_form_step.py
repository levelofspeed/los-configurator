import streamlit as st
import matplotlib.pyplot as plt
import os
import json

# Debug mode
DEBUG = True

def log(message):
    if DEBUG:
        st.write(f"DEBUG: {message}")

# Page config
st.set_page_config(page_title="Level of Speed Configurator", layout="wide")

# Initialize session state
if 'debug_info' not in st.session_state:
    st.session_state.debug_info = []

# Multilanguage support (упрощенная версия)
language = 'en'  # Фиксируем язык для теста

# Load database
@st.cache_data
def load_db():
    db_path = os.path.join(os.getcwd(), 'data', 'full_database.json')
    with open(db_path, encoding='utf-8') as f:
        return json.load(f)

try:
    database = load_db()
    log("Database loaded successfully")
except Exception as e:
    st.error(f"Error loading database: {str(e)}")
    st.stop()

# Selection steps
try:
    st.header("Vehicle Selection")
    
    brands = [''] + list(database.keys())
    brand = st.selectbox("Select Brand", brands, key='brand')
    log(f"Selected brand: {brand}")
    
    if not brand:
        st.stop()
    
    models = [''] + list(database[brand].keys())
    model = st.selectbox("Select Model", models, key='model')
    log(f"Selected model: {model}")
    
    if not model:
        st.stop()
    
    generations = [''] + list(database[brand][model].keys())
    generation = st.selectbox("Select Generation", generations, key='generation')
    log(f"Selected generation: {generation}")
    
    if not generation:
        st.stop()
    
    engines_data = database[brand][model][generation]
    fuels = sorted({d.get('Type') for d in engines_data.values() if isinstance(d, dict)})
    fuel = st.selectbox("Select Fuel", [''] + fuels, key='fuel')
    log(f"Selected fuel: {fuel}")
    
    if not fuel:
        st.stop()
    
    engines = [name for name, d in engines_data.items() 
               if isinstance(d, dict) and d.get('Type') == fuel]
    engine = st.selectbox("Select Engine", [''] + engines, key='engine')
    log(f"Selected engine: {engine}")
    
    if not engine:
        st.stop()

    # Упрощенный выбор stage
    stage = st.selectbox("Select Tuning Stage", 
                        ["Power Only", "Options Only", "Full Package"], 
                        key='stage')
    log(f"Selected stage: {stage}")

    # Options selection
    if stage != "Power Only":
        options = engines_data[engine].get('Options', [])
        selected_options = st.multiselect("Select Options", options, key='options')
        log(f"Selected options: {selected_options}")

    # Display debug info
    if DEBUG:
        with st.expander("Debug Info"):
            st.write(st.session_state.debug_info)

    # Charts
    st.header("Performance Chart")
    try:
        rec = engines_data[engine]
        orig_hp, tuned_hp = rec['Original HP'], rec['Tuned HP']
        orig_tq, tuned_tq = rec['Original Torque'], rec['Tuned Torque']
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # HP plot
        ax1.bar(['Stock', 'Tuned'], [orig_hp, tuned_hp], color=['gray', 'red'])
        ax1.set_title("Horsepower")
        
        # Torque plot
        ax2.bar(['Stock', 'Tuned'], [orig_tq, tuned_tq], color=['gray', 'red'])
        ax2.set_title("Torque")
        
        st.pyplot(fig)
        plt.close(fig)
        log("Chart rendered successfully")
        
    except Exception as e:
        st.error(f"Error generating chart: {str(e)}")
        log(f"Chart error: {str(e)}")

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    log(f"Critical error: {str(e)}")
