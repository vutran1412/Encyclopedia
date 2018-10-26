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
"""The routes module sets up all the routes in the web app."""

# initializes the unsplash image api using environment variables
client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
redirect_uri = ""
code = ""
# authenticates the api
auth = Auth(client_id, client_secret, redirect_uri, code=code)
api = Api(auth)

# The home route this is the default page, user must be logged in to see all the saved sources
@app.route("/")
@app.route("/home", methods=['GET', 'POST']) # The home route accepts both the GET and POST methods
@login_required
# This function will be called to direct to the home page
def home():
    # initialize the requested page as 1
    page = request.args.get('page', 1, type=int)
    # query the sources logged in user save in db, ordered by the latest source saved, the source is paginated
    sources = Source.query.filter(Source.user_id == current_user.id)\
        .order_by(Source.date_posted.desc()).paginate(page=page, per_page=2)
    # Renders the html template for home and passes the sources in
    return render_template('home.html', sources=sources)


# Route for about page, to be populated with info from everyone in the group
@app.route("/about")
def about():
    return render_template('about.html', title='about')


# function to get api request when user makes a search
def get_request():
    # the search term is whatever user keys in the input form
    search_term = request.form['search_results'].title()
    # the wikipedia summary is returned
    wik_summary = wiki.summary(search_term)
    # the full url including the search term
    full_url = "https://en.wikipedia.org/wiki/" + search_term
    # unsplash json and url_pic returned from unsplash api
    unsplash_json = api.search.photos(search_term)
    unsplash_pic = unsplash_json['results'][0].links.download
    return search_term, wik_summary, full_url, unsplash_json, unsplash_pic


# search route to render search template
@app.route('/search', methods=['POST', 'GET'])
@login_required
def search():
    try:
        # if there are no search results, render the search template
        if request.form.get('search_results') is None:
            return render_template('search.html', title='search')
        else:
            # make the request to get the wikipedia summary and unsplash image
            search_term, wik_summary, full_url, unsplash_json, unsplash_pic = get_request()
            # save the results as session variables
            session['search_term'] = search_term
            session['wik_summary'] = wik_summary
            session['full_url'] = full_url
            # return the search template and pass the request results
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


# save route to save source to db
@app.route("/source", methods=['GET', 'POST'])
@login_required
def save_source():
    # create a source form object
    form = SourceForm()
    # populate the form fields with session variables
    form.title.data = session.get('search_term')
    form.content.data = session.get('wik_summary')
    form.url.data = session.get('full_url')
    # time stamp
    date_saved = datetime.now()
    # create a source object
    source = Source(title=form.title.data, date_posted=date_saved,
                    content=form.content.data,
                    url=form.url.data, user_id=current_user.id)
    # if form inputs are valid
    if form.validate_on_submit():
        # updates the source properties with form inputs
        source.title = form.title.data
        source.content = form.content.data
        source.url = form.url.data
        # Add source to db
        db.session.add(source)
        db.session.commit()
        # success message
        flash('Your source has been saved!', 'success')
        # redirect to home page where source will be displayed
        return redirect(url_for('home'))
    # render the save source and pass source
    return render_template('save_source.html', title='Save Sources', form=form,  legend='New Source', source=source)


# source route to render the source contents on a page
@app.route("/source/<int:source_id>")
def source(source_id):
    # retrieve the source from db
    source = Source.query.get_or_404(source_id)
    # render the source page html and pass the source
    return render_template('source.html', title=source.title, source=source)


# update route to update the source
@app.route("/source/<int:source_id>/update", methods=['GET', 'POST'])
@login_required
def update_source(source_id):
    # retrieve the source from db
    source = Source.query.get_or_404(source_id)
    # create a source form object
    form = SourceForm()
    # validates the form inputs
    if form.validate_on_submit():
        # save changes to source using data from form fields
        source.title = form.title.data
        source.content = form.content.data
        source.url = form.url.data
        db.session.commit()
        # success
        flash('Your source has been updated!', 'success')
        # redirect to new updated source page
        return redirect(url_for('source', source_id=source.id))
    # the GET method populates the form fields with existing information from the source
    elif request.method == 'GET':
        form.title.data = source.title
        form.content.data = source.content
        form.url.data = source.url
    # render the save source page and pass the form
    return render_template('save_source.html', title='Update Sources',
                           form=form, legend='Update Source')


