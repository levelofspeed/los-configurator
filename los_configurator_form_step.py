import streamlit as st
import matplotlib.pyplot as plt
import json
import os

# Debug setup
st.set_page_config(page_title="DEBUG - LoS Configurator")
st.sidebar.title("Debug Panel")
DEBUG = st.sidebar.checkbox("Enable debug", True)

def log(message):
    if DEBUG:
        st.session_state.debug_info.append(message)
        st.sidebar.code(f"Last event: {message}")

# Initialize session state
if 'debug_info' not in st.session_state:
    st.session_state.debug_info = []
if 'engine_data' not in st.session_state:
    st.session_state.engine_data = None

# Load database
@st.cache_data
def load_db():
    try:
        db_path = os.path.join('data', 'full_database.json')
        with open(db_path, encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log(f"DB load error: {str(e)}")
        st.error("Database loading failed")
        st.stop()

database = load_db()

# Vehicle selection - simplified
st.header("1. Vehicle Selection")

brand = st.selectbox("Brand", [''] + list(database.keys()), key='brand')
if not brand: st.stop()

model = st.selectbox("Model", [''] + list(database[brand].keys()), key='model')
if not model: st.stop()

generation = st.selectbox("Generation", [''] + list(database[brand][model].keys()), key='generation')
if not generation: st.stop()

engines_data = database[brand][model][generation]
fuel_types = sorted({e.get('Type') for e in engines_data.values() if isinstance(e, dict)})
fuel = st.selectbox("Fuel", [''] + fuel_types, key='fuel')
if not fuel: st.stop()

engines = [k for k, v in engines_data.items() if isinstance(v, dict) and v.get('Type') == fuel]
engine = st.selectbox("Engine", [''] + engines, key='engine')
if not engine: st.stop()

# Critical section - Tuning Stage
st.header("2. Tuning Configuration")
log(f"Pre-stage selection. Engine: {engine}")

# IMPORTANT: We'll try 3 different approaches one by one
approach = st.radio("Select rendering approach", 
                   ["Original", "Session State", "Static Options"], 
                   index=0)

if approach == "Original":
    # Original problematic version
    stage = st.selectbox("Tuning Stage", 
                        ["Power Only", "Options Only", "Full Package"],
                        key='stage_original')
    
elif approach == "Session State":
    # Version with session state tracking
    if 'tuning_stage' not in st.session_state:
        st.session_state.tuning_stage = "Power Only"
    
    new_stage = st.selectbox("Tuning Stage", 
                           ["Power Only", "Options Only", "Full Package"],
                           index=["Power Only", "Options Only", "Full Package"].index(st.session_state.tuning_stage),
                           key='stage_session')
    
    if new_stage != st.session_state.tuning_stage:
        log(f"Stage changed from {st.session_state.tuning_stage} to {new_stage}")
        st.session_state.tuning_stage = new_stage
    
    stage = st.session_state.tuning_stage

else:
    # Static options with reset
    stage = st.selectbox("Tuning Stage", 
                        ["Power Only", "Options Only", "Full Package"],
                        key='stage_static')

log(f"Selected stage: {stage}")

# Options selection - with protection
if stage != "Power Only":
    try:
        available_options = engines_data[engine].get('Options', [])
        selected_options = st.multiselect("Available Options", 
                                        available_options,
                                        key='engine_options')
        log(f"Selected options: {selected_options}")
    except Exception as e:
        st.error(f"Options loading error: {str(e)}")
        log(f"Options error: {str(e)}")

# Display debug info
if DEBUG:
    st.sidebar.subheader("Session State")
    st.sidebar.json(st.session_state)
    
    st.subheader("Debug Log")
    for msg in st.session_state.debug_info[-10:]:
        st.code(msg)

# Simple chart
try:
    st.header("Performance Chart")
    engine_spec = engines_data[engine]
    
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(['Stock HP', 'Tuned HP'], 
           [engine_spec['Original HP'], engine_spec['Tuned HP']], 
           color=['gray', 'red'])
    st.pyplot(fig)
    plt.close(fig)
    log("Chart rendered successfully")
    
except Exception as e:
    st.error(f"Chart error: {str(e)}")
    log(f"Chart failed: {str(e)}")
