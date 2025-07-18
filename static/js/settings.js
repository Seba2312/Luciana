let chosen = "{{ user.avatar or '' }}";

document.querySelectorAll("#avatar-grid button").forEach(btn => {
    btn.addEventListener("click", () => {
        document.querySelectorAll("#avatar-grid button")
            .forEach(b => b.classList.remove("ring-gray-800"));
        btn.classList.add("ring-gray-800");
        chosen = btn.dataset.colour;
    });
});

function sendMetric(ev) {
    fetch('/metrics/click', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({event: ev})
    });
}
/*
"""
Sends a click metric to the server for analytics when certain buttons are
interacted with.
"""
*/


document.getElementById("save-btn").addEventListener("click", async () => {
    const body = {
        first_name: document.getElementById("first-name").value.trim(),
        last_name: document.getElementById("last-name").value.trim(),
        sqm: parseInt(document.getElementById("sqm").value, 10),
        avatar: chosen,
    };

    const whereEl = document.getElementById("toggle-where");
    if (whereEl) {
        body.customization = {
            showWhere: whereEl.checked,
            showWhen: document.getElementById("toggle-when").checked,
            showParticipation: document.getElementById("toggle-part").checked,
            showTopics: document.getElementById("toggle-topics").checked,
            showVotingRight: document.getElementById("toggle-votes").checked,
        };
    } else {
        body.customization = null;
    }
    const res = await fetch("/settings/update", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(body)
    }).then(r => r.json());

    const msg = document.getElementById("msg");
    if (res.success) {
        msg.textContent = "Saved ✔";
        msg.className = "text-center text-green-600";
        setTimeout(() => location.reload(), 600);
    } else {
        msg.textContent = res.error || "Error";
        msg.className = "text-center text-red-600";
    }
});

const modal = document.getElementById("delete-modal");
document.getElementById("delete-btn").onclick = () => modal.classList.remove("hidden");
document.getElementById("cancel-del").onclick = () => modal.classList.add("hidden");

document.getElementById("confirm-del").onclick = async () => {
    const val = document.getElementById("confirm-input").value.trim();
    const err = document.getElementById("del-error");
    err.textContent = "";
    if (val !== "DELETE") {
        err.textContent = "You must type DELETE exactly";
        return;
    }
    const res = await fetch("/settings/delete", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({confirmation: val})
    }).then(r => r.json());

    if (res.success) {
        window.location = res.redirect;
    } else {
        err.textContent = res.error || "Deletion failed";
    }
};
/*
"""
Confirms account deletion by verifying the typed word and sending a delete
request; redirects on success or shows an error otherwise.
"""
*/