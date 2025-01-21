from config import db
from models import User

def delete_user(user_id):
    try:
        # Находим пользователя по ID
        user = User.query.get(user_id)
        
        if user is None:
            print(f'Пользователь с ID {user_id} не найден')
            return False
            
        # Удаляем пользователя
        db.session.delete(user)
        db.session.commit()
        print(f'Пользователь с ID {user_id} успешно удален')
        return True
        
    except Exception as e:
        db.session.rollback()
        print('Ошибка при удалении пользователя:', str(e))
        return False

if __name__ == '__main__':
    user_id = int(input('Введите ID пользователя: '))
    delete_user(user_id)