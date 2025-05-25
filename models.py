from datetime import datetime
from app import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    payments = db.relationship('Payment', backref='student', lazy=True, cascade="all, delete-orphan")
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f'<Student {self.name}>'

class LessonType(db.Model):
    __tablename__ = 'lesson_types'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    default_price = db.Column(db.Float, nullable=True)
    
    # Relationships
    payments = db.relationship('Payment', backref='lesson_type', lazy=True, cascade="all, delete-orphan")
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f'<LessonType {self.name}>'

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    lesson_type_id = db.Column(db.Integer, db.ForeignKey('lesson_types.id'), nullable=False)
    reference_month = db.Column(db.Integer, nullable=False)  # 1-12 for months
    reference_year = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pendente')  # 'Pendente' or 'Pago'
    payment_date = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f'<Payment {self.id} - {self.student.name} - {self.reference_month}/{self.reference_year}>'
