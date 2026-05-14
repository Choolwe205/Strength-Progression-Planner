from datetime import datetime
from app import db

class User(db.Model):
    __tablename__ = 'users'
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    username    = db.Column(db.String(50), unique=True, nullable=False)
    password    = db.Column(db.String(200), nullable=False)
    dob         = db.Column(db.Date, nullable=False)
    weight_kg   = db.Column(db.Float, nullable=False)
    height_cm   = db.Column(db.Float, nullable=False)
    experience  = db.Column(db.String(20), nullable=False)
    bmi         = db.Column(db.Float)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    workouts    = db.relationship('Workout', backref='user', lazy=True)
    progression = db.relationship('ProgressionLog', backref='user', lazy=True)

class Workout(db.Model):
    __tablename__ = 'workouts'
    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    exercise       = db.Column(db.String(50), nullable=False)
    target_sets    = db.Column(db.Integer)
    target_reps    = db.Column(db.Integer)
    target_weight  = db.Column(db.Float)
    actual_sets    = db.Column(db.Integer)
    actual_reps    = db.Column(db.Integer)
    actual_weight  = db.Column(db.Float)
    completed      = db.Column(db.Boolean, default=False)
    timestamp      = db.Column(db.DateTime, default=datetime.utcnow)

class ProgressionLog(db.Model):
    __tablename__ = 'progression_log'
    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    exercise       = db.Column(db.String(50), nullable=False)
    current_weight = db.Column(db.Float)
    current_reps   = db.Column(db.Integer)
    failures       = db.Column(db.Integer, default=0)
    deload_active  = db.Column(db.Boolean, default=False)
    updated_at     = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'exercise'),)