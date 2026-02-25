// History Page JavaScript Functions

function deleteReel(id) {
    if (confirm('Confirm delete this reel?')) {
        // Create a form and send POST request
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/delete-reel/${id}/`;
        
        const csrfTokenInput = document.createElement('input');
        csrfTokenInput.type = 'hidden';
        csrfTokenInput.name = 'csrfmiddlewaretoken';
        csrfTokenInput.value = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                                getCookie('csrftoken');
        
        form.appendChild(csrfTokenInput);
        document.body.appendChild(form);
        form.submit();
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
