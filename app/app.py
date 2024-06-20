from os import getenv

from flask import Flask, render_template, url_for, redirect, flash, request
from sqlalchemy import select
from db import Session, Task, User
from sqlalchemy.orm import sessionmaker
from flask_login import current_user, login_required, LoginManager, login_user
from forms import LoginForm, RegisterForm

from datetime import datetime

from dotenv import load_dotenv


load_dotenv()
SECRET_KEY = getenv('SECRET_KEY')
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)



@login_manager.user_loader
def load_user(user_id):
    with Session.begin() as session:
        user = session.scalar(select(User).where(User.id == user_id))
        if user:
            user = User(email=user.email)
            return user



@app.get("/main")
def index():
    context = dict()
    with Session.begin() as session:
        if Task.author is None :
            return redirect(url_for('register'))
        context["tasks"] = session.scalars(select(Task).where(Task.author == current_user.email)).all()
        return render_template("index.html", **context, current_user=current_user)
    


@login_manager.user_loader
def load_user(user_id):
    with Session.begin() as session:
        user = session.scalar(select(User).where(User.id == user_id))
        if user:
            user = User(email=user.email)
            return user


@app.get('/')
def register():
    form = RegisterForm()
    return render_template('form_template.html', form=form)

@app.post('/')
def register_post():
    form = RegisterForm()
    with Session.begin() as session:
        user = session.scalar(select(User).where(User.email == form.email.data))
        if user:
            flash("User exists!")
            return redirect(url_for('register'))
        pwd = form.password.data
        user = User(
            nickname=form.email.data.split('@')[0],
            email=form.email.data,
            password=pwd,
        )
        session.add(user)
        return redirect(url_for('login'))
    return render_template('form_template.html', form=form)

@app.get('/login')
def login():
    form = LoginForm()
    return render_template('form_template.html', form=form)

@app.post('/login')
def login_post():
    form = LoginForm()
    if form.validate_on_submit():
        with Session.begin() as session:
            user = session.query(User).where(User.nickname == form.nickname.data).first()
            if user:
                if user.password == form.password.data:
                    login_user(user)
                    return redirect(url_for("index"))
                flash("Wrong password")
            else:
                flash("Wrong nickname")
    return render_template('form_template.html', form=form)



@app.get('/publish')
@login_required
def get_task():
    return render_template("publish.html") 


@app.post("/publish")
@login_required
def publish_task():
    title = request.form['title']
    content= request.form['content']
    published = datetime.now()
    deadline_str = request.form['deadline']
    author = current_user.email
    done = False

    deadline = datetime.fromisoformat(deadline_str)


    with Session.begin() as session:
        task = Task(title = title, content = content,published = published, deadline = deadline, author = author, done = done)
        session.add(task)
        # session.commit()
        return redirect(url_for('index'))
    


@app.get('/info<int:task_id>')
@login_required
def task_info(task_id):
    with Session.begin() as session:
        task = session.scalars(select(Task).where(Task.id == task_id)).first()
        if task:
            return render_template('info.html', task=task, task_id = task_id)
        else:
            return "Task not found", 403




@app.post('/tasks/<int:task_id>/complete')
@login_required
def complete_task(task_id):
    with Session.begin() as session:
        task = session.scalar(select(Task).where(Task.id == task_id, Task.author == current_user.email))
        if task and not task.done:  
            task.done = True
            session.add(task)
            flash(f"Task '{task.title}' marked as completed!")
            return redirect(url_for('task_info', task_id=task_id))
        flash("Task not found or you don't have permission to complete this task.")
        return redirect(url_for('index'))


@app.get("/tasks/<string:user_email>")
@login_required
def user_completed_tasks(user_email):
    with Session.begin() as session:
        done_tasks = session.scalars(select(Task).where(Task.author == current_user.email, Task.done == True)).all()
        task_lenght = len(done_tasks)
        return render_template("completed_tasks.html", done_tasks=done_tasks, user_email=current_user.email, task_lenght=task_lenght)

                                

if __name__ == "__main__":
    app.run(debug=True)