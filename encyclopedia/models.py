from encyclopedia import db, login_manager, app
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from datetime import datetime
from flask_login import UserMixin

# login manager to get user id
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# user table model to store individual users in db
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    research = db.relationship('Source', backref='user', lazy=True)

    # generate a reset token using TimedJSONWebSignatureSerializer, this will be used to reset user password
    # reset token expires in 30 minutes
    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    # static method to verify the reset token that was emailed to the user
    @staticmethod
    def verify_reset_token(token):
        # pass the secret key into serializer
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        # return user if token is verified
        return User.query.get(user_id)

    # String representation of the user model
    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')  "

# source table store sources in db
class Source(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    url = db.Column(db.Text, nullable=False)
    # user will have a one to many relationship with sources, since one user can have many sources saved
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # string representation of the source model
    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"
