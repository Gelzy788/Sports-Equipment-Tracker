from config import db
from datetime import datetime
from datetime import time
from flask_login import UserMixin


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer(), primary_key=True, unique=True, nullable=False)
    username = db.Column(db.String(64), nullable=False, unique=True)
    email = db.Column(db.String(128), nullable=False, unique=True)
    password = db.Column(db.String(64), nullable=False)
    admin = db.Column(db.Boolean, default=False)
    profile_picture = db.Column(db.String(128), nullable=True)


class Equipment(db.Model):
    __tablename__ = 'equipment'
    equipment_id = db.Column(db.Integer(), db.ForeignKey(
        'storage.id'), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey(
        'users.id'), primary_key=True)
    count = db.Column(db.Integer(), default=1)

    __table_args__ = (db.UniqueConstraint(
        'equipment_id', 'user_id', name='uq_equipment_user'),)

    storage = db.relationship('Storage', backref='equipment')


class Storage(db.Model):
    __tablename__ = 'storage'
    id = db.Column(db.Integer(), primary_key=True, nullable=False)
    name = db.Column(db.String(64), nullable=False)
    count = db.Column(db.Integer())


class Requests(db.Model):
    __tablename__ = 'requests'
    id = db.Column(db.Integer(), primary_key=True, nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    equipment_id = db.Column(db.Integer(), db.ForeignKey('storage.id'))
    count = db.Column(db.Integer(), default=1)
    description = db.Column(db.Text)
    request_type = db.Column(db.String(20))  # 'получение' или 'ремонт'
    status = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Добавляем отношения
    storage = db.relationship('Storage', backref='requests')
    user = db.relationship('User', backref='requests')


class Purchases(db.Model, UserMixin):
    __tablename__ = 'purchases'
    id = db.Column(db.Integer(), primary_key=True, nullable=False)
    name_eq = db.Column(db.String(64), nullable=False)
    price = db.Column(db.Integer(), nullable=False)
    count = db.Column(db.Integer())
    supplier = db.Column(db.String())
    status = db.Column(db.Boolean, default=False)

    @property
    def total_price(self):
        return self.price * self.count
