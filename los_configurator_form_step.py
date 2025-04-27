import streamlit as st

# Configure page
st.set_page_config(
    page_title="Level of Speed Configurator",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

import pandas as pd
import matplotlib.pyplot as plt

# Загрузка данных из Excel
@st.cache_data
def load_data():
    return pd.read_excel("configurator_template_fixed.xlsx")

df = load_data()

st.title("🔧 Level of Speed Configurator")

# Шаг 1: выбор бренда
brands = sorted(df['Brand'].unique())
brand = st.sidebar.selectbox("📋 Select Brand", [""] + brands)
if not brand:
    st.info("👉 Please select a Brand to continue")
else:
    # Шаг 2: выбор модели
    models = sorted(df[df['Brand'] == brand]['Model'].unique())
    model = st.sidebar.selectbox("📋 Select Model", [""] + models)
    if not model:
        st.info("👉 Please select a Model to continue")
    else:
        # Шаг 3: выбор поколения
        gens = df[(df['Brand'] == brand) & (df['Model'] == model)]
        generations = sorted(gens['Generation'].unique())
        generation = st.sidebar.selectbox("📋 Select Generation", [""] + generations)
        if not generation:
            st.info("👉 Please select a Generation to continue")
        else:
            # Шаг 4: выбор топлива
            fuels = sorted(gens[gens['Generation'] == generation]['Fuel'].unique())
            fuel = st.sidebar.selectbox("📋 Select Fuel", [""] + fuels)
            if not fuel:
                st.info("👉 Please select a Fuel to continue")
            else:
                # Шаг 5: выбор двигателя
                subset = gens[(gens['Generation'] == generation) & (gens['Fuel'] == fuel)]
                engines = sorted(subset['Engine'].unique())
                engine = st.sidebar.selectbox("📋 Select Engine", [""] + engines)
                if not engine:
                    st.info("👉 Please select an Engine to continue")
                else:
                    # Получение спецификаций
                    spec = subset[subset['Engine'] == engine].iloc[0]

                    st.subheader("🔍 Tuning Results")
                    # Таблица результатов
                    result_df = pd.DataFrame({
                        'Metric': ['HP', 'Torque'],
                        'Original': [spec['Original HP'], spec['Original Torque']],
                        'Tuned': [spec['Tuned HP'], spec['Tuned Torque']]
                    }).set_index('Metric')
                    st.table(result_df)

                    # Объединённый график прироста
                    st.subheader("📈 Performance Comparison")
                    st.bar_chart(result_df)

                    # Форма обратной связи для клиента
                    st.subheader("📨 Request a Callback")
                    with st.form(key='callback_form'):
                        customer_name = st.text_input("Your Name")
                        customer_email = st.text_input("Your Email")
                        submit_button = st.form_submit_button(label='Submit Request')
                    if submit_button:
                        # Здесь можно добавить отправку данных
                        st.success(f"Thank you, {customer_name}! We will contact you at {customer_email} soon.")
