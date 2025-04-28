import streamlit as st
import matplotlib.pyplot as plt
import json
import os
import traceback
from datetime import datetime

# 1. Настройка состояния приложения ============================================
if 'app' not in st.session_state:
    st.session_state.app = {
        'stage': 1,  # 1=выбор авто, 2=тюнинг, 3=результаты
        'vehicle': None,
        'tuning': None,
        'last_error': None
    }

# 2. Загрузка данных с защитой ================================================
@st.cache_data
def load_database():
    try:
        with open('data/full_database.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.session_state.app['last_error'] = {
            'time': datetime.now().strftime("%H:%M:%S"),
            'error': str(e),
            'trace': traceback.format_exc()
        }
        return None

database = load_database()

# 3. Визуализация ошибок ======================================================
def show_errors():
    if st.session_state.app['last_error']:
        err = st.session_state.app['last_error']
        with st.expander("❌ Ошибка (нажмите для деталей)", expanded=False):
            st.error(f"**Время:** {err['time']}")
            st.code(f"Ошибка: {err['error']}\n\n{err['trace']}")
        if st.button("🔄 Попробовать снова"):
            st.session_state.app['last_error'] = None
            st.rerun()

# 4. Шаг 1: Выбор автомобиля ==================================================
def render_vehicle_selection():
    st.header("🔧 Выбор автомобиля")
    
    try:
        # Защита от отсутствия данных
        if not database:
            st.error("База данных не загружена")
            return

        cols = st.columns(3)
        
        # Выбор марки
        with cols[0]:
            brands = sorted(database.keys())
            brand = st.selectbox("Марка", [''] + brands, key='brand')
        
        # Выбор модели
        with cols[1]:
            models = []
            if brand:
                models = sorted(database[brand].keys())
            model = st.selectbox("Модель", [''] + models, key='model')
        
        # Выбор поколения
        with cols[2]:
            generations = []
            if brand and model:
                generations = sorted(database[brand][model].keys())
            generation = st.selectbox("Поколение", [''] + generations, key='generation')
        
        # Дополнительные параметры
        if brand and model and generation:
            engines_data = database[brand][model][generation]
            
            # Выбор топлива
            fuels = sorted({e.get('Type') for e in engines_data.values() 
                          if isinstance(e, dict)})
            fuel = st.selectbox("Топливо", [''] + fuels, key='fuel')
            
            # Выбор двигателя
            if fuel:
                engines = [k for k, v in engines_data.items() 
                         if isinstance(v, dict) and v.get('Type') == fuel]
                engine = st.selectbox("Двигатель", [''] + engines, key='engine')
                
                # Сохранение выбора
                if engine:
                    st.session_state.app['vehicle'] = {
                        'brand': brand,
                        'model': model,
                        'generation': generation,
                        'fuel': fuel,
                        'engine': engine,
                        'specs': engines_data[engine]
                    }
        
        # Кнопка продолжения
        if st.session_state.app['vehicle']:
            if st.button("Далее →", key='to_step_2'):
                st.session_state.app['stage'] = 2
                st.rerun()

    except Exception as e:
        st.session_state.app['last_error'] = {
            'time': datetime.now().strftime("%H:%M:%S"),
            'error': str(e),
            'trace': traceback.format_exc()
        }
        st.rerun()

# 5. Шаг 2: Настройка тюнинга =================================================
def render_tuning_config():
    st.header("⚡ Настройка тюнинга")
    
    try:
        vehicle = st.session_state.app['vehicle']
        st.success(f"Выбран: {vehicle['brand']} {vehicle['model']} ({vehicle['engine']})")
        
        # Выбор типа тюнинга
        tuning_type = st.radio(
            "Тип тюнинга",
            ["Только мощность", "Только опции", "Полный пакет"],
            index=0,
            key='tuning_type'
        )
        
        # Выбор опций
        selected_options = []
        if "опции" in tuning_type.lower():
            options = vehicle['specs'].get('Options', [])
            selected_options = st.multiselect(
                "Доступные опции",
                options,
                key='tuning_options'
            )
        
        # Сохранение выбора
        st.session_state.app['tuning'] = {
            'type': tuning_type,
            'options': selected_options
        }
        
        # Управление навигацией
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Назад", key='back_to_step_1'):
                st.session_state.app['stage'] = 1
                st.rerun()
        with col2:
            if st.button("Далее →", key='to_step_3'):
                st.session_state.app['stage'] = 3
                st.rerun()

    except Exception as e:
        st.session_state.app['last_error'] = {
            'time': datetime.now().strftime("%H:%M:%S"),
            'error': str(e),
            'trace': traceback.format_exc()
        }
        st.rerun()

# 6. Шаг 3: Результаты ========================================================
def render_results():
    st.header("📊 Результаты")
    
    try:
        vehicle = st.session_state.app['vehicle']
        tuning = st.session_state.app['tuning']
        
        # Отображение графиков
        fig, ax = plt.subplots(figsize=(10, 5))
        specs = vehicle['specs']
        
        ax.bar(
            ['Сток', 'Тюнинг'],
            [specs['Original HP'], specs['Tuned HP']],
            color=['gray', 'red']
        )
        ax.set_ylabel('Мощность (л.с.)')
        st.pyplot(fig)
        plt.close(fig)
        
        # Информация о выборе
        st.write(f"**Тип тюнинга:** {tuning['type']}")
        if tuning['options']:
            st.write("**Выбранные опции:**")
            for opt in tuning['options']:
                st.write(f"- {opt}")
        
        # Кнопка сброса
        if st.button("🔄 Начать заново", key='restart'):
            st.session_state.app = {
                'stage': 1,
                'vehicle': None,
                'tuning': None,
                'last_error': None
            }
            st.rerun()

    except Exception as e:
        st.session_state.app['last_error'] = {
            'time': datetime.now().strftime("%H:%M:%S"),
            'error': str(e),
            'trace': traceback.format_exc()
        }
        st.rerun()

# 7. Главный контроллер ========================================================
def main():
    show_errors()
    
    if not database:
        st.error("Не удалось загрузить базу данных")
        return
    
    if st.session_state.app['stage'] == 1:
        render_vehicle_selection()
    elif st.session_state.app['stage'] == 2:
        render_tuning_config()
    elif st.session_state.app['stage'] == 3:
        render_results()

if __name__ == "__main__":
    main()
