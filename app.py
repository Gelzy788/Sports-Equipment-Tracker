from flask import Flask, render_template, flash, request, redirect, url_for, jsonify
from flask_login import login_required, login_user, logout_user, current_user
from models import *
from config import app, login_manager, ALLOWED_EXTENSIONS
from database import add_user, update_profile_picture
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from user_app import user_bp
import os

# Проверяем наличие файла базы данных
if not os.path.exists('database.db'):
    print("База данных не найдена. Создаем новую базу данных...")
    from database import init_database
    init_database()
    print("База данных успешно создана!")

login_manager.init_app(app)
login_manager.login_view = 'login'

# Регистрируем Blueprint для пользовательских маршрутов
app.register_blueprint(user_bp, url_prefix='/user')

# Добавляем глобальную переменную для уведомлений
@app.context_processor
def inject_notifications():
    notifications_count = 0
    if current_user.is_authenticated:
        # Считаем количество необработанных заявок для пользователя
        notifications_count = Requests.query.filter_by(
            user_id=current_user.id,
            status=False
        ).count()
    return dict(notifications_count=notifications_count)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Войти в аккаунт
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Получите данные из формы
        email = request.form['email']
        password = request.form['password']

        # Найдите пользователя в базе данных
        user = User.query.filter_by(email=email).first()

        # Проверьте пароль
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Вы успешно вошли в систему!")
            return redirect(url_for("profile"))
        else:
            flash("Неправильный email или пароль.")

    return render_template("login.html")


# Регистрация пользователя
@app.route("/registration", methods=["GET", "POST"])
def registration():
    if request.method == "POST":
        # Получите данные из формы
        email = request.form['email']
        password = request.form['password']
        username = request.form['username']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Пользователь с таким email уже существует.")
            return redirect(url_for('registration'))

        add_user(email, password, username)
        return redirect(url_for('login'))

    return render_template('registration.html')


# Выйти из аккаунта
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Вы вышли из системы.")
    return redirect(url_for("get_data"))


