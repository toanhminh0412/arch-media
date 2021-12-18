from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import base64
from base64 import b64encode
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

class UserProfile(db.Model):
    __tablename__ = 'user_profile'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    occupation = db.Column(db.String(200), nullable=False)
    image_data = db.Column(db.LargeBinary, nullable=False)
    image = db.Column(db.Text, nullable=False)
    status_list = db.relationship('Status', backref='user')

    def __repr__(self):
        return '<UserProfile %r>' % self.name

class Status(db.Model):
    __tablename__ = 'status'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(1000), nullable=False)
    mood = db.Column(db.String(200), nullable = False)
    created_on = db.Column(db.DateTime(), default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user_profile.id'))

    def __repr__(self):
        return '<Status %r>' % self.content

def render_picture(data):
    
    render_pic = base64.b64encode(data).decode('ascii') 
    return render_pic

@app.route("/create-user", methods=['GET', 'POST'])
def create_user():
    if request.method == "POST":
        try:
            user_info = request.form
            file = request.files['image']
            image_data = file.read()
            image = render_picture(image_data)
            new_user = UserProfile(name=user_info['name'], age=user_info['age'], occupation=user_info['occupation'], image_data=image_data, image=image)
            db.session.add(new_user)
            db.session.commit()
            return redirect("/")
        except:
            return "Error trying to add user" + str(file) + str(image_data)
    return render_template("users/create_user.html")

@app.route("/", methods=['GET'])
def show_users():
    users = UserProfile.query.all()
    return render_template("users/homepage.html", users=users)

@app.route('/delete-user/<int:id>')
def delete_user(id):
    delete_user = UserProfile.query.get_or_404(id)
    try:
        db.session.delete(delete_user)
        db.session.commit()
        return redirect("/")
    except:
        return "Error trying to delete the user"

@app.route('/update-user/<int:id>', methods=['GET', 'POST'])
def update_user(id):
    user = UserProfile.query.get_or_404(id)
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
    return render_template('users/update_user.html', user=user)

@app.route('/write-status/<int:user_id>', methods=['GET', 'POST'])
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
    return render_template('status/write_status.html', user=user)
            

@app.route('/status', methods=['GET'])
def show_status():
    status_list = Status.query.all()
    return render_template('status/show_status.html', status_list=status_list)

@app.route('/update-status/<int:status_id>', methods=['GET', 'POST'])
def update_status(status_id):
    status = Status.query.get_or_404(status_id)
    if request.method == "POST":
        try:
            status_updates = request.form
            status.content = status_updates['content']
            status.mood = status_updates['mood']
            db.session.commit()
            return redirect('/status')
        except:
            return 'There was an error updating status'
    return render_template('status/update_status.html', status=status)

@app.route('/delete-status/<int:status_id>')
def delete_status(status_id):
    status = Status.query.get_or_404(status_id)
    try:
        db.session.delete(status)
        db.session.commit()
        return redirect('/status')
    except:
        return "Error trying to delete the status"

if __name__ == "__main__":
    app.run(debug=True)