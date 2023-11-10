'''This is the main flask webapp'''
#!/usr/bin/env python3

import os
import sqlite3 as sql
import datetime
from typing import List, Dict
from flask import Flask, url_for, request, render_template, redirect, session
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

DATABASE = os.environ.get("DATABASE", "todo.db")


DATETIME_DB_FORMAT = "%Y-%m-%d %H:%M"
DATETIME_FORM_FORMAT = "%Y-%m-%dT%H:%M"

@app.route("/")
def index():
    """This is the login page, if already logged in redirects to viewing tasks"""
    if session.get("user_id"):  # type: ignore
        return redirect(url_for("view_user_tasks"), code=303)

    return render_template("index.html")


@app.route("/login", methods=["POST"])
def login():
    """This is the method to handle posts routes to log in"""
    username = request.form.get("username", "default")

    user_dict = get_or_create_user(username)

    if not user_dict:
        return "Something went wrong"

    session["user_id"] = user_dict.get("ID", -1)
    session["username"] = user_dict.get("name", "defaultuser")

    return redirect(url_for("view_user_tasks"))


@app.route("/tasks")
def view_user_tasks():
    """Method to handle viewing all tasks for a specific user"""
    if not session.get("user_id"):  # type: ignore
        return redirect(url_for("index"), code=303)

    user_id: int = session["user_id"]  # type: ignore

    tasks = get_user_tasks(user_id)  # type: ignore

    return render_template("tasks.html", tasks=tasks)


@app.route("/tasks/json")
def get_user_tasks_json():
    """Get all the tasks for a specific user but returned as JSON"""
    if not session.get("user_id"):  # type: ignore
        return redirect(url_for("index"), code=303)

    user_id: int = session["user_id"]  # type: ignore

    tasks = get_user_tasks(user_id)  # type: ignore

    return tasks


@app.route("/tasks/<task_id>")
def view_task(task_id: int):
    """View a specific task by it's ID as long as you are the right user"""
    if not session.get("user_id"):  # type: ignore
        return redirect(url_for("index"), code=303)

    user_id: int = session["user_id"]  # type: ignore

    task = get_task(task_id, user_id)  # type: ignore

    return render_template("view_task.html", task=task)


@app.route("/tasks/edit/<task_id>", methods=["GET", "POST"])
def edit_task(task_id: int):
    """Edit a specific task, done only if you are the correct user"""
    if not session.get("user_id"):  # type: ignore
        return redirect(url_for("index"), code=303)

    user_id: int = session["user_id"]  # type: ignore
    task = get_task(task_id, user_id)  # type: ignore

    if request.method == "GET":
        return render_template("edit_task.html", task=task)
    else:
        user_id: int = session["user_id"]  # type: ignore
        task_user_id: str | None = request.form.get("task_user_id")

        if str(user_id) != task_user_id: # type: ignore
            return redirect(url_for("index"), code=303)

        # Getting all the information from form
        task_name = request.form.get("task_name")
        due_date = request.form.get("due_date")
        complete = request.form.get("complete")

        if complete == 'on':
            complete = True
        else:
            complete = False

        if not due_date:
            due_date = task["due_date"]            

        # Take the string date and make it a datetime object
        due_date = datetime.datetime.strptime(
            due_date, DATETIME_FORM_FORMAT).strftime(DATETIME_DB_FORMAT)

        update_task({"task_id": task_id, "task_name": task_name,
                    "due_date": due_date, "complete": complete})

        return redirect(url_for("index"), code=303)


@app.route("/tasks/create", methods=["GET", "POST"])
def create_task():
    """Create a task, either get the form or post to actually create it"""
    if request.method == "GET":
        return render_template("create.html")
    else:
        if not session.get("user_id"):  # type: ignore
            return redirect(url_for("index"), code=303)

        user_id = session["user_id"]  # type: ignore
        task_name = request.form.get("task_name")
        due_date = request.form.get("due_date")

        if not user_id:
            return redirect(url_for("index"))

        if not task_name:
            print("No task name provided")
            return redirect(url_for("view_user_tasks"))

        if not due_date:
            due_date =\
                (datetime.datetime.now() +
                 datetime.timedelta(days=1)).strftime(DATETIME_FORM_FORMAT)

        # Take the string date and make it a datetime object
        due_date = datetime.datetime.strptime(due_date, DATETIME_FORM_FORMAT)
        # Take the datetime object and make it a string in the proper format
        due_date = due_date.strftime(DATETIME_DB_FORMAT)

        create_task_db(
            {"user_id": user_id, "task_name": task_name, "due_date": due_date})

        return redirect(url_for("view_user_tasks"))


