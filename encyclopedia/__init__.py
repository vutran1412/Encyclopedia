from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = '3ad2c1998384bfa7718e7f4799cbecb554b26578a99a4b06141fe48e3425be23e457c13963c33ee3c892ed4e5cc2228a07d97805d11a7238654725913b896a1f962d049fad60bc7b306110c8c10e3f210b742cd7476f27ea81bc0ddce2926b0c7b1328c4ab1c4f62b5d0e32ea4dd64ff98e251fa417e330a0ac15bdeb5a83191120ce6427ab5ac9e7d46cb0b99cb9ba7b01939b7187b6f889462576f9307d52dce1690a8f82d041369a32f3b96345224af3dfec0e4490f5ca53a5e2c055aa12727950680277ed220a2a2565252bd3a9034756df6fc4f698547bee58a6cf45080a78d707193537881817686a4760a445e31dc56d9568896d0f8e47329787bae67'
app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///site.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')
mail = Mail(app)

from encyclopedia import routes
