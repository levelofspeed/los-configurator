
import streamlit as st

# Установка конфигурации страницы (должна быть первой)
st.set_page_config(page_title="Level of Speed Configurator", layout="wide")

# Имитация языков для селектора
languages = ["en", "de", "ru"]

# Создаём три колонки, помещаем селектор в крайнюю правую
col1, col2, col3 = st.columns([6, 1, 1])
with col3:
    selected_language = st.selectbox("Language / Sprache / Язык", languages)

# Заголовок страницы
st.markdown("<h1 style='text-align: center;'>Level of Speed Configurator</h1>", unsafe_allow_html=True)

# Пример остального содержимого (можно заменить на реальный конфигуратор)
st.write(f"Выбранный язык: {selected_language}")
