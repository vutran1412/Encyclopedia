from encyclopedia import app, db, bcrypt
from flask import render_template, url_for, flash, redirect, request
from encyclopedia.forms import RegistrationForm, LoginForm, UpdateAccountForm
from encyclopedia.models import User, Source
from flask_login import login_user, logout_user, current_user, login_required
import wikipedia as wiki
from unsplash.api import Api
from unsplash.auth import Auth


client_id = ""
client_secret = ""
redirect_uri = ""
code = ""

auth = Auth(client_id, client_secret, redirect_uri, code=code)
api = Api(auth)

sources = [
    {
        'title': 'Crocodiles',
        'content': 'Nature\'s deadliest predator',
        'date_accessed': 'October 10, 2018',
        'url': 'https://en.wikipedia.org/wiki/Crocodile'
    }
]


@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', title='Encyclopedia Researcher', sources=sources)


@app.route("/about")
def about():
    return render_template('about.html', title='about')


@app.route('/search', methods=['POST', 'GET'])
def search():
    if request.form.get('search_results') == None:  #This is avoiding an error where search_results was a bad key because it did not exist since the form had not been sent
        return render_template('search.html', title='search')
    else:
        search_term = request.form['search_results']
        wik_summary = wiki.summary(search_term)
        unsplash_json = api.search.photos(search_term)
        unsplash_pic = unsplash_json['results'][0].links.download

        return render_template('search.html', title='results', wik_summary=wik_summary, search_term=search_term, unsplash_pic=unsplash_pic)




@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please Check the email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/account")
@login_required
def account():
    form = UpdateAccountForm()
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)