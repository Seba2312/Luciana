function toggleGift(idx) {
    document.getElementById('gifts-' + idx).classList.toggle('hidden');
}
/*
"""
Expands or collapses the gift details for a member based on their index.
"""
*/

function refresh() {
    location.reload();
}
/*
"""
Reloads the current page to reflect the latest data from the server.
"""
*/

async function makeChair(uid) {
    if (!confirm("Make this user aparment chair?")) return;
    const r = await fetch("/members/api/set_chair", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({uid})
    });
    if (r.ok) {
        location.reload();
    } else {
        alert("Action not permitted (maybe you are not the chair).");
    }
}
/*
"""
Sets the specified user as the apartment chair after confirming and reloads
the page upon success or alerts if not permitted.
"""
*/

async function kickUser(uid) {
    if (!confirm("Remove this user from the apartment?")) return;
    const r = await fetch("/members/api/kick", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({uid})
    });
    if (r.ok) {
        location.reload();
    } else {
        alert("Action failed (see console).");
    }
}
/*
"""
Removes a user from the apartment after confirmation and reloads on success,
otherwise displays an error.
"""
*/

async function resetMine() {
    if (!confirm("Withdraw ALL gifts you have given?")) return;
    await fetch("/members/api/reset_gifts", {method: "POST"});
    location.reload();
}
/*
"""
Withdraws all gifts given by the current user and reloads the page.
"""
*/

const dlg = document.getElementById("giftDialog");
const select = document.getElementById("giftSelect");
const amountI = document.getElementById("giftAmount");

function openGift() {
    dlg.classList.remove("hidden");
}
/*
"""
Opens the gift dialog so the user can send virtual square meters.
"""
*/

function closeGift() {
    dlg.classList.add("hidden");
    amountI.value = "";
}
/*
"""
Closes the gift dialog and clears the amount input field.
"""
*/

async function sendGift() {
    const to = select.value;
    const sqm = parseInt(amountI.value, 10);

    if (!sqm || sqm <= 0) {
        alert("Enter a positive number");
        return;
    }

    const r = await fetch("/members/api/gift", {
        method: "POST", headers: {"Content-Type": "application/json"},
        body: JSON.stringify({to_uid: to, sqm})
    });
    const js = await r.json();
    if (js.success) {
        location.reload();
    } else {
        alert(js.error || "Error");
    }
}
/*
"""
Sends the entered gift amount to another user and reloads if successful,
otherwise shows the returned error message.
"""
*/