from datetime import datetime
import os
from app import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # Relationships
    notifications_sent = db.relationship('Notification', backref='sent_by', lazy=True, foreign_keys='Notification.sent_by_id')
    files_uploaded = db.relationship('File', backref='uploaded_by', lazy=True)
    
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
    notifications = db.relationship('Notification', backref='student', lazy=True, foreign_keys='Notification.student_id')
    files = db.relationship('File', backref='student', lazy=True, foreign_keys='File.student_id')
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f'<Student {self.name}>'
    
    def whatsapp_link(self, message=""):
        """Generate WhatsApp link for this student"""
        # Clean the phone number (remove spaces, parentheses, and dashes)
        clean_phone = ''.join(filter(str.isdigit, self.phone))
        # If the phone number doesn't start with country code (55 for Brazil), add it
        if not clean_phone.startswith('55'):
            clean_phone = '55' + clean_phone
        return f"https://wa.me/{clean_phone}?text={message}"

class LessonType(db.Model):
    __tablename__ = 'lesson_types'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    default_price = db.Column(db.Float, nullable=True)
    
    # Relationships
    payments = db.relationship('Payment', backref='lesson_type', lazy=True, cascade="all, delete-orphan")
    files = db.relationship('File', backref='lesson_type', lazy=True)
    
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

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(20), nullable=False)  # 'Cobrança', 'Lembrete', 'Aviso'
    sent_date = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(20), default='Pendente')  # 'Enviada', 'Pendente'
    
    # For individual notifications
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)
    
    # For group notifications
    group_name = db.Column(db.String(100), nullable=True)
    lesson_type_id = db.Column(db.Integer, db.ForeignKey('lesson_types.id'), nullable=True)
    
    # Who sent the notification
    sent_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f'<Notification {self.id} - {self.title}>'

class File(db.Model):
    __tablename__ = 'files'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # 'PDF', 'Partitura', 'Áudio', 'Vídeo'
    upload_date = db.Column(db.DateTime, default=datetime.now)
    
    # For individual files
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)
    
    # For group files
    group_name = db.Column(db.String(100), nullable=True)
    lesson_type_id = db.Column(db.Integer, db.ForeignKey('lesson_types.id'), nullable=True)
    
    # Who uploaded the file
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f'<File {self.id} - {self.name}>'
    
    @property
    def file_extension(self):
        """Get the file extension"""
        _, ext = os.path.splitext(self.file_path)
        return ext.lower()
    
    @property
    def is_image(self):
        """Check if the file is an image"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
        return self.file_extension in image_extensions
    
    @property
    def is_audio(self):
        """Check if the file is an audio file"""
        audio_extensions = ['.mp3', '.wav', '.ogg', '.m4a']
        return self.file_extension in audio_extensions
    
    @property
    def is_video(self):
        """Check if the file is a video"""
        video_extensions = ['.mp4', '.avi', '.mov', '.wmv']
        return self.file_extension in video_extensions
    
    @property
    def is_document(self):
        """Check if the file is a document"""
        doc_extensions = ['.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx', '.ppt', '.pptx']
        return self.file_extension in doc_extensions
