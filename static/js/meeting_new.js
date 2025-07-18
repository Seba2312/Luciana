const modeSel = document.getElementById('modeSelect')
    const locBlock = document.getElementById('locationBlock')
    const meetInfo = document.getElementById('meetInfo')
    const searchInput = document.getElementById('search_address')
    const formattedIn = document.getElementById('formatted_address')

    function syncMode() {
        const m = modeSel.value
        const needsLoc = (m === 'praesenz' || m === 'hybrid')
        locBlock.classList.toggle('hidden', !needsLoc)
        meetInfo.classList.toggle('hidden', !(m === 'online' || m === 'hybrid'))

        searchInput.required = needsLoc
    }
    /*
    """
    Toggles visibility of location and meeting info inputs based on the
    selected meeting mode and marks the address field as required when needed.
    """
    */

    modeSel.addEventListener('change', syncMode)
    syncMode()

    document.getElementById('newForm').addEventListener('submit', async e => {
        e.preventDefault()

        const m = modeSel.value
        if ((m === 'praesenz' || m === 'hybrid') && !formattedIn.value.trim()) {
            return alert('Please choose an address from the map before saving')
        }

        const payload = Object.fromEntries(new FormData(e.target).entries())
        const r = await fetch('/meeting/api/new', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        })

        if (r.ok) {
            location.href = '/home'
            return
        }

        const msg = (await r.json()).error || 'Unknown error'

        if (r.status === 401 && msg === 'NO_CREDS') {
            alert('Session timed-out – please log-in again to create a Google Meet.')
            window.location = '/logout'
        } else {
            alert('Error creating meeting: ' + msg)
        }
    })
    /*
    """
    Handles creation of a new meeting, validating the form, sending it to the
    server and reacting to errors like missing credentials.
    """
    */
