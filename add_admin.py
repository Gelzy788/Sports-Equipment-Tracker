from config import db
from models import User
from werkzeug.security import generate_password_hash

def create_admin():
    # Создаем админа с указанными данными
    admin = User(
        username='admin',
        email='admin@mail.ru',
        password=generate_password_hash('12345', method='sha256'),
        admin=True
    )
    
    try:
        db.session.add(admin)
        db.session.commit()
        print('Администратор успешно создан!')
    except Exception as e:
        db.session.rollback()
        print('Ошибка при создании администратора:', str(e))

if __name__ == '__main__':
    create_admin()
