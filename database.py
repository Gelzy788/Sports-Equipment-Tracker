from config import db, app
from models import User, Storage, Equipment, Requests, Purchases
from werkzeug.security import generate_password_hash
import os
from datetime import datetime

def add_user(email, password, username, is_admin=False):
    # Хэшируем пароль перед сохранением с использованием sha256
    hashed_password = generate_password_hash(password, method='sha256')
    new_user = User(email=email, password=hashed_password, username=username, admin=is_admin)
    try:
        db.session.add(new_user)
        db.session.commit()
        return new_user
    except Exception as err:
        print("User error: ", err)
        return None

def update_profile_picture(user_id, profile_picture):
    user = User.query.get(user_id)
    if user:
        # Удаляем старое фото профиля, если оно существует
        if user.profile_picture and user.profile_picture != 'default.jpg':
            old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], user.profile_picture)
            if os.path.exists(old_image_path):
                os.remove(old_image_path)

        user.profile_picture = profile_picture
        try:
            db.session.commit()
        except Exception as err:
            print("Error updating profile picture: ", err)

def init_database():
    # Создаем все таблицы
    with app.app_context():
        db.drop_all()  # Удаляем старые таблицы
        db.create_all()  # Создаем новые таблицы
        
        # Добавляем тестовое оборудование
        equipment_list = [
            {'name': 'Футбольный мяч', 'count': 10},
            {'name': 'Баскетбольный мяч', 'count': 8},
            {'name': 'Волейбольный мяч', 'count': 6},
            {'name': 'Теннисная ракетка', 'count': 4},
            {'name': 'Скакалка', 'count': 15}
        ]
        
        for eq in equipment_list:
            storage_item = Storage(name=eq['name'], count=eq['count'])
            db.session.add(storage_item)
        
        db.session.commit()
        
        # Создаем тестового администратора
        admin = add_user(
            email='admin@mail.ru',
            password='12345',
            username='admin',
            is_admin=True
        )
        
        # Создаем тестового пользователя
        user = add_user(
            email='user@mail.ru',
            password='12345',
            username='user',
            is_admin=False
        )
        
        
        
        db.session.commit()
        print("База данных успешно инициализирована!")

if __name__ == "__main__":
    init_database()
