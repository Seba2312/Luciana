document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('add-meeting-btn');
    if (btn) {
        btn.addEventListener('click', () => {
            fetch('/metrics/click', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({event: 'add_meeting'})
            });
        });
    }
});
/*
"""
Tracks clicks on the new meeting button by sending a metrics event when the
page is loaded and the button is pressed.
"""
*/
