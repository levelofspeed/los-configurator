import streamlit as st
import matplotlib.pyplot as plt
import json
import os

# Настройка состояния
if 'app_initialized' not in st.session_state:
    st.session_state.app_initialized = True
    st.session_state.current_stage = "vehicle_selection"
    st.session_state.vehicle_data = {}
    st.session_state.tuning_config = {}
    st.session_state.debug_log = []

def log(message):
    st.session_state.debug_log.append(message)
    if st.sidebar.checkbox("Show debug log", False):
        st.sidebar.write(st.session_state.debug_log)

# Загрузка данных (без изменений)
@st.cache_data
def load_db():
    db_path = os.path.join('data', 'full_database.json')
    with open(db_path, encoding='utf-8') as f:
        return json.load(f)

database = load_db()

# Главный контроллер представлений
def render_app():
    if st.session_state.current_stage == "vehicle_selection":
        render_vehicle_selection()
    elif st.session_state.current_stage == "tuning_config":
        render_tuning_config()
    elif st.session_state.current_stage == "results":
        render_results()

# Шаг 1: Выбор автомобиля
def render_vehicle_selection():
    st.header("1. Выбор автомобиля")
    
    brands = [''] + list(database.keys())
    brand = st.selectbox("Марка", brands, index=0, key='brand_select')
    
    if brand:
        models = [''] + list(database[brand].keys())
        model = st.selectbox("Модель", models, index=0, key='model_select')
        
        if model:
            generations = [''] + list(database[brand][model].keys())
            generation = st.selectbox("Поколение", generations, index=0, key='generation_select')
            
            if generation:
                engines_data = database[brand][model][generation]
                fuel_types = sorted({e.get('Type') for e in engines_data.values() if isinstance(e, dict)})
                fuel = st.selectbox("Топливо", [''] + fuel_types, index=0, key='fuel_select')
                
                if fuel:
                    engines = [k for k, v in engines_data.items() if isinstance(v, dict) and v.get('Type') == fuel]
                    engine = st.selectbox("Двигатель", [''] + engines, index=0, key='engine_select')
                    
                    if engine:
                        st.session_state.vehicle_data = {
                            'brand': brand,
                            'model': model,
                            'generation': generation,
                            'fuel': fuel,
                            'engine': engine,
                            'specs': engines_data[engine]
                        }
                        
                        if st.button("Далее →"):
                            st.session_state.current_stage = "tuning_config"
                            st.rerun()

# Шаг 2: Настройка тюнинга
def render_tuning_config():
    st.header("2. Настройка тюнинга")
    st.write(f"Выбран двигатель: {st.session_state.vehicle_data['engine']}")
    
    # Жёстко фиксируем варианты выбора
    TUNING_STAGES = {
        "power": "Только мощность",
        "options": "Только опции", 
        "full": "Полный пакет"
    }
    
    # Используем session_state для хранения выбора
    if 'tuning_stage' not in st.session_state:
        st.session_state.tuning_stage = "power"
    
    # Радиокнопки вместо selectbox для стабильности
    new_stage = st.radio(
        "Тип тюнинга",
        options=list(TUNING_STAGES.keys()),
        format_func=lambda x: TUNING_STAGES[x],
        index=list(TUNING_STAGES.keys()).index(st.session_state.tuning_stage),
        key='stage_radio'
    )
    
    # Обновляем состояние только при изменении
    if new_stage != st.session_state.tuning_stage:
        st.session_state.tuning_stage = new_stage
        st.rerun()
    
    # Выбор опций (только для соответствующих пакетов)
    if st.session_state.tuning_stage in ["options", "full"]:
        available_options = st.session_state.vehicle_data['specs'].get('Options', [])
        
        if 'selected_options' not in st.session_state:
            st.session_state.selected_options = []
        
        st.session_state.selected_options = st.multiselect(
            "Доступные опции",
            available_options,
            default=st.session_state.selected_options,
            key='options_multiselect'
        )
    
    # Кнопки навигации
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Назад"):
            st.session_state.current_stage = "vehicle_selection"
            st.rerun()
    with col2:
        if st.button("Далее →"):
            st.session_state.current_stage = "results"
            st.rerun()

# Шаг 3: Результаты
def render_results():
    st.header("3. Результаты")
    
    # Простые графики без сложной логики
    try:
        specs = st.session_state.vehicle_data['specs']
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.bar(['Сток', 'Тюнинг'], [specs['Original HP'], specs['Tuned HP']], color=['gray', 'red'])
        ax.set_ylabel('Мощность (л.с.)')
        st.pyplot(fig)
        plt.close(fig)
    except Exception as e:
        st.error(f"Ошибка построения графиков: {str(e)}")
    
    if st.button("← Начать заново"):
        st.session_state.current_stage = "vehicle_selection"
        st.session_state.tuning_config = {}
        st.rerun()

# Запуск приложения
render_app()

# Отладочная информация
if st.sidebar.checkbox("Показать состояние"):
    st.sidebar.json(st.session_state)