# Загрузить изображение
@app.route('/upload', methods=['POST'])
@login_required
def upload_image():
    if 'file' not in request.files:
        flash('Нет файла для загрузки')
        return redirect(url_for('profile'))

    file = request.files['file']

    if file.filename == '':
        flash('Файл не выбран')
        return redirect(url_for('profile'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        current_user.profile_picture = filename
        db.session.commit()
        flash('Файл успешно загружен')
        return redirect(url_for('profile'))

    flash('Недопустимый файл')
    return redirect(url_for('profile'))


# страница профиля
@app.route("/profile")
@login_required
def profile():
    # Получите текущего пользователя
    user = current_user
    return render_template("profile.html", user=user)


# Главная страница
@app.route("/")
def get_data():
    return render_template('index.html')


# Страница инвентаря (склада)
@app.route("/storage", methods=['GET', 'POST'])
@login_required
def storage():
    if not current_user.admin:
        flash('Доступ запрещен')
        return redirect(url_for('index'))

    storage_items = Storage.query.all()
    users = User.query.filter_by(admin=False).all()

    if request.method == 'POST':
        if 'action' in request.form and request.form['action'] == 'give':
            # Логика выдачи инвентаря
            storage_id = request.form.get('storage_id')
            user_id = request.form.get('user_id')
            quantity = int(request.form.get('quantity'))

            storage_item = Storage.query.get(storage_id)
            user = User.query.get(user_id)

            if storage_item and user and storage_item.count >= quantity:
                storage_item.count -= quantity

                existing_equipment = Equipment.query.filter_by(
                    equipment_id=storage_item.id, user_id=user.id).first()

                if existing_equipment:
                    existing_equipment.count += quantity
                else:
                    new_equipment = Equipment(
                        equipment_id=storage_item.id, user_id=user.id, count=quantity)
                    db.session.add(new_equipment)

                db.session.commit()
                flash('Инвентарь успешно передан')
            else:
                flash('Ошибка при передаче инвентаря')

        elif 'action' in request.form and request.form['action'] == 'take_back':
            # Логика забирания инвентаря
            user_id = request.form.get('user_id')
            equipment_id = request.form.get('equipment_id')
            quantity = int(request.form.get('quantity'))

            user = User.query.get(user_id)
            equipment = Equipment.query.filter_by(
                user_id=user.id, equipment_id=equipment_id).first()

            if equipment and equipment.count >= quantity:
                equipment.count -= quantity
                if equipment.count == 0:
                    db.session.delete(equipment)

                # Добавляем количество на склад
                storage_item = Storage.query.get(equipment_id)
                if storage_item:
                    storage_item.count += quantity

                db.session.commit()
                flash('Инвентарь успешно забран у пользователя')
            else:
                flash('Ошибка: недостаточно инвентаря для забора')

    return render_template('storage.html', items=storage_items, users=users)


# Добавление нового предмета
@app.route("/storage/add", methods=['GET', 'POST'])
@login_required
def add_item():
    if not current_user.admin:
        flash("Доступ запрещен")
        return redirect(url_for('get_data'))

    if request.method == 'POST':
        name = request.form.get('name')
        count = request.form.get('count', type=int)

        if name and count is not None:
            # Проверяем, существует ли предмет
            existing_item = Storage.query.filter_by(name=name).first()
            if existing_item:
                # Если предмет существует, увеличиваем его количество
                existing_item.count += count
                flash(f'Количество предмета "{name}" увеличено на {count}')
            else:
                # Если предмет не существует, добавляем его как новый
                new_item = Storage(name=name, count=count)
                db.session.add(new_item)
                flash(f'Предмет "{name}" успешно добавлен')

            db.session.commit()
            return redirect(url_for('storage'))

    return render_template('add_item.html')


# Редактирование предмета
@app.route("/storage/edit/<int:item_id>", methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    if not current_user.admin:
        flash("Доступ запрещен")
        return redirect(url_for('get_data'))

    item = Storage.query.get_or_404(item_id)

    if request.method == 'POST':
        item.name = request.form.get('name')
        item.count = request.form.get('count', type=int)
        db.session.commit()
        flash('Предмет успешно обновлен')
        return redirect(url_for('storage'))

    return render_template('edit_item.html', item=item)


# Удаление предмета
@app.route("/storage/delete/<int:item_id>", methods=['DELETE'])
@login_required
def delete_item(item_id):
    if not current_user.admin:
        return jsonify({'error': 'Доступ запрещен'}), 403

    item = Storage.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Предмет удален'}), 200


# Страница управления пользователями
@app.route("/users")
@login_required
def users():
    if not current_user.admin:
        flash("Доступ запрещен")
        return redirect(url_for('get_data'))

    users_list = User.query.all()
    return render_template("users.html", users=users_list)


# Изменение статуса администратора
@app.route("/users/toggle_admin/<int:user_id>", methods=['POST'])
@login_required
def toggle_admin(user_id):
    if not current_user.admin:
        return jsonify({'error': 'Доступ запрещен'}), 403

    # Предотвращаем снятие прав у самого себя
    if user_id == current_user.id:
        return jsonify({'error': 'Нельзя изменить права администратора у самого себя'}), 400

    user = User.query.get_or_404(user_id)
    user.admin = not user.admin
    db.session.commit()

    return jsonify({
        'message': f"Права администратора {'предоставлены' if user.admin else 'отозваны'}",
        'admin': user.admin
    })


# Страница планирования закупок
@app.route("/purchases", methods=['GET', 'POST'])
@login_required
def purchases():
    if not current_user.admin:
        flash("Доступ запрещен")
        return redirect(url_for('get_data'))

    if request.method == 'POST':
        name_eq = request.form.get('name_eq')
        price = request.form.get('price', type=int)
        count = request.form.get('count', type=int)
        supplier = request.form.get('supplier')
        status = request.form.get('status') == '1'

        if name_eq and price is not None and count is not None and supplier:
            new_purchase = Purchases(
                name_eq=name_eq, price=price, count=count, supplier=supplier, status=status)
            db.session.add(new_purchase)

            # Если статус "выполнено", добавляем товар на склад
            if status:
                item = Storage.query.filter_by(name=name_eq).first()
                if item:
                    item.count += count
                else:
                    new_item = Storage(name=name_eq, count=count)
                    db.session.add(new_item)

            db.session.commit()
            flash('План закупки успешно добавлен')
            return redirect(url_for('purchases'))

    purchase_plans = Purchases.query.all()
    return render_template("purchases.html", purchases=purchase_plans)


# Изменение статуса закупки
@app.route("/purchases/toggle_status/<int:purchase_id>", methods=['POST'])
@login_required
def toggle_purchase_status(purchase_id):
    if not current_user.admin:
        return jsonify({'error': 'Доступ запрещен'}), 403

    purchase = Purchases.query.get_or_404(purchase_id)
    item = Storage.query.filter_by(name=purchase.name_eq).first()

    if purchase.status:  # Если статус "выполнено", пытаемся отменить
        if item and item.count >= purchase.count:
            item.count -= purchase.count
            purchase.status = False
            db.session.commit()
            return jsonify({
                'message': f"Статус закупки изменен на 'не выполнено'. Количество предметов '{purchase.name_eq}' уменьшено на складе.",
                'status': purchase.status
            })
        else:
            return jsonify({'error': f"Недостаточно предметов '{purchase.name_eq}' на складе для отмены выполнения закупки."}), 400
    else:  # Если статус "не выполнено", пытаемся выполнить
        if item:
            item.count += purchase.count
        else:
            new_item = Storage(name=purchase.name_eq, count=purchase.count)
            db.session.add(new_item)

        purchase.status = True
        db.session.commit()
        return jsonify({
            'message': f"Статус закупки изменен на 'выполнено'. Предметы '{purchase.name_eq}' добавлены на склад.",
            'status': purchase.status
        })


# Удаление закупки
@app.route("/purchases/delete/<int:purchase_id>", methods=['DELETE'])
@login_required
def delete_purchase(purchase_id):
    if not current_user.admin:
        return jsonify({'error': 'Доступ запрещен'}), 403

    purchase = Purchases.query.get_or_404(purchase_id)
    db.session.delete(purchase)
    db.session.commit()

    return jsonify({'message': 'Закупка удалена'}), 200


@app.route('/my_inventory')
@login_required
def my_inventory():
    user_equipment = Equipment.query.filter_by(user_id=current_user.id).all()
    return render_template('my_inventory.html', equipment=user_equipment)


@app.route("/user_inventory/<int:user_id>")
@login_required
def user_inventory(user_id):
    user_equipment = Equipment.query.filter_by(user_id=user_id).all()
    return jsonify({
        'equipment': [{
            'equipment_id': item.equipment_id,
            'storage': Storage.query.get(item.equipment_id),
            'count': item.count
        } for item in user_equipment]
    })


@app.route("/profile/<int:user_id>")
@login_required
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    user_equipment = Equipment.query.filter_by(user_id=user.id).all()
    return render_template("user_profile.html", user=user, equipment=user_equipment)


# Страница заявок (для всех пользователей)
@app.route("/requests")
@login_required
def view_requests():
    if current_user.admin:
        # Для админа показываем все заявки с возможностью управления
        requests = Requests.query.order_by(Requests.created_at.desc()).all()
        return render_template('admin_requests.html', requests=requests)
    else:
        # Для обычного пользователя показываем только его заявки
        user_requests = Requests.query.filter_by(user_id=current_user.id).order_by(Requests.created_at.desc()).all()
        return render_template('my_requests.html', requests=user_requests)


# Обработка заявки (одобрение/отклонение)
@app.route("/admin/request/<int:request_id>/<action>", methods=['POST'])
@login_required
def process_request(request_id, action):
    if not current_user.admin:
        flash('У вас нет доступа к этой функции', 'danger')
        return redirect(url_for('view_requests'))
    
    request = Requests.query.get_or_404(request_id)
    storage_item = Storage.query.get(request.equipment_id)
    
    if not storage_item:
        flash('Оборудование не найдено', 'danger')
        return redirect(url_for('view_requests'))
    
    try:
        if action == 'approve':
            # Проверяем все активные заявки на это оборудование
            active_requests = Requests.query.filter_by(
                equipment_id=request.equipment_id,
                status=None
            ).order_by(Requests.created_at).all()
            
            # Считаем общее количество запрошенного оборудования в активных заявках
            total_requested = sum(r.count for r in active_requests if r.id <= request.id)
            
            if storage_item.count >= total_requested:
                request.status = True
                storage_item.count -= request.count
                flash('Заявка одобрена', 'success')
            else:
                flash('Недостаточно оборудования на складе с учетом всех активных заявок', 'danger')
                return redirect(url_for('view_requests'))
        elif action == 'reject':
            request.status = False
            flash('Заявка отклонена', 'danger')
        
        db.session.commit()
        return redirect(url_for('view_requests'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Произошла ошибка при обработке заявки: {str(e)}', 'danger')
        return redirect(url_for('view_requests'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
