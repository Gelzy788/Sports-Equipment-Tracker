from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from models import db, Storage, Equipment, Requests
from datetime import datetime

user_bp = Blueprint('user', __name__)

# Просмотр доступного инвентаря
@user_bp.route('/available_equipment')
@login_required
def available_equipment():
    # Получаем все оборудование
    equipment = Storage.query.all()
    
    # Получаем активные заявки пользователя
    user_requests = Requests.query.filter_by(
        user_id=current_user.id,
        status=None  # None означает, что заявка еще не обработана
    ).all()
    
    # Создаем множество ID оборудования, на которое есть активные заявки
    active_requests = {req.equipment_id for req in user_requests}
    
    # Добавляем информацию о наличии активных заявок к каждому элементу оборудования
    for item in equipment:
        item.has_active_request = item.id in active_requests
    
    return render_template('available_equipment.html', equipment=equipment)

# Создание заявки на получение инвентаря
@user_bp.route('/request_equipment/<int:equipment_id>', methods=['POST'])
@login_required
def request_equipment(equipment_id):
    print(f"Создание заявки для equipment_id: {equipment_id}")
    storage = Storage.query.get_or_404(equipment_id)
    
    # Получаем запрошенное количество
    quantity = int(request.form.get('quantity', 1))
    print(f"Запрошенное количество: {quantity}")
    
    # Проверяем, достаточно ли оборудования
    if quantity > storage.count:
        flash('Недостаточно оборудования на складе', 'error')
        return redirect(url_for('user.available_equipment'))
    
    # Проверяем, нет ли уже активной заявки на это оборудование
    existing_request = Requests.query.filter_by(
        user_id=current_user.id,
        equipment_id=equipment_id,
        status=None,
        request_type='получение'
    ).first()
    
    if existing_request:
        flash('У вас уже есть активная заявка на это оборудование', 'warning')
        return redirect(url_for('user.available_equipment'))
    
    print(f"Создание новой заявки для пользователя {current_user.id}")
    # Создаем новую заявку
    new_request = Requests(
        user_id=current_user.id,
        equipment_id=equipment_id,
        request_type='получение',
        count=quantity,
        status=None,
        created_at=datetime.utcnow()
    )
    
    try:
        print("Добавление заявки в базу данных")
        db.session.add(new_request)
        db.session.commit()
        print("Заявка успешно создана")
        flash('Заявка успешно создана', 'success')
    except Exception as e:
        print(f"Ошибка при создании заявки: {str(e)}")
        db.session.rollback()
        flash('Произошла ошибка при создании заявки', 'error')
    
    return redirect(url_for('user.available_equipment'))

# Создание заявки на ремонт/замену
@user_bp.route('/create_repair_request/<int:equipment_id>', methods=['POST'])
@login_required
def create_repair_request(equipment_id):
    equipment = Equipment.query.filter_by(
        user_id=current_user.id,
        equipment_id=equipment_id
    ).first_or_404()

    description = request.form.get('description')
    count = int(request.form.get('count', 1))

    if not description:
        flash('Необходимо указать описание проблемы', 'danger')
        return redirect(url_for('user.repair_request', equipment_id=equipment_id))

    if count < 1 or count > equipment.count:
        flash('Неверное количество оборудования', 'danger')
        return redirect(url_for('user.repair_request', equipment_id=equipment_id))

    # Создаем заявку на ремонт
    repair_request = Requests(
        user_id=current_user.id,
        equipment_id=equipment_id,
        count=count,
        description=description,
        request_type='ремонт',
        status=None,
        created_at=datetime.utcnow(),
        status_viewed=True
    )

    try:
        db.session.add(repair_request)
        db.session.commit()
        flash('Заявка на ремонт создана', 'success')
    except:
        db.session.rollback()
        flash('Произошла ошибка при создании заявки', 'danger')

    return redirect(url_for('user.my_requests'))

# Просмотр своих заявок
@user_bp.route('/my_requests')
@login_required
def my_requests():
    # Получаем все заявки пользователя
    requests = Requests.query.filter_by(user_id=current_user.id).order_by(Requests.created_at.desc()).all()
    
    # Проверяем наличие непросмотренных уведомлений
    has_unviewed_requests = any(not r.status_viewed for r in requests)
    has_unviewed_approved = any(not r.status_viewed and r.status == 1 for r in requests)
    has_unviewed_rejected = any(not r.status_viewed and r.status == 0 for r in requests)
    
    return render_template('my_requests.html', 
                         requests=requests,
                         has_unviewed_requests=has_unviewed_requests,
                         has_unviewed_approved=has_unviewed_approved,
                         has_unviewed_rejected=has_unviewed_rejected)

