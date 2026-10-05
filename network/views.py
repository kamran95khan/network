from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse

from .models import User, Post, Comment


def index(request):

    if request.method == "POST":

        if not request.user.is_authenticated:
            return HttpResponseRedirect(reverse("login"))

        content = request.POST.get("content", "").strip()

        if content:
            Post.objects.create(
                user=request.user,
                content=content
            )

        return HttpResponseRedirect(reverse("index"))

    posts = Post.objects.all().order_by("-timestamp")

    paginator = Paginator(posts, 10)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    return render(request, "network/index.html", {
        "page_obj": page_obj
    })


def profile(request, username):

    profile_user = get_object_or_404(User, username=username)

    posts = Post.objects.filter(
        user=profile_user
    ).order_by("-timestamp")

    paginator = Paginator(posts, 10)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    is_following = False

    if request.user.is_authenticated:
        is_following = request.user.following.filter(
            id=profile_user.id
        ).exists()

    return render(request, "network/profile.html", {
        "profile_user": profile_user,
        "page_obj": page_obj,
        "is_following": is_following
    })


def follow(request, username):

    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))

    profile_user = get_object_or_404(User, username=username)

    if request.method == "POST" and request.user != profile_user:
        request.user.following.add(profile_user)

    return HttpResponseRedirect(
        reverse("profile", args=[username])
    )


def unfollow(request, username):

    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))

    profile_user = get_object_or_404(User, username=username)

    if request.method == "POST":
        request.user.following.remove(profile_user)

    return HttpResponseRedirect(
        reverse("profile", args=[username])
    )


def following(request):

    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))

    posts = Post.objects.filter(
        user__in=request.user.following.all()
    ).order_by("-timestamp")

    paginator = Paginator(posts, 10)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    return render(request, "network/following.html", {
        "page_obj": page_obj
    })


def edit_post(request, post_id):

    if not request.user.is_authenticated:
        return JsonResponse({
            "error": "Login required."
        }, status=403)

    post = get_object_or_404(Post, id=post_id)

    if request.user != post.user:
        return JsonResponse({
            "error": "You cannot edit this post."
        }, status=403)

    if request.method != "POST":
        return JsonResponse({
            "error": "POST request required."
        }, status=400)

    content = request.POST.get("content", "").strip()

    if not content:
        return JsonResponse({
            "error": "Post cannot be empty."
        }, status=400)

    post.content = content
    post.save()

    return JsonResponse({
        "success": True,
        "content": post.content
    })


def like_post(request, post_id):

    if not request.user.is_authenticated:
        return JsonResponse({
            "error": "Login required."
        }, status=403)

    if request.method != "POST":
        return JsonResponse({
            "error": "POST request required."
        }, status=400)

    post = get_object_or_404(Post, id=post_id)

    if request.user in post.likes.all():

        post.likes.remove(request.user)
        liked = False

    else:

        post.likes.add(request.user)
        liked = True

    return JsonResponse({
        "liked": liked,
        "likes": post.likes.count()
    })


def add_comment(request, post_id):

    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))

    post = get_object_or_404(Post, id=post_id)

    if request.method == "POST":

        content = request.POST.get("content", "").strip()

        if content:
            Comment.objects.create(
                post=post,
                user=request.user,
                content=content
            )

    return HttpResponseRedirect(reverse("index"))


def login_view(request):

    if request.method == "POST":

        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            return HttpResponseRedirect(
                reverse("index")
            )

        return render(
            request,
            "network/login.html",
            {
                "message": "Invalid username and/or password."
            }
        )

    return render(request, "network/login.html")


def logout_view(request):

    logout(request)

    return HttpResponseRedirect(reverse("index"))


def register(request):

    if request.method == "POST":

        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]

        if password != confirmation:

            return render(
                request,
                "network/register.html",
                {
                    "message": "Passwords must match."
                }
            )

        try:

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

            user.save()

        except IntegrityError:

            return render(
                request,
                "network/register.html",
                {
                    "message": "Username already taken."
                }
            )

        login(request, user)

        return HttpResponseRedirect(
            reverse("index")
        )

    return render(request, "network/register.html")
