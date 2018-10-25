from encyclopedia import app, db, bcrypt, mail
from flask import render_template, url_for, flash, redirect, request, session
from encyclopedia.forms import RegistrationForm, LoginForm, \
    UpdateAccountForm, RequestResetForm, ResetPasswordForm, SourceForm
from encyclopedia.models import User, Source
from flask_login import login_user, logout_user, current_user, login_required
import secrets
import os
from PIL import Image
from flask_mail import Message
import wikipedia as wiki
from unsplash.api import Api
from unsplash.auth import Auth
from bs4 import BeautifulSoup
import requests
from datetime import datetime



client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
redirect_uri = ""
code = ""

auth = Auth(client_id, client_secret, redirect_uri, code=code)
api = Api(auth)


@app.route("/")
@app.route("/home", methods=['GET', 'POST'])
@login_required
def home():
    page = request.args.get('page', 1, type=int)
    sources = Source.query.filter(Source.user_id == current_user.id)\
        .order_by(Source.date_posted.desc()).paginate(page=page, per_page=2)
    return render_template('home.html', sources=sources)


@app.route("/about")
def about():
    return render_template('about.html', title='about')


def get_request():
    search_term = request.form['search_results'].title()
    wik_summary = wiki.summary(search_term)
    full_url = "https://en.wikipedia.org/wiki/" + search_term
    unsplash_json = api.search.photos(search_term)
    unsplash_pic = unsplash_json['results'][0].links.download
    return search_term, wik_summary, full_url, unsplash_json, unsplash_pic


@app.route('/search', methods=['POST', 'GET'])
@login_required
def search():
    try:
        if request.form.get('search_results') is None:
            return render_template('search.html', title='search')
        else:
            search_term, wik_summary, full_url, unsplash_json, unsplash_pic = get_request()
            session['search_term'] = search_term
            session['wik_summary'] = wik_summary
            session['full_url'] = full_url
            return render_template('search.html', title='results', wik_summary=wik_summary,
                                   search_term=search_term, unsplash_pic=unsplash_pic,
                                   full_url=full_url)
    except wiki.DisambiguationError:
        # If there is more than one search result a DisambiguationError occurs.
        # We will accept and get the page from wikipedia.
        flash("Too ambiguous. Please be more specific with your search or choose an option below", 'danger')
        search_term = request.form['search_results'].title()
        full_url = "https://en.wikipedia.org/wiki/" + search_term
        # Using the Beautiful soup webscrapper to grab the search terms and categories.
        source = requests.get(full_url).text
        soup = BeautifulSoup(source, 'html.parser')
        # Finds Categories
        categories = soup.find_all('h2')
        # Finds search terms
        subItems = soup.find_all('ul')
        category_count = len(categories)
        subItem_count = len(subItems)
        categoryArray = []
        subItemArray = []

        for x in range(1, category_count -1):
            # Loops through categories and adds to categoryArray
            h2_span = categories[x].find('span').text
            categoryArray.append(h2_span)

        for x in range(2, category_count):
            # Loops through list of search terms contained in an unordered list and anchor tags.
            subArray = []
            h2_span = subItems[x].find_all('a')
            for y in range(0, len(h2_span)):
                # Then loops through the anchor taged items and adds them to the subArray
                try:
                    item = h2_span[y]
                    subArray.append(item['title'])
                except KeyError:
                    # Accepts a error if there isnt an item with an anchor tag.
                    pass
                # Adds to subItemArray.
            subItemArray.append(subArray)
            for array in subItemArray:
                # Checks for empty arrays due to passing KeyError and gets rid of them.
                x = 0
                if len(array) == 0:
                    subItemArray.pop(x)
                x += 1
        print(len(subItemArray))
        return render_template('search.html', disambigCategory=zip(categoryArray, subItemArray))

    except Exception:
        flash("Page doesn't exist for the search")
    return redirect(url_for('search'))


@app.route("/source", methods=['GET', 'POST'])
@login_required
def save_source():
    form = SourceForm()
    form.title.data = session.get('search_term')
    form.content.data = session.get('wik_summary')
    form.url.data = session.get('full_url')
    date_saved = datetime.now()
    source = Source(title=form.title.data, date_posted=date_saved,
                    content=form.content.data,
                    url=form.url.data, user_id=current_user.id)
    if form.validate_on_submit():
        source.title = form.title.data
        source.content = form.content.data
        source.url = form.url.data
        db.session.add(source)
        db.session.commit()
        flash('Your source has been saved!', 'success')
        return redirect(url_for('home'))
    return render_template('save_source.html', title='Save Sources', form=form,  legend='New Source', source=source)


@app.route("/source/<int:source_id>")
def source(source_id):
    source = Source.query.get_or_404(source_id)
    return render_template('source.html', title=source.title, source=source)


@app.route("/source/<int:source_id>/update", methods=['GET', 'POST'])
@login_required
def update_source(source_id):
    source = Source.query.get_or_404(source_id)
    form = SourceForm()
    if form.validate_on_submit():
        source.title = form.title.data
        source.content = form.content.data
        source.url = form.url.data
        db.session.commit()
        flash('Your source has been updated!', 'success')
        return redirect(url_for('source', source_id=source.id))
    elif request.method == 'GET':
        form.title.data = source.title
        form.content.data = source.content
        form.url.data = source.url
    return render_template('save_source.html', title='Update Sources',
                           form=form, legend='Update Source')


@app.route("/source/<int:source_id>/delete", methods=['POST'])
@login_required
def delete_source(source_id):
    source = Source.query.get_or_404(source_id)
    db.session.delete(source)
    db.session.commit()
    flash('Your source has been deleted!', 'success')
    return redirect(url_for('home'))



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


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@gmail.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link: 
    {url_for('reset_token', token=token, _external=True)}
    
    If you did not make this request then simply ignore this email and no changes will be made.
    '''
    mail.send(msg)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.')
    return render_template('reset_request.html', title='Password Reset', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('This is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)