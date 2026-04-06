import os
import csv
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename

# 1. Инициализация приложения (ВАЖНО: выше всех роутов)
app = Flask(__name__)

# 2. Конфигурация
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SECRET_KEY'] = 'dev_key_123'

# Убедимся, что папка для картинок существует
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])


# --- 3. Вспомогательные функции для CSV (Критерий: Хранение данных) ---

def save_to_csv(title, img_path):
    """Записывает новую строку в файл data.csv"""
    with open('data.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([title, img_path])


def load_from_csv():
    """Читает все данные из data.csv и возвращает список словарей"""
    properties = []
    if os.path.exists('data.csv'):
        with open('data.csv', 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) == 2:  # Проверка, что в строке есть и название, и путь
                    properties.append({'title': row[0], 'image': row[1]})
    return properties


# --- 4. Роуты (Страницы) ---

@app.route('/')
def index():
    # Загружаем список жилья из файла
    houses = load_from_csv()
    return render_template('index.html', houses=houses)


@app.route('/add', methods=['GET', 'POST'])
def add_property():
    if request.method == 'POST':
        title = request.form.get('title')
        file = request.files.get('file')

        if file and title:
            # Безопасно сохраняем файл (Критерий: Загрузка файлов)
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Формируем путь для отображения на сайте
            img_url = url_for('static', filename='uploads/' + filename)

            # Сохраняем в CSV
            save_to_csv(title, img_url)

            return redirect(url_for('index'))

    return render_template('add.html')


# 5. Запуск сервера
if __name__ == '__main__':
    app.run(debug=True)