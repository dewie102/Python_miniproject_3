#!/usr/bin/env python3

import sqlite3
from sqlite3 import Connection


def drop_db(conn: Connection):
    conn.execute('DROP TABLE IF EXISTS Users')
    conn.execute('DROP TABLE IF EXISTS Tasks')
    conn.execute('DROP TABLE IF EXISTS Sub_Tasks')

    print("Dropped any available talbes")
    conn.commit()


def create_db(conn: Connection):
    # Create the User table
    conn.execute('''CREATE TABLE IF NOT EXISTS Users
	(ID     INTEGER NOT NULL    UNIQUE,
	name    TEXT    NOT NULL,
    PRIMARY KEY (ID AUTOINCREMENT));''')

    # Create the Task Table
    conn.execute('''CREATE TABLE IF NOT EXISTS Tasks
	(ID         INTEGER     NOT NULL    UNIQUE,
	name		TEXT        NOT NULL,
	create_date	DATETIME    NOT NULL,
	due_date	DATETIME,
	complete	BOOLEAN,
	user_id 	INT 		NOT NULL,
    PRIMARY KEY (ID AUTOINCREMENT),
	FOREIGN KEY (user_id) REFERENCES Users (id));''')

    # Create the Subtask Table
    conn.execute('''CREATE TABLE IF NOT EXISTS Sub_Tasks
	(ID         INTEGER 	NOT NULL    UNIQUE,
	name		TEXT		NOT NULL,
	create_date	DATETIME	NOT NULL,
	due_date	DATETIME,
	complete	BOOLEAN,
	task_id 	INT 		NOT NULL,
    PRIMARY KEY (ID AUTOINCREMENT),
	FOREIGN KEY (task_id) REFERENCES Tasks (id));''')


if __name__ == "__main__":
    conn: Connection = sqlite3.connect('todo.db')
    print("Opened the database successfully!")

    drop_db(conn)
    create_db(conn)

    conn.close()