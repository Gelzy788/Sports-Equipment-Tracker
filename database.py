from config import db, app
from models import User
import os

from config import db
from models import User
from werkzeug.security import generate_password_hash


def add_user(email, password, username):
    # Хэшируем пароль перед сохранением
    hashed_password = generate_password_hash(password)
    new_user = User(email=email, password=hashed_password, username=username)
    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception as err:
        print("User error: ", err)


def delete_user(email, password, username):
    user = User(email=email, password=password, username=username)

    try:
        db.session.delete(user)
        db.session.commit()
    except Exception as err:
        print("User error: ", err)


def update_profile_picture(user_id, profile_picture):
    user = User.query.get(user_id)
    if user:
        # Удаляем старое фото профиля, если оно существует
        if user.profile_picture and user.profile_picture != 'default.png':
            old_image_path = os.path.join(
                app.config['UPLOAD_FOLDER'], user.profile_picture)
            if os.path.exists(old_image_path):
                os.remove(old_image_path)

        user.profile_picture = profile_picture
        try:
            db.session.commit()
        except Exception as err:
            print("Error updating profile picture: ", err)


if __name__ == "__main__":
    add_user('negm.ali@mail.ru', 'Azizalinegm111', 'Gelzy_')
