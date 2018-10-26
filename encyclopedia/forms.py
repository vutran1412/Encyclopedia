from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flask_login import current_user
from encyclopedia.models import User


# Registration form, this is where user can register for an account
class RegistrationForm(FlaskForm):
    # input fields with validations
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])

    submit = SubmitField('Sign Up')

    # function to validate username, to make sure user doesn't register with an existing username
    def validate_username(self, username):
        # try to query the db to see if the username user entered in the form is already in the db
        user = User.query.filter_by(username=username.data).first()
        # if user exists then raise validation error
        if user:
            raise ValidationError('That username is taken, please pick a different one.')

    # function to validate email to make sure user doesn't register with an existing email
    def validate_email(self, email):
        # query the db to see if the email is already in the db
        email = User.query.filter_by(email=email.data).first()
        # if email exists then raise validation error
        if email:
            raise ValidationError('That email is registered, please use a different one.')


# login form class, user must log in to access the app's functions
class LoginForm(FlaskForm):
    # form input fields with validations
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


# update account form, allows user to update username, email, and picture
class UpdateAccountForm(FlaskForm):
    # form input fields with validations
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

    # function to validate username, to make sure user doesn't register with an existing username
    def validate_username(self, username):
        # if username is not the same as the current user name
        if username.data != current_user.username:
            # check to see if the new username exists in the database
            user = User.query.filter_by(username=username.data).first()
            # if user exists then raise validation error
            if user:
                raise ValidationError('That username is taken, please pick a different one.')

    # function to validate email, to make sure user doesn't register with an existing email
    def validate_email(self, email):
        # if email is not the same as current user email
        if email.data != current_user.email:
            # check to see if the new email exists in the database
            email = User.query.filter_by(email=email.data).first()
            # if email exists then raise validation error
            if email:
                raise ValidationError('That email is registered, please use a different one.')


# request reset form, user can request a reset password form using their email
class RequestResetForm(FlaskForm):

    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    # validates the user's email to make sure user is in db
    def validate_email(self, email):
        # check to see if user's email is in db
        user = User.query.filter_by(email=email.data).first()
        # if not email exists raise validation error
        if user is None:
            raise ValidationError('There is no account with that email. You must register first')


# reset password form, allows user to reset password
class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

# source form, allows user to save source
class SourceForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    url = StringField('URL', validators=[DataRequired()])
    submit = SubmitField('Save Source')