# Просмотр своего инвентаря
@user_bp.route('/my_equipment')
@login_required
def my_equipment():
    equipment = Equipment.query.filter_by(user_id=current_user.id).all()
    return render_template('my_equipment.html', equipment=equipment)

# Просмотр истории использования инвентаря
@user_bp.route('/equipment_history')
@login_required
def equipment_history():
    history = Requests.query.filter_by(user_id=current_user.id).order_by(Requests.request_date.desc()).all()
    return render_template('equipment_history.html', history=history)

# Возврат инвентаря
@user_bp.route('/return_equipment/<int:equipment_id>', methods=['POST'])
@login_required
def return_equipment(equipment_id):
    equipment = Equipment.query.get_or_404(equipment_id)
    if equipment.current_holder_id != current_user.id:
        flash('У вас нет этого оборудования', 'error')
        return redirect(url_for('user.my_equipment'))
    
    equipment.current_holder_id = None
    equipment.status = 'available'
    
    storage_item = Storage.query.filter_by(equipment_id=equipment_id).first()
    if storage_item:
        storage_item.quantity_available += 1
    
    db.session.commit()
    flash('Оборудование успешно возвращено', 'success')
    return redirect(url_for('user.my_equipment'))

# Просмотр уведомлений
@user_bp.route('/notifications')
@login_required
def notifications():
    requests = Requests.query.filter_by(user_id=current_user.id).all()
    return render_template('notifications.html', notifications=requests)

# Отмена заявки
@user_bp.route('/cancel_request/<int:request_id>', methods=['POST'])
@login_required
def cancel_request(request_id):
    request_item = Requests.query.get_or_404(request_id)
    
    # Проверяем, что заявка принадлежит текущему пользователю
    if request_item.user_id != current_user.id:
        flash('У вас нет прав для отмены этой заявки', 'error')
        return redirect(url_for('user.my_requests'))
    
    # Проверяем, что заявка еще не обработана
    if request_item.status:
        flash('Нельзя отменить уже обработанную заявку', 'error')
        return redirect(url_for('user.my_requests'))
    
    # Если это заявка на получение оборудования, возвращаем его в доступное количество
    if request_item.request_type == 'получение':
        storage_item = Storage.query.get(request_item.equipment_id)
        if storage_item:
            storage_item.count += request_item.count
            
    # Удаляем заявку
    db.session.delete(request_item)
    db.session.commit()
    
    flash('Заявка успешно отменена', 'success')
    return redirect(url_for('user.my_requests'))

# Создание кастомной заявки
@user_bp.route('/create_custom_request', methods=['POST'])
@login_required
def create_custom_request():
    equipment_name = request.form.get('equipment_name')
    custom_description = request.form.get('custom_description')
    request_type = request.form.get('request_type')
    
    if not equipment_name or not custom_description:
        flash('Пожалуйста, заполните все поля', 'error')
        return redirect(url_for('user.available_equipment'))
    
    try:
        # Создаем новую заявку
        new_request = Requests(
            user_id=current_user.id,
            equipment_name=equipment_name,  
            custom_description=custom_description,
            request_type=request_type,
            status=None,
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_request)
        db.session.commit()
        flash('Кастомная заявка успешно создана', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка при создании заявки: {str(e)}")  
        flash(f'Произошла ошибка при создании заявки: {str(e)}', 'error')
    
    return redirect(url_for('user.my_requests'))

# API для поиска оборудования
@user_bp.route('/api/equipment/search')
@login_required
def search_equipment():
    term = request.args.get('term', '')
    if len(term) < 2:
        return jsonify([])
    
    # Поиск оборудования по названию
    equipment = Storage.query.filter(Storage.name.ilike(f'%{term}%')).all()
    return jsonify([{
        'id': item.id,
        'name': item.name,
        'description': item.description
    } for item in equipment])

# Отмечаем уведомления как просмотренные
@user_bp.route('/mark_notifications_viewed', methods=['POST'])
@login_required
def mark_notifications_viewed():
    # Получаем все непросмотренные заявки пользователя
    unviewed_requests = Requests.query.filter_by(
        user_id=current_user.id,
        status_viewed=False
    ).all()
    
    # Отмечаем их как просмотренные
    for request in unviewed_requests:
        request.status_viewed = True
    
    try:
        db.session.commit()
        return jsonify({'success': True})
    except:
        db.session.rollback()
        return jsonify({'success': False}), 500

# Просмотр формы заявки на ремонт
@user_bp.route('/repair_request/<int:equipment_id>', methods=['GET'])
@login_required
def repair_request(equipment_id):
    equipment = Equipment.query.filter_by(
        equipment_id=equipment_id,
        user_id=current_user.id
    ).first_or_404()
    
    return render_template('repair_request.html', equipment=equipment)
