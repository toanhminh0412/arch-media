from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_manager, login_user, login_required, current_user, logout_user
import base64
from base64 import b64encode
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'toanhminh04122001'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

class Owner(UserMixin, db.Model):
    __tablename__ = 'owner'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(1000), nullable=False)
    user_profiles = db.relationship('UserProfile', backref='owner')

    def __repr__(self):
        return '<Owner %r>' % self.email

# Each User can have multiple UserProfiles, this allows them to appear with different indetities on the social media
class UserProfile(db.Model):
    __tablename__ = 'user_profile'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    occupation = db.Column(db.String(200), nullable=False)
    image_data = db.Column(db.LargeBinary, nullable=False)
    image = db.Column(db.Text, nullable=False)
    status_list = db.relationship('Status', backref='user')
    owner_id = db.Column(db.Integer, db.ForeignKey('owner.id'))

    def __repr__(self):
        return '<UserProfile %r>' % self.name

# Each UserProfile can write their own status. This allows User to post status under multiple indentities
class Status(db.Model):
    __tablename__ = 'status'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(1000), nullable=False)
    mood = db.Column(db.String(200), nullable = False)
    created_on = db.Column(db.DateTime(), default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user_profile.id'))

    def __repr__(self):
        return '<Status %r>' % self.content

@login_manager.user_loader
def load_user(owner_id):
# since the user_id is just the primary key of our user table, use it in the query for the user
    return Owner.query.get(int(owner_id))

def render_picture(data):
    
    render_pic = base64.b64encode(data).decode('ascii') 
    return render_pic

# Authentication process 
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        check_owner = Owner.query.filter_by(email=request.form['email']).first()
        if check_owner:
            return render_template('owners/signup.html', message="Email already exists, try login")
        
        try:
            # create a new owner with the form data. Hash the password
            new_owner = Owner(email=request.form['email'], password=generate_password_hash(request.form['password'], method='sha256'), name=request.form['name'])

            # add the new owner to database
            db.session.add(new_owner)
            db.session.commit()
            return redirect('/login')
        except:
            return 'Error trying to add new owner'

    return render_template('owners/signup.html', message="")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        try:
            # Get the owner information based on input email and check if the 
            owner = Owner.query.filter_by(email=request.form['email']).first()
            
            if not owner or not check_password_hash(owner.password, request.form['password']):
                return render_template('owners/login.html', message='Please check your login details and try again')

            # if the above check passes, then we know the user has the right credentials
            login_user(owner, remember=True)
            return redirect('/')
        except:
            return 'There was an error in login process'

    return render_template('owners/login.html', message="")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

# Interacting with user profiles for each Owner
@app.route("/create-user", methods=['GET', 'POST'])
def create_user():
    if request.method == "POST":
        try:
            user_info = request.form
            file = request.files['image']
            image_data = file.read()
            image = render_picture(image_data)
            new_user = UserProfile(name=user_info['name'], age=user_info['age'], occupation=user_info['occupation'], image_data=image_data, image=image)
            new_user.owner = current_user
            db.session.add(new_user)
            db.session.commit()
            return redirect("/")
        except:
            return "Error trying to add user" + str(file) + str(image_data)
    return render_template("users/create_user.html")

@app.route("/", methods=['GET'])
@login_required
def show_users():
    users = UserProfile.query.filter_by(owner=current_user).all()
    return render_template("users/homepage.html", users=users, name=current_user.name)

@app.route("/user-details/<int:user_id>", methods=['GET'])
@login_required
def user_details(user_id):
    user = UserProfile.query.get_or_404(user_id)
    return render_template("users/user_details.html", user=user, name=current_user.name)

@app.route('/delete-user/<int:id>')
@login_required
def delete_user(id):
    delete_user = UserProfile.query.get_or_404(id)
    if delete_user.owner != current_user:
        return redirect('/')
    # Delete all status that are related to this user
    user_status_list = delete_user.status_list
    try:
        for status in user_status_list:
            db.session.delete(status)
            db.session.commit()
        db.session.delete(delete_user)
        db.session.commit()
        return redirect("/")
    except:
        return "Error trying to delete the user"

@app.route('/update-user/<int:id>', methods=['GET', 'POST'])
@login_required
def update_user(id):
    user = UserProfile.query.get_or_404(id)
    if user.owner != current_user:
        return redirect('/')

    if request.method == "POST":
        try:
            user.name = request.form['name']
            user.age = request.form['age']
            user.occupation = request.form['occupation']
            if 'image' in request.files.keys() != 0:
                user.image_data = request.files['image'].read()
                user.image = render_picture(user.image_data)
            db.session.commit()
            return redirect('/')
        except:
            return 'There was an error updating the user'
    return render_template('users/update_user.html', user=user, name=current_user.name)

# interacting with status for each UserProfile
@app.route('/write-status/<int:user_id>', methods=['GET', 'POST'])
@login_required
def write_status(user_id):
    user = UserProfile.query.get_or_404(user_id)
    if request.method == "POST":
        try:
            status_data = request.form
            new_status = Status(content=status_data['content'], mood=status_data['mood'], user=user)
            db.session.add(new_status)
            db.session.commit()
            return redirect('/status')
        except:
            return 'There was an error writing status'
    return render_template('status/write_status.html', user=user, name=current_user.name)
            

@app.route('/status', methods=['GET'])
@login_required
def show_status():
    status_list = Status.query.all()
    return render_template('status/show_status.html', status_list=status_list, name=current_user.name)

@app.route('/update-status/<int:status_id>', methods=['GET', 'POST'])
@login_required
def update_status(status_id):
    status = Status.query.get_or_404(status_id)
    if status.user.owner != current_user:
        redirect('/status')
    if request.method == "POST":
        try:
            status_updates = request.form
            status.content = status_updates['content']
            status.mood = status_updates['mood']
            db.session.commit()
            return redirect('/status')
        except:
            return 'There was an error updating status'
    return render_template('status/update_status.html', status=status, name=current_user.name)

@app.route('/delete-status/<int:status_id>')
@login_required
def delete_status(status_id):
    status = Status.query.get_or_404(status_id)
    if status.user.owner != current_user:
        redirect('/status')
    try:
        db.session.delete(status)
        db.session.commit()
        return redirect('/status')
    except:
        return "Error trying to delete the status"

if __name__ == "__main__":
    app.run(debug=True)