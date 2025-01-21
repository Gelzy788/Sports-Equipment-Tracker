from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, Storage, Equipment, Requests
from datetime import datetime

user_bp = Blueprint('user', __name__)

# Просмотр доступного инвентаря
@user_bp.route('/available_equipment')
@login_required
def available_equipment():
    equipment = Storage.query.all()
    return render_template('available_equipment.html', equipment=equipment)

# Создание заявки на получение инвентаря
@user_bp.route('/request_equipment/<int:equipment_id>', methods=['POST'])
@login_required
def request_equipment(equipment_id):
    storage = Storage.query.get_or_404(equipment_id)
    
    # Получаем запрошенное количество
    quantity = int(request.form.get('quantity', 1))
    
    # Проверяем, достаточно ли оборудования
    if quantity > storage.count:
        flash('Недостаточно оборудования на складе', 'error')
        return redirect(url_for('user.available_equipment'))
    
    # Проверяем, нет ли уже активной заявки на это оборудование
    existing_request = Requests.query.filter_by(
        user_id=current_user.id,
        equipment_id=equipment_id,
        status=False,
        request_type='получение'
    ).first()
    
    if existing_request:
        flash('У вас уже есть активная заявка на это оборудование', 'warning')
        return redirect(url_for('user.available_equipment'))
    
    # Создаем новую заявку
    new_request = Requests(
        user_id=current_user.id,
        equipment_id=equipment_id,
        request_type='получение',
        count=quantity,
        status=False
    )
    
    # Уменьшаем доступное количество
    storage.count -= quantity
    
    try:
        db.session.add(new_request)
        db.session.commit()
        flash('Заявка успешно создана', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Произошла ошибка при создании заявки', 'error')
    
    return redirect(url_for('user.available_equipment'))

# Создание заявки на ремонт/замену
@user_bp.route('/repair_request/<int:equipment_id>', methods=['GET', 'POST'])
@login_required
def repair_request(equipment_id):
    equipment = Equipment.query.filter_by(
        equipment_id=equipment_id,
        user_id=current_user.id
    ).first_or_404()
    
    if request.method == 'POST':
        description = request.form.get('description', '')
        if not description:
            flash('Необходимо указать описание проблемы', 'error')
            return redirect(url_for('user.my_equipment'))
            
        new_request = Requests(
            user_id=current_user.id,
            equipment_id=equipment_id,
            description=description,
            status=False,
            request_type='ремонт'
        )
        
        db.session.add(new_request)
        db.session.commit()
        
        flash('Заявка на ремонт создана', 'success')
        return redirect(url_for('user.my_requests'))
        
    return render_template('repair_request.html', equipment=equipment)

# Просмотр своих заявок
@user_bp.route('/my_requests')
@login_required
def my_requests():
    requests = Requests.query.filter_by(user_id=current_user.id).all()
    return render_template('my_requests.html', requests=requests)

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
