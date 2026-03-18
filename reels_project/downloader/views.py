from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import FileResponse
import instaloader, os, re
from django.contrib import messages
import shutil
from downloader.models import DownloadHistory
from .forms import RegisterForm
from django.utils.safestring import mark_safe
import random
from django.core.mail import send_mail
from django.conf import settings
from .models import EmailOTP
import re
from django.utils import timezone
from datetime import timedelta
import requests as req_lib

def is_strong_password(password):
    if len(password) < 8:
        return False
    if not re.search("[A-Z]", password):
        return False
    if not re.search("[a-z]", password):
        return False
    if not re.search("[0-9]", password):
        return False
    if not re.search("[@#$%^&+=!]", password):
        return False
    return True


def login_view(request):
    
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Username check
        if not User.objects.filter(username=username).exists():
            messages.error(
                request,
                mark_safe('Account not found. <a href="/register/">Register Here</a>')
            )
            return render(request, 'login.html')

        user = authenticate(request, username=username, password=password)

        if user is not None:
                login(request, user)
                return redirect('download')
        else:
                messages.error(request, "Invalid username or password")

    return render(request, 'login.html')


def register_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Password match check
        if password1 != password2:
            messages.error(request, "Passwords do not match!")
            return redirect('register')

        # ✅ CHECK USERNAME
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists!")
            return redirect('register')

        # ✅ CHECK EMAIL
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return redirect('register')

        # ✅ CREATE USER (inactive for OTP)
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )
        user.is_active = True
        user.save()
        
         # 🔥 STEP 3 ADD AHI KARVU 👇👇👇

        # Generate OTP
        otp = str(random.randint(100000, 999999))

        # Save OTP in DB
        EmailOTP.objects.create(user=user, otp=otp)

        # Send Mail
        send_mail(
            'Your OTP Code',
            f'Your OTP is {otp}',
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )

        # Save user id in session
        request.session['user_id'] = user.id

        messages.success(request, "User Created Successfully!")
        return redirect('verify_otp')

    return render(request, 'register.html')
    
def verify_otp(request):
    if request.method == "POST":
        entered_otp = request.POST.get('otp')
        user_id = request.session.get('user_id')

        if not user_id:
            return redirect('register')

        try:
            user = User.objects.get(id=user_id)
            otp_obj = EmailOTP.objects.get(user=user)
        except:
            messages.error(request, "Something went wrong.")
            return redirect('register')

        # OTP expire after 5 minutes
        if timezone.now() > otp_obj.created_at + timedelta(minutes=5):
            otp_obj.delete()
            messages.error(request, "OTP Expired. Register again.")
            return redirect('register')

        if otp_obj.otp == entered_otp:
            user.is_active = True
            user.save()
            otp_obj.delete()
            messages.success(request, "Account Verified Successfully!")
            return redirect('login')
        else:
            messages.error(request, "Invalid OTP")

    return render(request, 'verify_otp.html')

@login_required(login_url='login')
def download_reel(request):
    if request.method == "POST":
        url = request.POST.get("url")

        try:
            # RapidAPI call
            api_url = "https://instagram-reels-downloader-api.p.rapidapi.com/download"
            
            headers = {
                "Content-Type": "application/json",
                "x-rapidapi-host": "instagram-reels-downloader-api.p.rapidapi.com",
                "x-rapidapi-key": os.environ.get('RAPIDAPI_KEY')
            }
            
            response = req_lib.get(api_url, headers=headers, params={"url": url})
            data = response.json()

            # Video URL extract karo
            video_url = None
            if isinstance(data, list) and len(data) > 0:
                video_url = data[0].get('url')
            elif isinstance(data, dict):
                video_url = data.get('url') or data.get('video_url') or data.get('download_url')

            if not video_url:
                return render(request, "home.html", {"error": "Video URL not found in API response"})

            # Video download karo
            video_response = req_lib.get(video_url, stream=True)
            
            # Media folder ma save karo
            shortcode = re.findall(r"/reel/([^/?]+)", url)
            shortcode = shortcode[0] if shortcode else "reel"
            
            media_reels_dir = os.path.join("media", "reels")
            os.makedirs(media_reels_dir, exist_ok=True)
            
            final_filename = f"{shortcode}.mp4"
            final_path = os.path.join(media_reels_dir, final_filename)
            
            with open(final_path, 'wb') as f:
                for chunk in video_response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # History save karo
            DownloadHistory.objects.create(
                user=request.user,
                reel_url=url,
                video_file=os.path.join("reels", final_filename)
            )

            return FileResponse(open(final_path, "rb"), as_attachment=True, filename=final_filename)

        except Exception as e:
            return render(request, "home.html", {"error": f"Error: {str(e)}"})

    return render(request, "home.html")

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
def download_history(request):
    history = DownloadHistory.objects.filter(
        user=request.user
    ).order_by('-download_at')

    return render(request, 'history.html', {'history': history})


@login_required(login_url='login')
def delete_reel(request, id):
    try:
        reel = DownloadHistory.objects.get(id=id, user=request.user)
        
        # Delete the video file if it exists
        if reel.video_file:
            file_path = os.path.join("media", str(reel.video_file))
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # Delete the database record
        reel.delete()
        messages.success(request, "Reel deleted successfully!")
    except DownloadHistory.DoesNotExist:
        messages.error(request, "Reel not found!")
    
    return redirect('history')
