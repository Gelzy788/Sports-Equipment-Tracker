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
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer(), db.ForeignKey('storage.id'))
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'))
    count = db.Column(db.Integer(), default=1)


class Storage(db.Model):
    __tablename__ = 'storage'
    id = db.Column(db.Integer(), primary_key=True, nullable=False)
    name = db.Column(db.String(64), nullable=False)
    count = db.Column(db.Integer())


class Requests(db.Model):
    __tablename__ = 'requests'
    id = db.Column(db.Integer(), primary_key=True, nullable=False)
    user_id = db.Column(db.BigInteger(), db.ForeignKey('users.id'))
    friend_id = db.Column(db.BigInteger(), db.ForeignKey('users.id'))
    status = db.Column(db.Boolean, default=False)


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
