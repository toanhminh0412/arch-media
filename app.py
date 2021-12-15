from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import base64
from base64 import b64encode

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    occupation = db.Column(db.String(200), nullable=False)
    image_data = db.Column(db.LargeBinary, nullable=False)
    image = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return '<UserProfile %r>' % self.name

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
    return render_template("create.html")

@app.route("/", methods=['GET'])
def show_users():
    users = UserProfile.query.all()
    return render_template("homepage.html", users=users)

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
    return render_template('update.html', user=user)
            

if __name__ == "__main__":
    app.run(debug=True)