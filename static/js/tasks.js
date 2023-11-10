let tasks_container = document.getElementById("tasks_container");

let tasks = incoming_tasks;

tasks.forEach((task) => {
    let task_row = document.createElement("tr");
    tasks_container.appendChild(task_row);
    task_row.innerHTML = return_html({
        ID: task["ID"],
        name: task["name"],
        create_date: task["create_date"],
        due_date: task["due_date"],
    });

    if (task["complete"] == "true") {
        checkbox = task_row.querySelector("input[type='checkbox']");
        checkbox.checked = true;
    }

    task_row.addEventListener("click", handleClick);
    /* checkbox_row = document.createElement("td");
    checkbox_input = document.createElement("input");
    checkbox_input. */
});

function return_html({ ID, name, create_date, due_date }) {
    return `
    <td><input type="checkbox" class="form-check-input" disabled></td>
    <td>${name}</td>
    <td>${create_date}</td>
    <td>${due_date}</td>
    <td>
        <div>
            <button id="view_${ID}" type="button" class="btn btn-primary">View</button>
            <button id="edit_${ID}" type="button" class="btn btn-warning">Edit</button>
            <button id="delete_${ID}" type="button" class="btn btn-danger">Delete</button>
        </div>
    </td>
    `;
}

async function handleClick(evt) {
    if (evt.target.id.includes("view")) {
        let task_id = evt.target.id.split("_")[1];
        location.href = `/tasks/${task_id}`;
    } else if (evt.target.id.includes("edit")) {
        let task_id = evt.target.id.split("_")[1];
        location.href = `/tasks/edit/${task_id}`;
    } else if (evt.target.id.includes("delete")) {
        let task_id = evt.target.id.split("_")[1];
        let response = await fetch("/tasks/delete/" + task_id, {
            method: "DELETE",
        });

        if (response.status == 200) {
            location.reload();
            return;
        } else {
            alert("Something went wrong with deleting");
        }
    }
}
