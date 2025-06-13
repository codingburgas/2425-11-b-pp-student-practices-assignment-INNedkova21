from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from HandwrittenDigitRecognizer.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = 'Users'
    __table_args__ = {'extend_existing': True}

    ID = db.Column(db.Integer, primary_key=True)
    FirstName = db.Column(db.String(50), nullable=False)
    LastName = db.Column(db.String(50), nullable=False)
    Email = db.Column(db.String(120), unique=True, nullable=False)
    Password = db.Column(db.String(120), nullable=False)
    Role = db.Column(db.String(120), nullable=False, default='User')

    def set_password(self, password):
        self.Password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.Password, password)

    def get_id(self):
        return str(self.ID)

    def __repr__(self):
        return f'<User {self.Email}>'