import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Создаем экземпляр приложения
app = Flask(__name__)

# Настраиваем секретный ключ
app.config['SECRET_KEY'] = 'hardsecretkey'

# Получаем абсолютный путь к директории проекта
basedir = os.path.abspath(os.path.dirname(__file__))

# Путь к существующей базе данных
DB_PATH = os.path.join(basedir, 'database.db')

# Проверяем существование базы данных
if not os.path.exists(DB_PATH):
    raise FileNotFoundError(
        'База данных не найдена. Убедитесь, что файл database.db существует в корневой директории проекта.'
    )

# Настраиваем подключение к существующей SQLite базе данных
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + DB_PATH
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Настраиваем папку для загрузки файлов
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'profile_images')

# Создаем папку для загрузки файлов, если она не существует
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Разрешенные расширения файлов
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Инициализируем объекты БД и менеджера авторизации
db = SQLAlchemy(app)
login_manager = LoginManager()
