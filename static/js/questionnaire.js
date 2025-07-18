document.addEventListener('DOMContentLoaded', () => {
    const pwdBlock = document.getElementById('password-block');
    const pwdInput = document.getElementById('pwd-input');
    const pwdBtn = document.getElementById('pwd-btn');
    const pwdErr = document.getElementById('pwd-error');
    const form = document.getElementById('qform');
    const thanks = document.getElementById('thanks');

    pwdBtn.addEventListener('click', () => {
        if (pwdInput.value === 'homes42') {
            pwdBlock.classList.add('hidden');
            form.classList.remove('hidden');
        } else {
            pwdErr.textContent = 'Incorrect password';
        }
    });

    form.addEventListener('submit', e => {
        e.preventDefault();
        const data = new FormData(form);
        fetch('/questionnaire', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(Object.fromEntries(data.entries()))
        }).then(r => r.json()).then(res => {
            if (res.success) {
                form.classList.add('hidden');
                thanks.classList.remove('hidden');
            }
        });
    });
});
/*
"""
Controls access to the questionnaire via a simple password prompt and sends
the filled form to the server, then shows a thank you message on success.
"""
*/