# Have to make this POST for now because html forms only support get and post...
@app.route("/tasks/delete/<task_id>", methods=["DELETE"])
def delete_task(task_id: int):
    """Quick method to delete a task"""
    delete_task_db(task_id)
    return "{}"
    # return redirect(url_for("view_user_tasks"), code=303)


@app.route("/signout")
def signout():
    """Simple logout by deleting the session and redirecting to index"""
    session.clear()
    return redirect(url_for("index"))


def get_or_create_user(username: str):
    """Method to get a user from the DB and if they do not exist, create them with 1 default task"""
    try:
        with sql.connect(DATABASE) as conn:
            conn.row_factory = sql.Row
            cursor = conn.cursor()

            cursor.execute(f"SELECT * FROM Users WHERE name='{username}'")

            results = cursor.fetchall()

            if len(results) > 0:
                return dict(results[0])
            else:
                # Create a new user
                cursor.execute(
                    f"INSERT INTO Users (name) VALUES ('{username}')")
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
                               '{datetime.datetime.now().strftime(DATETIME_DB_FORMAT)}',
                               '{(datetime.datetime.now() + datetime.timedelta(days=1)).strftime(DATETIME_DB_FORMAT)}',
                               "false",
                               {new_user["ID"]})'''

                cursor.execute(cmd)

                # Commit it to the DB
                conn.commit()

                return new_user
    except Exception as ex: # pylint: disable=broad-except
        print(f"There was an error: {ex}")


def get_user_tasks(user_id: int) -> List[Dict[str, str]]:
    """Method to get all the tasks using the user_id"""
    tasks: List[Dict[str, str]] = []

    try:
        with sql.connect(DATABASE) as conn:
            conn.row_factory = sql.Row
            cursor = conn.cursor()

            cursor.execute(f"SELECT * FROM Tasks WHERE user_id = {user_id}")
            results = cursor.fetchall()

            for data in results:
                task = dict(data)
                tasks.append(task)
    except Exception as ex: # pylint: disable=broad-except
        print(f"Something went wrong: {ex}")
    finally:
        return tasks # pylint: disable=return-in-finally, lost-exception


def get_task(task_id: int, user_id: int):
    """Method to get one task as long as the right user is requesting it"""
    task: Dict[str, str] = {}
    try:
        with sql.connect(DATABASE) as conn:
            conn.row_factory = sql.Row
            cursor = conn.cursor()

            cursor.execute(
                f"SELECT * FROM Tasks WHERE ID={task_id} AND user_id={user_id}")
            result = cursor.fetchone()

            task = dict(result)
    except Exception as ex: # pylint: disable=broad-except
        print(f"Something went wrong: {ex}")
    finally:
        return task # pylint: disable=return-in-finally, lost-exception


def create_task_db(task_dict: dict[str, str]):
    """Method to create a task in the database"""
    try:
        with sql.connect(DATABASE) as conn:
            conn.execute(f'''INSERT INTO Tasks
                               (name, create_date, due_date, complete, user_id) VALUES
                               ('{task_dict["task_name"]}',
                               '{datetime.datetime.now().strftime(DATETIME_DB_FORMAT)}',
                               '{task_dict["due_date"]}',
                               "false",
                               {task_dict["user_id"]});''')
            conn.commit()
    except Exception as ex: # pylint: disable=broad-except
        print(f"Something went wrong: {ex}")


def delete_task_db(task_id: int):
    """Method to delete a task in the database"""
    try:
        with sql.connect(DATABASE) as conn:
            conn.execute(f'''DELETE FROM Tasks
                               WHERE ID={task_id}''')
            conn.commit()
    except Exception as ex: # pylint: disable=broad-except
        print(f"Something went wrong: {ex}")


def update_task(task_dict: dict[str, int | str | bool | None]):
    """Method to update a task in the database"""
    try:
        with sql.connect(DATABASE) as conn:
            conn.execute(f'''UPDATE Tasks
                            SET name = '{task_dict["task_name"]}',
                            due_date ='{task_dict["due_date"]}',
                            complete = '{task_dict["complete"]}'
                            WHERE
                            ID={task_dict["task_id"]};''')
            conn.commit()
    except Exception as ex: # pylint: disable=broad-except
        print(f"Something went wrong: {ex}")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=2224, debug=True)
