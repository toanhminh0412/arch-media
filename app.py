from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    occupation = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return '<UserProfile %r>' % self.name

@app.route("/create-user", methods=['GET', 'POST'])
def create_user():
    if request.method == "POST":
        try:
            user_info = request.form
            new_user = UserProfile(name=user_info['name'], age=user_info['age'], occupation=user_info['occupation'])
            db.session.add(new_user)
            db.session.commit()
            # return render_template("create.html")
            return redirect("/")
        except:
            return "Error trying to add user"
    return render_template("create.html")

@app.route("/", methods=['GET'])
def show_users():
    users = UserProfile.query.all()
    return render_template("homepage.html", users=users)

if __name__ == "__main__":
    app.run(debug=True)