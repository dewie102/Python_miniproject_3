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

    return redirect(url_for("view_user_tasks"))


@app.route("/tasks")
def view_user_tasks():
    if not session.get("user_id"): #type: ignore
        return redirect(url_for("index"), code=303)

    user_id: int = session["user_id"] # type: ignore
    username: str = session["username"] # type: ignore

    tasks = get_user_tasks(user_id) #type: ignore

    return render_template("tasks.html", tasks = tasks)


@app.route("/tasks/json")
def get_user_tasks_json():
    if not session.get("user_id"): #type: ignore
        return redirect(url_for("index"), code=303)

    user_id: int = session["user_id"] # type: ignore

    tasks = get_user_tasks(user_id) #type: ignore

    return tasks


@app.route("/tasks/<task_id>")
def view_task(task_id: int):
    if not session.get("user_id"): #type: ignore
        return redirect(url_for("index"), code=303)
    
    user_id: int  = session["user_id"] #type: ignore

    task = get_task(task_id, user_id) #type: ignore

    return render_template("view_task.html", task = task)


@app.route("/tasks/create", methods=["GET", "POST"])
def create_task():
    if request.method == "GET":
        return render_template("create.html")
    else:
        if not session.get("user_id"): #type: ignore
            return redirect(url_for("index"), code=303)

        user_id = session["user_id"] #type: ignore
        task_name = request.form.get("task_name")
        due_date = request.form.get("due_date")

        if not user_id:
            return redirect(url_for("index"))

        if not task_name:
            print("No task name provided")
            return redirect(url_for("view_user_tasks"))
  
        if not due_date:
            due_date =\
                (datetime.datetime.now() +\
                datetime.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
        
        # Take the string date and make it a datetime object
        due_date = datetime.datetime.strptime(due_date, "%Y-%m-%dT%H:%M")
        # Take the datetime object and make it a string in the proper format
        due_date = due_date.strftime("%Y-%m-%d %H:%M")
        
        create_task_db({"user_id": user_id, "task_name": task_name, "due_date": due_date})

        return redirect(url_for("view_user_tasks"))


# Have to make this POST for now because html forms only support get and post...
@app.route("/tasks/delete/<task_id>", methods=["DELETE"])
def delete_task(task_id: int):
    delete_task_db(task_id)
    return "{}"
    #return redirect(url_for("view_user_tasks"), code=303)


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
                               '{datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}',
                               '{(datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M")}',
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


def get_task(task_id: int, user_id: int):
    task: Dict[str, str] = {}
    try:
        with sql.connect(database_name) as conn:
            conn.row_factory = sql.Row
            cursor = conn.cursor()

            cursor.execute(f"SELECT * FROM Tasks WHERE ID={task_id} AND user_id={user_id}")
            result = cursor.fetchone()

            task = dict(result)
    except Exception as ex:
        print(f"Something went wrong: {ex}")
    finally:
        return task


def create_task_db(task_dict: dict[str, str]):
    try:
        with sql.connect(database_name) as conn:  
            conn.execute(f'''INSERT INTO Tasks
                               (name, create_date, due_date, complete, user_id) VALUES
                               ('{task_dict["task_name"]}',
                               '{datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}',
                               '{task_dict["due_date"]}',
                               "false",
                               {task_dict["user_id"]});''') 
            conn.commit()
    except Exception as ex:
        print(f"Something went wrong: {ex}")


def delete_task_db(task_id: int):
    try:
        with sql.connect(database_name) as conn:  
            conn.execute(f'''DELETE FROM Tasks
                               WHERE ID={task_id}''') 
            conn.commit()
    except Exception as ex:
        print(f"Something went wrong: {ex}")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=2224, debug=True)