const startTime = Date.now();

function sendMetrics(payload) {
    navigator.sendBeacon('/metrics/click', JSON.stringify(payload));
}
/*
"""
Uses the Beacon API to asynchronously send interaction metrics to the server.
"""
*/

window.addEventListener('beforeunload', () => {
    const duration = Date.now() - startTime;
    sendMetrics({event: 'time_on_page', page: window.location.pathname, duration});
});
/*
"""
On page unload, calculates how long the user stayed and sends that duration
as a metric to the server.
"""
*/

document.addEventListener('click', (e) => {
    const target = e.target.closest('button, a');
    if (!target) return;
    const label = target.id || target.getAttribute('href') || target.textContent.trim().slice(0, 20);
    sendMetrics({event: 'click', page: window.location.pathname, label});
});
/*
"""
Captures button and link clicks, extracts a label and reports the event for
analytics purposes.
"""
*/
