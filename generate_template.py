import pandas as pd
import json
import os

# Получаем текущий каталог скрипта для корректных относительных путей
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Путь к единому файлу JSON с полной базой
DATA_FILE = os.path.join(BASE_DIR, 'data', 'full_database.json')
# Путь к шаблону Excel (output)
OUTPUT_FILE = os.path.join(BASE_DIR, 'configurator_template_fixed.xlsx')

# 1) Читаем полный JSON
with open(DATA_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 2) Расплющиваем вложенную структуру в таблицу
rows = []
for brand, models in data.items():
    for model_name, gens in models.items():
        for generation, engines in gens.items():
            for engine_label, specs in engines.items():
                if specs:
                    rows.append({
                        'Brand': brand,
                        'Model': model_name,
                        'Generation': generation,
                        'Fuel': specs.get('Type', ''),
                        'Engine': engine_label,
                        'Original HP': specs.get('Original HP', ''),
                        'Tuned HP': specs.get('Tuned HP', ''),
                        'Original Torque': specs.get('Original Torque', ''),
                        'Tuned Torque': specs.get('Tuned Torque', ''),
                        'Options': ';'.join(specs.get('Options', []))
                    })

# 3) Преобразуем в DataFrame и сохраняем в Excel
df = pd.DataFrame(rows)
# Если нужно, можно отсортировать
# df.sort_values(['Brand', 'Model', 'Generation', 'Engine'], inplace=True)

df.to_excel(OUTPUT_FILE, index=False)
print(f"✔️ Шаблон сгенерирован: {OUTPUT_FILE}")
