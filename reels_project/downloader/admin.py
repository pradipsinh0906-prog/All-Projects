from django.contrib import admin
from downloader.models import DownloadHistory
import os
from django.conf import settings

@admin.register(DownloadHistory)
class DownloadHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'reel_url', 'download_at', 'has_video')
    list_filter = ('download_at', 'user')
    search_fields = ('user__username', 'reel_url')
    readonly_fields = ('download_at',)
    
    def has_video(self, obj):
        return bool(obj.video_file)
    has_video.boolean = True
    has_video.short_description = 'Has Video'
    
    def delete_model(self, request, obj):
        # Delete the video file when deleting the record
        if obj.video_file:
            file_path = os.path.join(settings.MEDIA_ROOT, obj.video_file.name)
            if os.path.exists(file_path):
                os.remove(file_path)
        super().delete_model(request, obj)

