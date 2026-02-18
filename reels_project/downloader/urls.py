from django.urls import path
from downloader.views import login_view, register_view, download_reel, logout_view, download_history, delete_reel

urlpatterns = [
    path('', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('download/', download_reel, name='download'),
    path('history/', download_history, name='history'),
    path('delete/<int:id>/', delete_reel, name='delete_reel'),
    path('logout/', logout_view, name='logout'),
]