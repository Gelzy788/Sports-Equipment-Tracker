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

# Настраиваем подключение к SQLite базе данных
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + DB_PATH
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Настройки для загрузки файлов
UPLOAD_FOLDER = os.path.join(basedir, 'static', 'profile_images')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Создаем папку для загрузки, если её нет
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Инициализируем объекты БД и менеджера авторизации
db = SQLAlchemy(app)
login_manager = LoginManager()
