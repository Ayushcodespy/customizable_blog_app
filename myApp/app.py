from flask import Flask, render_template, request, redirect, url_for, session, make_response
from flask_sqlalchemy import SQLAlchemy
import json
from datetime import datetime
from flask_mail import Mail, Message
import math

with open('config.json', 'r') as c:
    params = json.load(c)["params"]

local_server = True
app = Flask(__name__)
app.secret_key = "super-secret-key"

# mail = Mail(app)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'patelayush.satna@gmail.com'
app.config['MAIL_PASSWORD'] = 'jlyw stso gslm vbey'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:@localhost/cleanblog' # before config.json
if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']
db = SQLAlchemy(app)


class Contacts(db.Model):
    __tablename__ = 'contacts'
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(12), nullable=False)
    message = db.Column(db.String(120), nullable=True)
    date = db.Column(db.String(12), nullable=True)


class Post(db.Model):
    __tablename__ = 'posts'
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(25), nullable=False)
    tagline = db.Column(db.String(25), nullable=False)
    content = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(25), nullable=False)
    date = db.Column(db.DateTime, nullable=False)


@app.route('/', methods=['GET'])
def index():  # put application's code here
    posts = Post.query.all()
    # pagination
    last = math.ceil(len(posts) / int(params['no_of_posts']))
    page = request.args.get('page')
    if not str(page).isnumeric():
        page = 1
    page = int(page)
    posts = posts[(page - 1) * int(params['no_of_posts']): (page - 1) * int(params['no_of_posts']) + int(
        params['no_of_posts'])]
    if page == 1:
        prev = "#"
        _next = "/?page=" + str(page + 1)
    elif page == last:
        prev = "/?page=" + str(page - 1)
        _next = "#"
    else:
        prev = "/?page=" + str(page - 1)
        _next = "/?page=" + str(page + 1)

    return render_template('index.html', param=params, posts=posts, prev=prev, next=_next)


@app.route('/about')
def about():
    return render_template('about.html', param=params)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        message = request.form['message']

        entry = Contacts(name=name, email=email, phone=phone, message=message, date=datetime.now())
        db.session.add(entry)
        db.session.commit()

        msg = Message('New message from ' + name, sender='codestech01@gmail.com',
                      recipients=[params['rec_gmail_username']])
        msg.body = message + '\n' + phone
        mail.send(msg)

        # sending email to the user for confirmation mail
        msg_to_user = Message('Thanks for connecting Mr./Mrs. ' + name, sender='codestech01@gmail.com',
                              recipients=[email])
        msg_to_user.body = "Welcome Mr./Mrs. " + name + "\n" "Our team will contact you soon"
        mail.send(msg_to_user)

    return render_template('contact.html', param=params)


@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Post.query.filter_by(slug=post_slug).first()
    return render_template('post.html', param=params, post=post)


@app.route("/admin_login", methods=['GET', 'POST'])
def login():
    if 'user' in session and session['user'] == 'admin':
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['admin_username']
        password = request.form['admin_password']
        if username == "admin" and password == "admin":
            session['user'] = username
            return redirect(url_for('dashboard'))
        else:
            error = "! Invalid username or password"
            return render_template('admin_login.html', error=error)
    return render_template('admin_login.html')


# @app.route("/dashboard")
# def dashboard():
#     posts = Post.query.all()
#     return render_template('dashboard.html', param=params, posts=posts)

@app.route("/dashboard")
def dashboard():
    if 'user' not in session or session['user'] != 'admin':
        return redirect(url_for('login'))

    posts = Post.query.all()
    response = make_response(render_template('dashboard.html', param=params, posts=posts))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

@app.route("/edit/<int:sno>", methods=['GET', 'POST'])
def edit(sno):
    if 'user' in session and session['user'] == 'admin':
        if request.method == 'POST':
            ed_title = request.form['title']
            ed_tagline = request.form['tagline']
            ed_content = request.form['content']
            ed_img_url = request.form['img_url']
            ed_date = datetime.now()
            ed_slug = request.form['slug']

            if sno == 0:
                post = Post(title=ed_title, tagline=ed_tagline, slug=ed_slug, img_url=ed_img_url, content=ed_content,
                            date=ed_date)
                db.session.add(post)
                db.session.commit()
                return redirect(url_for('dashboard'))

            else:
                post = Post.query.filter_by(sno=sno).first()
                post.title = ed_title
                post.tagline = ed_tagline
                post.slug = ed_slug
                post.date = ed_date
                post.img_url = ed_img_url
                post.content = ed_content
                db.session.commit()
                return redirect(url_for('dashboard'))


        post = Post.query.filter_by(sno=sno).first()
        return render_template('edit.html', param=params, post=post, sno=sno)


@app.route("/delete/<int:sno>", methods=['GET', 'POST'])
def delete(sno):
    Post.query.filter_by(sno=sno).delete()
    db.session.commit()
    return redirect(url_for('dashboard'))


@app.route("/admin_logout")
def logout():
    if 'user' in session:
        session.pop('user')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(port=5001, debug=True)
