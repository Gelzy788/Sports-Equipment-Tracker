from config import db, app
from models import User, Equipment, Storage, Requests, Purchases
from database import add_user

# Создаем контекст приложения
with app.app_context():
    # Удаляем все существующие таблицы
    db.drop_all()
    
    # Создаем все таблицы заново
    db.create_all()
    
    # Добавляем администратора
    add_user('admin@example.com', 'admin123', 'admin')
    
    # Делаем коммит изменений
    db.session.commit()
