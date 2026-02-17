from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import FileResponse
import instaloader, os, re
from django.contrib import messages


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

        shortcode = re.findall(r"/reel/([^/?]+)", url)
        if not shortcode:
            return render(request, "index.html", {"error": "Invalid Reel URL"})

        shortcode = shortcode[0]

        loader = instaloader.Instaloader(
            download_pictures=False,
            download_videos=True,
            save_metadata=False,
            post_metadata_txt_pattern=""
        )

        post = instaloader.Post.from_shortcode(loader.context, shortcode)
        loader.download_post(post, target="media")

        for file in os.listdir("media"):
            if file.endswith(".mp4"):
                return FileResponse(open(f"media/{file}", "rb"), as_attachment=True)

    return render(request, "index.html")


def logout_view(request):
    logout(request)
    return redirect('login')
