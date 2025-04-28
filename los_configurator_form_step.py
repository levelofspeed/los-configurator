import streamlit as st
import json
from pathlib import Path

# 1. Настройка путей
BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "data" / "full_database.json"
LOGO_FILE = BASE_DIR / "static" / "logo_white.png"

# 2. Улучшенная загрузка данных с защитой
@st.cache_data
def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            
            # Фильтрация пустых значений
            filtered = {}
            for brand, models in data.items():
                if not models: continue
                filtered[brand] = {}
                for model, gens in models.items():
                    if not gens: continue
                    filtered[brand][model] = {}
                    for gen, engines in gens.items():
                        if not engines: continue
                        filtered[brand][model][gen] = {
                            engine: specs for engine, specs in engines.items() 
                            if specs and isinstance(specs, dict)
                        }
            return filtered
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {str(e)}")
        return {}

# 3. Главное приложение с полной защитой
def main():
    st.set_page_config(page_title="Level of Speed Configurator", layout="wide")
    
    # Логотип (с защитой)
    try:
        if LOGO_FILE.exists():
            st.image(str(LOGO_FILE), use_column_width=True)
    except Exception as e:
        st.warning(f"Не удалось загрузить логотип: {str(e)}")

    # Загрузка данных
    db = load_data()
    if not db:
        st.error("Нет данных для отображения. Проверьте файл базы данных.")
        st.stop()

    # Инициализация состояния
    if "stage" not in st.session_state:
        st.session_state.update({
            "stage": 1,
            "vehicle": None,
            "tuning": None
        })

    # Шаг 1: Выбор авто (с полной защитой)
    if st.session_state.stage == 1:
        st.header("🔧 Выбор автомобиля")
        
        try:
            # Выбор марки
            brands = sorted(db.keys())
            if not brands:
                st.error("Нет доступных марок")
                st.stop()
            
            brand = st.selectbox("Марка", brands, index=0)
            
            # Выбор модели
            models = sorted(db[brand].keys()) if brand else []
            if not models:
                st.error("Нет доступных моделей для выбранной марки")
                st.stop()
            
            model = st.selectbox("Модель", models, index=0)
            
            # Выбор поколения
            gens = sorted(db[brand][model].keys()) if model else []
            if not gens:
                st.error("Нет доступных поколений для выбранной модели")
                st.stop()
            
            gen = st.selectbox("Поколение", gens, index=0)
            
            # Выбор двигателя
            engines = sorted(db[brand][model][gen].keys()) if gen else []
            if not engines:
                st.error("Нет доступных двигателей для выбранного поколения")
                st.stop()
            
            engine = st.selectbox("Двигатель", engines, index=0)
            
            if engine and st.button("Далее →"):
                st.session_state.vehicle = {
                    "brand": brand,
                    "model": model,
                    "generation": gen,
                    "engine": engine,
                    "specs": db[brand][model][gen][engine]
                }
                st.session_state.stage = 2
                st.rerun()
                
        except Exception as e:
            st.error(f"Ошибка при выборе автомобиля: {str(e)}")
            st.stop()

    # Шаг 2: Настройка тюнинга
    elif st.session_state.stage == 2:
        try:
            v = st.session_state.vehicle
            st.header(f"⚡ {v['brand']} {v['model']} ({v['engine']})")
            
            # Выбор типа тюнинга
            tuning_type = st.radio(
                "Тип тюнинга",
                ["Только мощность", "Только опции", "Полный пакет"],
                index=0
            )
            
            # Выбор опций (если нужно)
            options = []
            if "опции" in tuning_type.lower():
                available_options = v["specs"].get("Options", [])
                if available_options:
                    options = st.multiselect("Доступные опции", available_options)
                else:
                    st.warning("Для этого двигателя нет доступных опций")
            
            # Навигация
            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Назад"):
                    st.session_state.stage = 1
                    st.rerun()
            with col2:
                if st.button("Далее →"):
                    st.session_state.tuning = {
                        "type": tuning_type,
                        "options": options
                    }
                    st.session_state.stage = 3
                    st.rerun()
                    
        except Exception as e:
            st.error(f"Ошибка при настройке тюнинга: {str(e)}")
            st.stop()

    # Шаг 3: Результаты
    elif st.session_state.stage == 3:
        try:
            v = st.session_state.vehicle
            t = st.session_state.tuning
            
            st.header("📊 Результаты конфигурации")
            st.subheader(f"{v['brand']} {v['model']} {v['generation']}")
            st.write(f"**Двигатель:** {v['engine']}")
            st.write(f"**Тип тюнинга:** {t['type']}")
            
            if t["options"]:
                st.write("**Выбранные опции:**")
                for opt in t["options"]:
                    st.write(f"- {opt}")
            else:
                st.write("**Выбранные опции:** Нет")
            
            st.divider()
            st.write(f"**Мощность:** {v['specs']['Original HP']} → {v['specs']['Tuned HP']} л.с.")
            st.write(f"**Крутящий момент:** {v['specs']['Original Torque']} → {v['specs']['Tuned Torque']} Нм")
            
            if st.button("🔄 Начать заново", type="primary"):
                st.session_state.clear()
                st.rerun()
                
        except Exception as e:
            st.error(f"Ошибка при отображении результатов: {str(e)}")
            st.stop()

if __name__ == "__main__":
    main()
