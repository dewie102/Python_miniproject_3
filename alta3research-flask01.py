'''This is the main flask webapp'''
#!/usr/bin/env python3

import os
import sqlite3 as sql
import datetime
from flask import Flask, url_for, request, render_template, redirect, session
from dotenv import load_dotenv
from typing import List, Dict

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

database_name = 'todo.db'

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "default")

    user_dict = get_or_create_user(username)

    if not user_dict:
        return "Something went wrong"

    session["user_id"] = user_dict.get("ID", -1)
    session["username"] = user_dict.get("name", "defaultuser")

    return redirect(url_for("get_tasks"))

@app.route("/tasks")
def get_tasks():
    user_id: int = session["user_id"] # type: ignore
    username: str = session["username"] # type: ignore

    tasks = get_user_tasks(user_id) #type: ignore

    return render_template("tasks.html", tasks = tasks)


@app.route("/tasks/<task_id>")
def view_task(task_id: int):

    task = get_task(task_id)

    return render_template("view_task.html", task = task)

@app.route("/tasks/create")
def create_task():
    return "Creating task"

@app.route("/tasks/delete/<number>")
def delete_task(number: int):
    return "Deleting task"


def get_or_create_user(username: str):
    try:
        with sql.connect(database_name) as conn:
            conn.row_factory = sql.Row
            cursor = conn.cursor()

            cursor.execute(f"SELECT * FROM Users WHERE name='{username}'")

            results = cursor.fetchall()

            if len(results) > 0:
                return dict(results[0])
            else:
                # Create a new user
                cursor.execute(f"INSERT INTO Users (name) VALUES ('{username}')")
                # Commit it to the DB
                conn.commit()
                # Get the new user
                cursor.execute(f"SELECT * FROM Users WHERE name='{username}'")
                rows = cursor.fetchall()
                # Change the row into python dict
                new_user = dict(rows[0])
                # Create a new "default" task for show
                cmd: str = f'''INSERT INTO Tasks
                               (name, create_date, due_date, complete, user_id) VALUES
                               ("DEFAULT TASK",
                               '{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                               '{(datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")}',
                               "false",
                               {new_user["ID"]})'''
                
                cursor.execute(cmd)
                
                # Commit it to the DB
                conn.commit()

                return new_user
    except Exception as ex:
        print(f"There was an error: {ex}")
        

def get_user_tasks(user_id: int) -> List[Dict[str, str]]:
    tasks: List[Dict[str, str]] = []

    try:
        with sql.connect(database_name) as conn:
            conn.row_factory = sql.Row
            cursor = conn.cursor()

            cursor.execute(f"SELECT * FROM Tasks WHERE user_id = {user_id}")
            results = cursor.fetchall()

            for data in results:
                task = dict(data)
                tasks.append(task)
    except Exception as ex:
        print(f"Something went wrong: {ex}")
    finally:
        return tasks


def get_task(task_id):
    task: Dict[str, str] = {}
    try:
        with sql.connect(database_name) as conn:
            conn.row_factory = sql.Row
            cursor = conn.cursor()

            cursor.execute(f"SELECT * FROM Tasks WHERE ID={task_id}")
            result = cursor.fetchone()

            task = dict(result)
    except Exception as ex:
        print(f"Something went wrong: {ex}")
    finally:
        return task



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=2224, debug=True)