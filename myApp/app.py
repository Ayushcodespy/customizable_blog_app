from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import json
from datetime import datetime
from flask_mail import Mail, Message

with open('config.json', 'r') as c:
    params = json.load(c)["params"]

local_server = True
app = Flask(__name__)

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
    return render_template('index.html', param=params, posts=posts)


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


if __name__ == '__main__':
    app.run(debug=True)
