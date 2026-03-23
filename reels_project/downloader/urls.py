from downloader import views
from django.urls import path
from downloader.views import login_view, register_view, download_reel, logout_view, download_history, delete_reel, forgot_password_view
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

urlpatterns = [
    path('', views.login_view, name='home'),
    path('register/', register_view, name='register'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('login/', views.login_view, name='login'),  
    path('download/', download_reel, name='download'),
    path('history/', download_history, name='history'),
    path('delete/<int:id>/', delete_reel, name='delete_reel'),
    path('delete-reel/<int:id>/', delete_reel, name='delete_reel_alt'),
    path('logout/', logout_view, name='logout'),
    path('forgot-password/', forgot_password_view, name='forgot_password'),
    path('password-reset-done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html', success_url=reverse_lazy('password_reset_complete')), name='password_reset_confirm'),
    path('reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),

    
]