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
    return render_template('user/available_equipment.html', equipment=equipment)

# Создание заявки на получение инвентаря
@user_bp.route('/request_equipment/<int:equipment_id>', methods=['GET', 'POST'])
@login_required
def request_equipment(equipment_id):
    equipment = Storage.query.get_or_404(equipment_id)
    
    if request.method == 'POST':
        requested_count = int(request.form.get('count', 1))
        
        if requested_count <= 0:
            flash('Количество должно быть положительным числом', 'error')
            return redirect(url_for('user.available_equipment'))
            
        if requested_count > equipment.count:
            flash('Запрошенное количество превышает доступное', 'error')
            return redirect(url_for('user.available_equipment'))
            
        new_request = Requests(
            user_id=current_user.id,
            equipment_id=equipment_id,
            count=requested_count,
            status=False,
            request_type='получение'
        )
        
        db.session.add(new_request)
        db.session.commit()
        
        flash('Заявка на получение инвентаря создана', 'success')
        return redirect(url_for('user.my_requests'))
        
    return render_template('user/request_equipment.html', equipment=equipment)

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
        
    return render_template('user/repair_request.html', equipment=equipment)

# Просмотр своих заявок
@user_bp.route('/my_requests')
@login_required
def my_requests():
    requests = Requests.query.filter_by(user_id=current_user.id).all()
    return render_template('user/my_requests.html', requests=requests)

# Просмотр своего инвентаря
@user_bp.route('/my_equipment')
@login_required
def my_equipment():
    equipment = Equipment.query.filter_by(user_id=current_user.id).all()
    return render_template('user/my_equipment.html', equipment=equipment)
