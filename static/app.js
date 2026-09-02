let selectedOccurrence = null;


// ============================================================
// LOAD DATA
// ============================================================

async function loadData() {
    await loadActiveTasks();
    await loadHistory();
}


// ============================================================
// ACTIVE TASKS
// ============================================================

async function loadActiveTasks() {

    const response = await fetch(
        "/api/occurrences/active"
    );

    const tasks = await response.json();

    const container =
        document.getElementById("activeTasks");

    container.innerHTML = "";


    if (tasks.length === 0) {

        container.innerHTML =
            "<p>No active tasks.</p>";

        return;
    }


    tasks.forEach(task => {

        const div =
            document.createElement("div");

        div.className = "task";


        div.innerHTML = `

            <strong>${task.occurrence_id}</strong>

            <br>

            ${task.result_name}

            <br>

            <small>
                ${new Date(
                    task.created_datetime
                ).toLocaleString()}
            </small>

            <div class="task-actions">

                <button onclick="markNo('${task.occurrence_id}')">
                    No
                </button>

                <button onclick="executeTask('${task.occurrence_id}')">
                    Executed
                </button>

                <button onclick="openPunishment('${task.occurrence_id}')">
                    Punishment
                </button>

            </div>
        `;


        container.appendChild(div);

    });
}


// ============================================================
// HISTORY
// ============================================================

async function loadHistory() {

    const response = await fetch(
        "/api/occurrences/history"
    );

    const history = await response.json();

    const container =
        document.getElementById("history");

    container.innerHTML = "";


    if (history.length === 0) {

        container.innerHTML =
            "<p>No history yet.</p>";

        return;
    }


    history.forEach(item => {

        const div =
            document.createElement("div");

        div.className = "history-item";


        let punishment = "";


        if (item.punishment_type === "Lock Time") {

            punishment =
                ` | Punishment: ${formatTime(
                    item.punishment_days,
                    item.punishment_hours,
                    item.punishment_minutes
                )}`;
        }


        div.innerHTML = `

            <strong>${item.occurrence_id}</strong>

            -

            ${item.result_name}

            -

            ${item.status}

            ${punishment}

            <br>

            <button onclick="undoTask('${item.occurrence_id}')">
                Undo
            </button>
        `;


        container.appendChild(div);

    });
}


// ============================================================
// NO
// ============================================================

function markNo(occurrenceId) {

    alert(
        "The task remains active."
    );
}


// ============================================================
// EXECUTE
// ============================================================

async function executeTask(occurrenceId) {

    const confirmation =
        confirm(
            "Are you sure this task has been executed?"
        );


    if (!confirmation) {
        return;
    }


    const response =
        await fetch(
            `/api/occurrences/${encodeURIComponent(occurrenceId)}/execute`,
            {
                method: "POST"
            }
        );


    if (!response.ok) {

        const result = await response.json();

        alert(result.detail);

        return;
    }


    await loadData();
}


// ============================================================
// UNDO
// ============================================================

async function undoTask(occurrenceId) {

    const confirmation =
        confirm(
            "Undo this execution?"
        );


    if (!confirmation) {
        return;
    }


    const response =
        await fetch(
            `/api/occurrences/${occurrenceId}/undo`,
            {
                method: "POST"
            }
        );


    if (!response.ok) {

        const result = await response.json();

        alert(result.detail);

        return;
    }


    await loadData();
}


// ============================================================
// PUNISHMENT
// ============================================================

function openPunishment(occurrenceId) {

    selectedOccurrence =
        occurrenceId;

    document.getElementById(
        "punishmentModal"
    ).style.display = "flex";
}


function closePunishment() {

    document.getElementById(
        "punishmentModal"
    ).style.display = "none";
}


// ============================================================
// LOCK TIME
// ============================================================

function showLockTime() {

    closePunishment();

    document.getElementById(
        "lockTimeModal"
    ).style.display = "flex";
}


function closeLockTime() {

    document.getElementById(
        "lockTimeModal"
    ).style.display = "none";
}


async function applyLockTime() {

    const data = {

        punishment_type: "Lock Time",

        minimum_days:
            Number(
                document.getElementById(
                    "minDays"
                ).value
            ),

        minimum_hours:
            Number(
                document.getElementById(
                    "minHours"
                ).value
            ),

        minimum_minutes:
            Number(
                document.getElementById(
                    "minMinutes"
                ).value
            ),

        maximum_days:
            Number(
                document.getElementById(
                    "maxDays"
                ).value
            ),

        maximum_hours:
            Number(
                document.getElementById(
                    "maxHours"
                ).value
            ),

        maximum_minutes:
            Number(
                document.getElementById(
                    "maxMinutes"
                ).value
            )
    };


    const response =
        await fetch(
            `/api/occurrences/${selectedOccurrence}/punishment`,
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify(data)
            }
        );


    const result =
        await response.json();


    if (!response.ok) {

        alert(result.detail);

        return;
    }


    alert(
        `Punishment generated:\n\n` +
        `${String(result.days).padStart(2, "0")} days\n` +
        `${String(result.hours).padStart(2, "0")} hours\n` +
        `${String(result.minutes).padStart(2, "0")} minutes`
    );


    closeLockTime();

    await loadData();
}


// ============================================================
// NEW TASK
// ============================================================

async function applyNewTask() {

    const response =
        await fetch(
            `/api/occurrences/${selectedOccurrence}/punishment`,
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    punishment_type:
                        "New Task"
                })
            }
        );


    const result =
        await response.json();


    if (!response.ok) {

        alert(result.detail);

        return;
    }


    closePunishment();

    await loadData();
}


// ============================================================
// TEST EVENT
// ============================================================

async function sendTestEvent() {

    const result =
        document.getElementById(
            "testResult"
        ).value;


    const eventId =
        "TEST-" +
        Date.now();


    const response =
        await fetch(
            "/api/wheel-event",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({

                    event_id: eventId,

                    event_type:
                        "Wheel Spun",

                    result: result,

                    timestamp:
                        new Date().toISOString(),

                    source:
                        "Test"
                })
            }
        );


    const data =
        await response.json();


    console.log(data);


    if (!response.ok) {

        alert(
            data.detail || "Something went wrong."
        );

        return;
    }


    await loadData();
}


// ============================================================
// FORMAT TIME
// ============================================================

function formatTime(
    days,
    hours,
    minutes
) {

    return (
        String(days).padStart(2, "0") +
        "d " +

        String(hours).padStart(2, "0") +
        "h " +

        String(minutes).padStart(2, "0") +
        "m"
    );
}


// ============================================================
// START
// ============================================================

loadData();
