from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
app.config['SECRET_KEY'] ='thisissecret'
db = SQLAlchemy(app)
Bootstrap(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

name_template = ""


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String())

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('remember me')

class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect('/')
        return '<h1>Invalid username or password</h1>'

    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return redirect('/')

    return render_template('signup.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', name=current_user.username)

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(20), nullable=False, default='N/A')
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return 'Blog post ' + str(self.id)

class Marker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(20), nullable=False, default='N/A')
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    longitude = db.Column(db.Float, nullable=False)
    latitude = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return 'Marker:  ' + str(self.id) + " " + str(self.longitude) + ", " + str(self.latitude)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(20), nullable=False, default='N/A')
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return 'Comment_id: ' + str(self.id) + ' parent_id: ' + str(self.parent_id)

@app.route('/')
def hello():
    all_markers = Marker.query.order_by(Marker.date_posted).all()
    global name_template
    if(current_user.is_authenticated):
        name_template=current_user.username
    else:
        name_template=""
    return render_template('index.html', markers=all_markers, name=name_template)

@app.route('/index')
def index():
    return "/index"


@app.route('/posts', methods=['GET', 'POST'])
def posts():

    if request.method == 'POST':
        post_title = request.form['title']
        post_content = request.form['content']
        post_author = request.form['author']
        new_post = BlogPost(title=post_title, content=post_content, author=post_author)
        db.session.add(new_post)
        db.session.commit()
        return redirect('/posts')
    else:
        all_posts = BlogPost.query.order_by(BlogPost.date_posted).all()
        return render_template('posts.html', posts=all_posts)

@app.route('/posts/delete/<int:id>')
def delete(id):
    post = BlogPost.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()
    return redirect('/posts')

@app.route('/posts/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    
    post = BlogPost.query.get_or_404(id)

    if request.method == 'POST':
        post.title = request.form['title']
        post.author = request.form['author']
        post.content = request.form['content']
        db.session.commit()
        return redirect('/')
    else:
        return render_template('edit.html', post=post)




@app.route('/marker/<int:id>', methods=['GET', 'POST'])
def marker_id(id):

    if request.method == 'POST':
        marker_content = request.form['content']
        marker_author = request.form['author']
        new_comment = Comment(content=marker_content, author=marker_author, parent_id=id)
        db.session.add(new_comment)
        db.session.commit()
        return redirect('/marker/' + str(id))
    else:
        required_marker = Marker.query.filter_by(id=id).first()
        releated_comments = Comment.query.filter_by(parent_id=id).all()
        return render_template('marker.html', marker=required_marker, comments = releated_comments)

@app.route('/addmarker/LatLng(<float:lat>&<float:lng>)', methods=['GET', 'POST'])
@login_required
def add_marker(lat, lng):

    if request.method == 'POST':
        marker_title = request.form['title']
        marker_content = request.form['content']
        marker_author = request.form['author']
        marker_longitude = request.form['longitude']
        marker_latitude = request.form['latitude']
        new_marker = Marker(title=marker_title, content=marker_content, author=marker_author,
        longitude=marker_longitude, latitude=marker_latitude)
        db.session.add(new_marker)
        db.session.commit()
        return redirect('/')
    else:
        return render_template('addmarker.html', lat=lat, lng=lng)


@app.route('/markers', methods=['GET', 'POST'])
def markers():

    if request.method == 'POST':
        marker_title = request.form['title']
        marker_content = request.form['content']
        marker_author = request.form['author']
        marker_longitude = request.form['longitude']
        marker_latitude = request.form['latitude']
        new_marker = Marker(title=marker_title, content=marker_content, author=marker_author,
        longitude=marker_longitude, latitude=marker_latitude)
        db.session.add(new_marker)
        db.session.commit()
        return redirect('/markers')
    else:
        all_markers = Marker.query.order_by(Marker.date_posted).all()
        return render_template('markers.html', markers=all_markers)

@app.route('/markers/delete/<int:id>')
def deletemarker(id):
    marker = Marker.query.get_or_404(id)
    db.session.delete(marker)
    db.session.commit()
    return redirect('/markers')

@app.route('/markers/edit/<int:id>', methods=['GET', 'POST'])
def editmarker(id):
    
    marker = Marker.query.get_or_404(id)

    if request.method == 'POST':
        marker.title = request.form['title']
        marker.author = request.form['author']
        marker.content = request.form['content']
        marker.longitude = request.form['longitude']
        marker.latitude = request.form['latitude']
        db.session.commit()
        return redirect('/')
    else:
        return render_template('editmarker.html', marker=marker)

@app.route('/comment/delete/<int:id>')
def deletecomment(id):
    comment = Comment.query.get_or_404(id)
    parent_id = comment.parent_id
    db.session.delete(comment)
    db.session.commit()
    return redirect('/marker/' + str(parent_id))

@app.route('/comment/edit/<int:id>', methods=['GET', 'POST'])
def editcomment(id):
    
    comment = Comment.query.get_or_404(id)

    if request.method == 'POST':
        comment.author = request.form['author']
        comment.content = request.form['content']
        db.session.commit()
        return redirect('/marker/' + str(comment.parent_id))
    else:
        return render_template('editcomment.html', comment=comment)

@app.route('/plot')
def plot():
    global name_template
    return render_template('plot.html', name= name_template)

if __name__ == "__main__":
    app.run(debug=True)