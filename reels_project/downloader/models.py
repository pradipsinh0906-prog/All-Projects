from django.db import models
from django.contrib.auth.models import User

class DownloadHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reel_url = models.URLField()
    video_file = models.FileField(upload_to="reels/", null=True, blank=True)
    download_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.reel_url}"