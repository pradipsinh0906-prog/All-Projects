from django.urls import path
from downloader.views import login_view, register_view, download_reel, logout_view

urlpatterns = [
    path('', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('download/', download_reel, name='download'),
    path('logout/', logout_view, name='logout'),
]