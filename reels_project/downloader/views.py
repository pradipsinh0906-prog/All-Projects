from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import FileResponse
import instaloader, os, re
from django.contrib import messages
import shutil
from downloader.models import DownloadHistory


def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)

        if user:
            login(request, user)
            return redirect('download')
        else:
            messages.error(request, "Invalid username or password! Please register if you don't have an account.")
            return render(request, 'login.html')

    return render(request, 'login.html')


def register_view(request):
    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {'error': 'Username already exists'})

        User.objects.create_user(username=username, email=email, password=password)
        return redirect('login')

    return render(request, 'register.html')

@login_required(login_url='login')
def download_reel(request):
    if request.method == "POST":
        url = request.POST.get("url")

        try:
            shortcode = re.findall(r"/reel/([^/?]+)", url)
            if not shortcode:
                return render(request, "home.html", {"error": "Invalid Reel URL"})

            shortcode = shortcode[0]

            # Create temp directory for download
            temp_dir = "temp_download"
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            os.mkdir(temp_dir)

            loader = instaloader.Instaloader(
                download_pictures=False,
                download_videos=True,
                save_metadata=False,
                post_metadata_txt_pattern=""
            )

            post = instaloader.Post.from_shortcode(loader.context, shortcode)
            loader.download_post(post, target=temp_dir)

            # Find the downloaded video file
            video_file_path = None
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.endswith(".mp4"):
                        video_file_path = os.path.join(root, file)
                        break
                if video_file_path:
                    break

            if not video_file_path:
                shutil.rmtree(temp_dir)
                return render(request, "home.html", {"error": "Failed to download video"})

            # Create media/reels directory if it doesn't exist
            media_reels_dir = os.path.join("media", "reels")
            if not os.path.exists(media_reels_dir):
                os.makedirs(media_reels_dir)

            # Copy file to media/reels folder with shortcode as filename
            final_filename = f"{shortcode}.mp4"
            final_path = os.path.join(media_reels_dir, final_filename)
            shutil.copy(video_file_path, final_path)

            # Clean up temp directory
            shutil.rmtree(temp_dir)

            # ✅ SAVE HISTORY
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
