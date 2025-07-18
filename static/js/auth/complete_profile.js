const url = new URL(window.location.href);
const uid = url.searchParams.get("uid");

const sqmInput = document.getElementById("sqm");
const rolePreview = document.getElementById("role-preview");
const roleText = document.getElementById("role-text");
const saveBtn = document.getElementById("save-btn");
const timerSpan = document.getElementById("timer");
const waitMsg = document.getElementById("wait-msg");

let remaining = 30;
timerSpan.textContent = remaining;
saveBtn.disabled = true;
const countdown = setInterval(() => {
    remaining -= 1;
    timerSpan.textContent = remaining;
    if (remaining <= 0) {
        clearInterval(countdown);
        saveBtn.disabled = false;
        waitMsg.classList.add("hidden");
    }
}, 1000);

function updateRolePreview() {
    const sqm = parseInt(sqmInput.value, 10);
    if (!isNaN(sqm)) {
        roleText.textContent = sqm === 0 ? "Tenant" : "Landlord";
        rolePreview.classList.remove("hidden");
    } else {
        rolePreview.classList.add("hidden");
    }
}
/*
"""
Determines the displayed role based on entered square meters and shows or
hides the preview accordingly.
"""
*/

sqmInput.addEventListener("input", updateRolePreview);

document.getElementById("save-btn").addEventListener("click", async () => {
    const first_name = document.getElementById("first-name").value.trim();
    const last_name = document.getElementById("last-name").value.trim();
    const sqm = parseInt(sqmInput.value, 10);

    if (!first_name || !last_name || isNaN(sqm) || sqm < 0) {
        show("Please fill in every field correctly");
        return;
    }

    await fetch("/auth/api/complete_profile", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({uid, first_name, last_name, sqm})
    });

    await fetch("/auth/api/set_session", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({uid})
    });

    window.location = "/home";
});

function show(msg) {
    const p = document.getElementById("error");
    p.textContent = msg;
    p.classList.remove("hidden");
}
/*
"""
Displays an error message element with the provided text.
"""
*/
