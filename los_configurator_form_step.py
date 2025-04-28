import streamlit as st
import matplotlib.pyplot as plt
import json
import os
import traceback

# Базовые настройки
st.set_page_config(layout="wide")
st.title("Конфигуратор тюнинга (Устойчивая версия)")

# Инициализация состояния
if 'init' not in st.session_state:
    st.session_state.init = True
    st.session_state.stage = 1
    st.session_state.data_loaded = False
    st.session_state.vehicle = {}
    st.session_state.tuning = {'stage': None, 'options': []}

# Загрузка данных с защитой
@st.cache_data
def load_database():
    try:
        with open('data/full_database.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Ошибка загрузки базы данных: {str(e)}")
        st.stop()

# Показываем индикатор загрузки
with st.spinner('Загрузка базы данных...'):
    try:
        database = load_database()
        st.session_state.data_loaded = True
    except:
        st.error("Критическая ошибка при загрузке данных")
        st.stop()

# Шаг 1: Выбор автомобиля
if st.session_state.stage == 1 and st.session_state.data_loaded:
    st.header("Шаг 1: Выбор автомобиля")
    
    try:
        # Выбор марки
        brands = sorted(database.keys())
        brand = st.selectbox("Марка автомобиля", [''] + brands, key='brand_select')
        
        if brand:
            # Выбор модели
            models = sorted(database[brand].keys())
            model = st.selectbox("Модель", [''] + models, key='model_select')
            
            if model:
                # Выбор поколения
                generations = sorted(database[brand][model].keys())
                generation = st.selectbox("Поколение", [''] + generations, key='generation_select')
                
                if generation:
                    # Выбор топлива
                    engines_data = database[brand][model][generation]
                    fuels = sorted({e.get('Type') for e in engines_data.values() if isinstance(e, dict)})
                    fuel = st.selectbox("Топливо", [''] + fuels, key='fuel_select')
                    
                    if fuel:
                        # Выбор двигателя
                        engines = [k for k, v in engines_data.items() 
                                 if isinstance(v, dict) and v.get('Type') == fuel]
                        engine = st.selectbox("Двигатель", [''] + engines, key='engine_select')
                        
                        if engine:
                            st.session_state.vehicle = {
                                'brand': brand,
                                'model': model,
                                'generation': generation,
                                'fuel': fuel,
                                'engine': engine,
                                'specs': engines_data[engine]
                            }
                            
                            if st.button("Далее", key='to_step_2'):
                                st.session_state.stage = 2
                                st.rerun()

    except Exception as e:
        st.error(f"Ошибка при выборе автомобиля: {str(e)}")
        st.write(traceback.format_exc())

# Шаг 2: Выбор тюнинга
elif st.session_state.stage == 2:
    st.header("Шаг 2: Настройка тюнинга")
    st.write(f"Выбранный двигатель: {st.session_state.vehicle['engine']}")
    
    try:
        # Выбор типа тюнинга (радиокнопки для стабильности)
        TUNING_TYPES = {
            'power': 'Только мощность',
            'options': 'Только опции',
            'full': 'Полный пакет'
        }
        
        tuning_type = st.radio(
            "Тип тюнинга",
            options=list(TUNING_TYPES.keys()),
            format_func=lambda x: TUNING_TYPES[x],
            key='tuning_type_radio'
        )
        
        # Выбор опций (если нужно)
        if tuning_type in ['options', 'full']:
            available_options = st.session_state.vehicle['specs'].get('Options', [])
            selected_options = st.multiselect(
                "Доступные опции",
                options=available_options,
                default=st.session_state.tuning['options'],
                key='options_multiselect'
            )
        else:
            selected_options = []
        
        # Сохраняем настройки
        st.session_state.tuning = {
            'stage': tuning_type,
            'options': selected_options
        }
        
        # Кнопки навигации
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Назад", key='back_to_step_1'):
                st.session_state.stage = 1
                st.rerun()
        with col2:
            if st.button("Далее", key='to_step_3'):
                st.session_state.stage = 3
                st.rerun()
                
    except Exception as e:
        st.error(f"Ошибка при настройке тюнинга: {str(e)}")
        st.write(traceback.format_exc())

# Шаг 3: Результаты
elif st.session_state.stage == 3:
    st.header("Шаг 3: Результаты")
    
    try:
        # Простые и надежные графики
        specs = st.session_state.vehicle['specs']
        
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(['Сток', 'Тюнинг'], 
               [specs['Original HP'], specs['Tuned HP']], 
               color=['gray', 'red'])
        ax.set_ylabel('Мощность (л.с.)')
        st.pyplot(fig)
        plt.close(fig)
        
        # Информация о выборе
        st.write(f"**Тип тюнинга:** {st.session_state.tuning['stage']}")
        if st.session_state.tuning['options']:
            st.write("**Выбранные опции:**")
            for opt in st.session_state.tuning['options']:
                st.write(f"- {opt}")
        
        if st.button("Начать заново", key='restart'):
            st.session_state.stage = 1
            st.session_state.vehicle = {}
            st.session_state.tuning = {'stage': None, 'options': []}
            st.rerun()
            
    except Exception as e:
        st.error(f"Ошибка при отображении результатов: {str(e)}")
        st.write(traceback.format_exc())

# Отладочная информация
if st.sidebar.checkbox("Показать отладочную информацию"):
    st.sidebar.header("Состояние приложения")
    st.sidebar.write("Текущий этап:", st.session_state.stage)
    st.sidebar.json({
        "vehicle": st.session_state.vehicle,
        "tuning": st.session_state.tuning
    })
