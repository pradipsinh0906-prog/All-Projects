from downloader import views
from django.urls import path
from downloader.views import login_view, register_view, download_reel, logout_view, download_history, delete_reel

urlpatterns = [
    path('register/', register_view, name='register'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('', login_view, name='login'),
    path('download/', download_reel, name='download'),
    path('history/', download_history, name='history'),
    path('delete/<int:id>/', delete_reel, name='delete_reel'),
    path('delete-reel/<int:id>/', delete_reel, name='delete_reel_alt'),
    path('logout/', logout_view, name='logout'),
    
]