import requests

url="http://127.0.0.1:2224"

username = input("Please enter username: ").strip()

session = requests.session()

login = session.post(f"{url}/login", data={"username": username})

data = session.get(f"{url}/tasks/json")

tasks = data.json()

for task in tasks:
    print(f"Task: {task['name']}")
    print(f"\tDue Date: {task['due_date']}")
    print(f"\tCreated On: {task['create_date']}")
    print(f"\tComplete?: {task['complete']}")
    print(f"\tTask ID: {task['ID']}")
    print()

#print(data)