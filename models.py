from extensions import db  # Import from extensions
from flask_login import UserMixin
from util import hash_pass
from datetime import datetime, timezone, timedelta
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import Email, DataRequired

class Users(db.Model, UserMixin):
    __tablename__ = 'Users'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, unique=True)
    username = db.Column(db.String(64), nullable=False, unique=True)
    access_token = db.Column(db.String(255), nullable=False)
    refresh_token = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    phone = db.Column(db.String(100), nullable=True)
    password = db.Column(db.LargeBinary)
    membership_time = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc) + timedelta(days=7))

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]
            if property == 'password':
                value = hash_pass(value)  # Hash the password
            setattr(self, property, value)

    def __repr__(self):
        return str(self.username)
    
class Customize(db.Model):
    __tablename__ = 'Customize'
    
    id = db.Column(db.Integer, primary_key=True)
    client = db.Column(db.Boolean, default=False)
    user = db.Column(db.Boolean, default=False)
    sealed = db.Column(db.Boolean, default=False)
    intro = db.Column(db.String(250), nullable=True)
    links = db.Column(db.JSON, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)

    # Establish a relationship with the Users table
    users = db.relationship('Users', backref=db.backref('customize', lazy=True))

    def __repr__(self):
        return f"<Bids for User ID {self.user_id}>"  
    
class Skills(db.Model):
    __tablename__ = 'Skills'
    
    id = db.Column(db.Integer, primary_key=True)
    skills = db.Column(db.JSON, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)

    # Establish a relationship with the Users table
    users = db.relationship('Users', backref=db.backref('skills', lazy=True))

    def __repr__(self):
        return f"<Bids for User ID {self.user_id}>"  
    
class Pricing(db.Model):
    __tablename__ = 'Pricing'
    
    id = db.Column(db.Integer, primary_key=True)
    hourly = db.Column(db.String(64), nullable=True)
    fixed = db.Column(db.String(64), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)

    # Establish a relationship with the Users table
    users = db.relationship('Users', backref=db.backref('pricing', lazy=True))

    def __repr__(self):
        return f"<Bids for User ID {self.user_id}>"  
    
class Bidding(db.Model):
    __tablename__ = 'Bidding'
    
    id = db.Column(db.Integer, primary_key=True)
    is_bidding = db.Column(db.String(64), nullable=False)
    task = db.Column(db.String(100), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)

    # Establish a relationship with the Users table
    users = db.relationship('Users', backref=db.backref('bidding', lazy=True))

    def __repr__(self):
        return f"<Bids for User ID {self.user_id}>"  



class CreateAccountForm(FlaskForm):
    email = StringField('Email',
                        id='email_create',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password',
                             id='pwd_create',
                             validators=[DataRequired()])

class LoginForm(FlaskForm):
    username = StringField('Username',
                         id='username_login',
                         validators=[DataRequired()])
    password = PasswordField('Password',
                             id='pwd_login',
                             validators=[DataRequired()])