# delete source route to delete a source from db
@app.route("/source/<int:source_id>/delete", methods=['POST'])
@login_required
def delete_source(source_id):
    # retrieves the source from db
    source = Source.query.get_or_404(source_id)
    # delete the source
    db.session.delete(source)
    db.session.commit()
    # success message
    flash('Your source has been deleted!', 'success')
    # redirect to home page with the updated screen
    return redirect(url_for('home'))


# register route to register new user
@app.route("/register", methods=['GET', 'POST'])
def register():
    # redirect user to home page if user is login
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    # create the registration form object
    form = RegistrationForm()
    # if user input is valid
    if form.validate_on_submit():
        # take user's password and generate a hash
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        # create a user object
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        # save user in db
        db.session.add(user)
        db.session.commit()
        # success message
        flash('Your account has been created! You are now able to log in', 'success')
        # redirect user ot login page
        return redirect(url_for('login'))
    # renders the registration page and pass the form
    return render_template('register.html', title='Register', form=form)


# login route, user has be registered and logged in to use the app's functionality
@app.route("/login", methods=['GET', 'POST'])
def login():
    # if user is logged in user will be redirected to the home page where all their saved sources will be displayed
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    # create a login form object
    form = LoginForm()
    # if input is valid
    if form.validate_on_submit():
        # retrieved the user from db by email
        user = User.query.filter_by(email=form.email.data).first()
        # check the password the user entered in the form against the hashed password stored in db
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            # login user
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            # redirect home page
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            # unsuccessful login message
            flash('Login Unsuccessful. Please Check the email and password', 'danger')
    # render the login template and pass the form
    return render_template('login.html', title='Login', form=form)


# logout route
@app.route("/logout")
def logout():
    # flask_login's logout user function to logout
    logout_user()
    # redirects the user to home, in this case a signup page
    return redirect(url_for('home'))


# function to save a picture to the user's profile
def save_picture(form_picture):
    # picture file name is a string of random_hex and f_ext
    random_hex = secrets.token_hex(8)
    # retrieves the picture path from the user's machine
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    # saves the picture path from user's machine to static/profile pics folder
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    # picture's max out put in the form of a thumbnail
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    # return picture
    return picture_fn


# Account route to update user's account information
@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    # create the update account form
    form = UpdateAccountForm()
    # validate user input
    if form.validate_on_submit():
        # if user updates the profile picture
        if form.picture.data:
            # save picture as a new profile picture
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        # changes current user's info to anything the user enters in the form
        current_user.username = form.username.data
        current_user.email = form.email.data
        # save changes in db
        db.session.commit()
        # success message
        flash('Your account has been updated!', 'success')
        # redirect to the account page and display the changes
        return redirect(url_for('account'))
    # the get method to populate the form with data from the db
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    # return image file from the profile_pics folder
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    # render the account template and pass in the form and image_file
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)


# function to send a reset password email, for when user forgets password
def send_reset_email(user):
    # get user's reset token
    token = user.get_reset_token()
    # create a message object
    msg = Message('Password Reset Request',
                  sender='noreply@gmail.com',
                  recipients=[user.email])
    # message to be sent in the email
    msg.body = f'''To reset your password, visit the following link: 
    {url_for('reset_token', token=token, _external=True)}
    
    If you did not make this request then simply ignore this email and no changes will be made.
    '''
    # sends the message
    mail.send(msg)


# reset password function
@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    # if user is logged in redirect to the homepage
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    # create a request reset form object
    form = RequestResetForm()
    # if user input is valid
    if form.validate_on_submit():
        # retrieve user from db by email
        user = User.query.filter_by(email=form.email.data).first()
        # send the reset email to user
        send_reset_email(user)
        # success message
        flash('An email has been sent with instructions to reset your password.')
    # render reset request page and pass form
    return render_template('reset_request.html', title='Password Reset', form=form)


# reset password route, user recieves the token in the reset mail
@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    # if user is logged in redirect to home page
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    # verify user with token
    user = User.verify_reset_token(token)
    # if the token is expired then redirect user to reset request page
    if user is None:
        flash('This is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    # create a reset password form object
    form = ResetPasswordForm()
    # if user input is valid
    if form.validate_on_submit():
        # create a hashed password from new user password input in the form
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        # save user password as hashed password in db
        user.password = hashed_password
        db.session.commit()
        # success message
        flash('Your password has been updated! You are now able to log in', 'success')
        # redirect to login page
        return redirect(url_for('login'))
    # render reset token page and pass in form
    return render_template('reset_token.html', title='Reset Password', form=form)