// History Page JavaScript Functions

// Hide play button when video plays
document.addEventListener('DOMContentLoaded', function() {
    const videos = document.querySelectorAll('.video-player');
    
    videos.forEach((video, index) => {
        const playButtonOverlay = video.closest('.position-relative').querySelector('.play-button-overlay');
        
        if (!playButtonOverlay) return;
        
        // Play video when clicking on the overlay button
        playButtonOverlay.addEventListener('click', function(e) {
            if (e.target.closest('.video-overlay')) return;
            e.preventDefault();
            e.stopPropagation();
            if (video.paused) {
                video.play();
            }
        });
        
        // Pause/Play when clicking on video itself
        video.addEventListener('click', function(e) {
            if (video.paused) {
                video.play();
            } else {
                video.pause();
            }
        });
        
        // Double-click on video to toggle fullscreen
        video.addEventListener('dblclick', function(e) {
            e.stopPropagation();
            e.preventDefault();
        });
        
        // Hide play button when video plays
        video.addEventListener('play', function() {
            playButtonOverlay.style.opacity = '0';
            playButtonOverlay.style.pointerEvents = 'none';
        }, false);
        
        // Show play button when video pauses
        video.addEventListener('pause', function() {
            playButtonOverlay.style.opacity = '1';
            playButtonOverlay.style.pointerEvents = 'auto';
        }, false);
        
        // Show play button when video ends
        video.addEventListener('ended', function() {
            video.currentTime = 0;
            playButtonOverlay.style.opacity = '1';
            playButtonOverlay.style.pointerEvents = 'auto';
        }, false);
    });
});

function deleteReel(id) {
    if (confirm('Confirm delete this reel?')) {
        // Create a form and send POST request
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/delete/${id}/`;
        
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
