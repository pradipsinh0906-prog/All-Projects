// Auto-clear input field after successful download

document.addEventListener('DOMContentLoaded', function() {
    const downloadForm = document.getElementById('downloadForm');
    const urlInput = document.getElementById('urlInput');

    if (downloadForm && urlInput) {
        downloadForm.addEventListener('submit', function() {
            // Only clear the input after a short delay to allow form submission
            setTimeout(function() {
                // Check if there's a success (no error message displayed)
                var errorAlert = document.querySelector('.alert-danger');
                if (!errorAlert) {
                    urlInput.value = '';
                }
            }, 500);
        });
    }

    // Also clear input when page reloads and there's no error
    var errorAlert = document.querySelector('.alert-danger');
    if (!errorAlert && urlInput) {
        urlInput.value = '';
    }
});
