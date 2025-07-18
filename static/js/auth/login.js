async function postJson(url, data) {
    const resp = await fetch(url, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(data)
    });
    return resp.ok ? resp.json() : Promise.reject(await resp.json());
}
/*
"""
Sends a POST request with JSON data and returns the parsed response or a
rejected promise on failure.
"""
*/

async function init() {

    const cfg = await fetch("/auth/firebase-config").then(r => r.json());
    firebase.initializeApp(cfg);

    const provider = new firebase.auth.GoogleAuthProvider();
    provider.setCustomParameters({prompt: "select_account"});
    provider.addScope("https://www.googleapis.com/auth/calendar.events");

    document.getElementById("google-btn").addEventListener("click", async () => {

        try {
            const {credential, user} = await firebase.auth()
                .signInWithPopup(provider);

            const accessToken = credential.accessToken;
            const expiresIn = 3600;

            await postJson("/auth/api/add_user", {
                uid: user.uid,
                email: user.email,
                access_token: accessToken,
                expires_in: expiresIn
            });

            await postJson("/auth/api/set_session", {uid: user.uid});

            const status = await postJson("/auth/api/user_status", {uid: user.uid});

            if (status.missing_info) {
                window.location = `/auth/complete_profile?uid=${user.uid}`;
                return;
            }

            window.location = "/home";

        } catch (err) {
            const p = document.getElementById("error");
            p.textContent = err.message || err.error || "Unknown error";
            p.classList.remove("hidden");
        }
    });
}
/*
"""
Initializes Firebase and handles the Google login flow, including session
setup and profile completion redirect.
"""
*/

init();