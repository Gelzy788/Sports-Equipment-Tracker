from config import db
from models import User
from werkzeug.security import generate_password_hash

def create_admin():
    admin = User(
        username=input('Введите имя: '),
        email=input('Введите email: '),
        password=generate_password_hash(input('Введите пароль: '), method='sha256'),
        admin=int(input('Введите цифру 0 либо 1, чтобы установить права администратора: '))
    )
    
    try:
        db.session.add(admin)
        db.session.commit()
        print('Пользователь успешно создан!')
    except Exception as e:
        db.session.rollback()
        print('Ошибка при создании администратора:', str(e))

if __name__ == '__main__':
    create_admin()
