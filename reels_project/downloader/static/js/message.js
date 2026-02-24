setTimeout(function() {
    var alerts = document.querySelectorAll(".auto-hide");
    alerts.forEach(function(alertBox) {
        alertBox.style.transition = "opacity 0.5s";
        alertBox.style.opacity = "0";
        setTimeout(function() {
            alertBox.style.display = "none";
        }, 500);
    });
}, 6000);