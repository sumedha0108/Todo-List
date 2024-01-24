from flask import Flask, render_template, request, url_for, redirect, flash
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from sqlalchemy.orm import relationship
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_KEY')
Bootstrap5(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///posts.db")
db = SQLAlchemy()
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    todos = relationship('Todo', back_populates='user')


class Todo(db.Model):
    __tablename__ = "todo"
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='todo')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = relationship('User', back_populates='todos')


with app.app_context():
    db.create_all()


@app.route('/')
def home():
    return render_template('index.html', logged_in=current_user.is_authenticated)


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        data = request.form
        email = request.form.get('email')
        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()
        if user:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))
        new_user = User(
            email=data['email'],
            password=generate_password_hash(data['password'], method='pbkdf2:sha256', salt_length=8),
            name=data['name']
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('todolist'))

    return render_template("register.html", logged_in=current_user.is_authenticated)


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        # Find user by email entered.
        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()

        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Wrong password')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('todolist'))

    return render_template("login.html", logged_in=current_user.is_authenticated)


@app.route('/new-todo', methods=['POST'])
@login_required
def add_todo():
    todo_content = request.form.get('new_todo')
    new_todo = Todo(content=todo_content, user=current_user)
    db.session.add(new_todo)
    db.session.commit()
    flash('New Todo added successfully!')
    return redirect(url_for('todolist'))

@app.route('/update_todos', methods=['POST'])
def update_todos():
    for todo in current_user.todos:
        todo.status = request.form.get(f'status_{todo.id}')
        db.session.commit()

    flash("Todos updated successfully")
    return redirect(url_for('todolist'))

@app.route('/edit-task/<int:todo_id>', methods=['POST', 'GET'])
def edit_todo(todo_id):
    todo_to_update = db.get_or_404(Todo, todo_id)
    if request.method == 'POST':
        to_update = request.form.get('edited-todo')
        todo_to_update.content = to_update
        db.session.commit()
        return redirect(url_for('todolist'))
    return render_template('edit_todo.html', todo=todo_to_update)

@app.route('/makelist')
@login_required
def todolist():
    return render_template('makelist.html', todos=current_user.todos, logged_in=current_user.is_authenticated)

@app.route("/delete/<int:todo_id>")
def delete_todo(todo_id):
    todo_to_delete = db.get_or_404(Todo, todo_id)
    db.session.delete(todo_to_delete)
    db.session.commit()
    return redirect(url_for('todolist'))


@app.route('/logout')
def logout():
    logout_user()
    return render_template('index.html')



if __name__ == '__main__':
    app.run(debug=True)
