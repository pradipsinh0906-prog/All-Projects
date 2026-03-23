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
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
import threading

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

        if password1 != password2:
            messages.error(request, "Passwords do not match!")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists!")
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return redirect('register')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )
        user.is_active = True
        user.save()

        # Generate OTP
        otp = str(random.randint(100000, 999999))

        # Save OTP in DB
        EmailOTP.objects.update_or_create(user=user, defaults={'otp': otp})

        # ✅ Threading thi email moko — server crash nai thase
        def send_otp_email():
            try:
                send_mail(
                    'Your OTP Code - Reels Downloader',
                    f'Your OTP verification code is: {otp}\n\nThis code will expire in 5 minutes.\n\nIf you did not request this, please ignore this email.',
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error sending OTP email to {email}: {str(e)}")

        import threading
        thread = threading.Thread(target=send_otp_email)
        thread.daemon = True
        thread.start()

        request.session['user_id'] = user.id
        messages.success(request, "OTP sent to your email! Check inbox and spam folder.")
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
            # Extract shortcode from URL
            shortcode = re.findall(r"/reel/([^/?]+)|/p/([^/?]+)", url)
            if not shortcode:
                return render(request, "home.html", {"error": "❌ Invalid Instagram URL. Please use a reel or post URL."})
            
            shortcode = shortcode[0][0] or shortcode[0][1]
            
            # Create instaloader instance
            loader = instaloader.Instaloader()
            
            # Create media folder
            media_reels_dir = os.path.join("media", "reels")
            os.makedirs(media_reels_dir, exist_ok=True)
            
            # Download post
            post = instaloader.Post.from_shortcode(loader.context, shortcode)
            
            # Get video URL
            video_url = post.video_url if post.is_video else None
            
            if not video_url:
                return render(request, "home.html", {"error": "❌ This post doesn't contain a video."})
            
            # Download video
            video_response = req_lib.get(video_url, stream=True, timeout=30)
            
            final_filename = f"{shortcode}.mp4"
            final_path = os.path.join(media_reels_dir, final_filename)
            
            with open(final_path, 'wb') as f:
                for chunk in video_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Save to history
            DownloadHistory.objects.create(
                user=request.user,
                reel_url=url,
                video_file=os.path.join("reels", final_filename)
            )
            
            # Return file using proper HttpResponse to avoid caching issues
            with open(final_path, 'rb') as f:
                file_content = f.read()
            
            # Use octet-stream to force download instead of opening
            response = FileResponse(
                file_content,
                as_attachment=True,
                filename=final_filename,
                content_type='application/octet-stream'
            )
            # Force download with additional headers
            response['Content-Disposition'] = f'attachment; filename="{final_filename}"'
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            return response

        except instaloader.exceptions.InstaloaderException as e:
            return render(request, "home.html", {"error": f"❌ Instagram Error: {str(e)}"})
        except req_lib.exceptions.Timeout:
            return render(request, "home.html", {"error": "⏱️ Request timeout. Try again."})
        except req_lib.exceptions.RequestException as e:
            return render(request, "home.html", {"error": f"🌐 Network error: {str(e)}"})
        except Exception as e:
            return render(request, "home.html", {"error": f"❌ Error: {str(e)}"})

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


def forgot_password_view(request):
    """Custom password reset view with better error handling"""
    if request.method == "POST":
        email = request.POST.get('email', '').strip().lower()
        
        if not email:
            messages.error(request, "Please enter an email address.")
            return render(request, 'forgot_password.html')
        
        # Check if user with this email exists (case-insensitive)
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # Show feedback - email not registered
            messages.warning(request, f"No account found with email: {email}. Please check and try again or register a new account.")
            return render(request, 'forgot_password.html')
        
        # Generate token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Build reset URL
        from django.urls import reverse
        reset_url = request.build_absolute_uri(reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token}))
        
        # Prepare email content
        email_subject = "Password Reset Request - Reels Downloader"
        email_body = f"""Hello {user.username},

You requested a password reset for your Reels Downloader account.

Click the link below to set a new password:

{reset_url}

If you did not request this password reset, please ignore this email or let us know immediately.

This link will expire in 1 hour.

Note: Do not reply to this email. This is an automated message.

---
Reels Downloader
"""
        
        # Send email in background thread
        def send_reset_email():
            try:
                send_mail(
                    email_subject,
                    email_body,
                    settings.EMAIL_HOST_USER,
                    [user.email],
                    fail_silently=False,
                )
                print(f"✅ Password reset email sent to {user.email}")
            except Exception as e:
                print(f"❌ Error sending password reset email to {user.email}: {str(e)}")
        
        thread = threading.Thread(target=send_reset_email)
        thread.daemon = True
        thread.start()
        
        # Show success message
        messages.success(request, f"✅ Password reset link has been sent to {user.email}. Please check your inbox (and spam folder).")
        return redirect('password_reset_done')
    
    return render(request, 'forgot_password.html')
