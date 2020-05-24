from django.shortcuts import render,HttpResponse,get_object_or_404,HttpResponseRedirect
from .models import PostCategory,Thread,Comment
from django.contrib import messages
from django.contrib.auth import get_user_model,authenticate,login,logout
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .forms import SignUpForm
import requests,json
from django.http import HttpResponseForbidden
from django.utils import timezone

User = get_user_model()
# Create your views here.

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def grecaptcha_verify(request):
    if request.method == 'POST':
        response = {}
        try:
            captcha_rs = request.POST.get('g-recaptcha-response')
        except KeyError:
            return False

        url = "https://www.google.com/recaptcha/api/siteverify"
        params = {
            'secret': '6LfvHe4UAAAAAORHYr2rnTQKSrSXpSfHqllKPbfe',
            'response': captcha_rs,
            'remoteip': get_client_ip(request)
        }
        verify_rs = requests.post(url, params=params, verify=True)
        verify_rs = verify_rs.json()
        response["status"] = verify_rs.get("success", False)
        response['message'] = verify_rs.get('error-codes', None) or "Unspecified error."
        return response


def index(request):
    recentThreads = Thread.objects.all().order_by("-posted")[:10]
    index_context = {
        'categories': PostCategory.objects.all(),
        'discord': True,
        'threads': recentThreads,
    }
    return render(request, "forum/basic.html", index_context)

@login_required
def category(request, id):
    category = get_object_or_404(PostCategory, pk=id)
    threads = category.getRecentThreads()
    category_context = {
        'categories': PostCategory.objects.all(),
        'discord': True,
        'current_category': category,
        'threads': threads
    }
    return render(request, "forum/basic.html", category_context)

def thread(request, id):
    thread = get_object_or_404(Thread, pk=id)
    comments = thread.comment_set.order_by("-posted")[:10]
    thread_context = {
        'thread': thread,
        'comments': comments,
        'commentsite': reverse('sphynx:comment', kwargs={'id': id}),
        'permissionToEdit': thread.hasPermissionToEdit(request.user),
    }
    return render(request, "forum/thread.html", thread_context)

@login_required
def profile(request, id):
    profile_user = get_object_or_404(User, pk=id)
    profile_context = {
        'user': profile_user,
    }
    return render(request, "forum/profile.html", profile_context)

def auth(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("sphynx:index"))
    form = SignUpForm(request.POST)
    if form.is_valid():
        form.save()
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        login(request, user)
        return redirect('sphynx:index')
    else:
        form = SignUpForm()
    return render(request, 'forum/auth.html', {'form': form})


def logoutUser(request):
    if request.user.is_authenticated:
        logout(request)
    return HttpResponseRedirect(reverse("sphynx:index"))

def loginUser(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("sphynx:index"))
    try:
        username = request.POST['username']
        raw_password = request.POST['password']
    except KeyError:
        return HttpResponseRedirect(reverse("sphynx:auth"))


    if grecaptcha_verify(request)['status'] == False:
        login_context = {
            'errormsg': 'Invalid captcha response!'
        }
        return render(request, "forum/auth.html", login_context)

    

    user = authenticate(username=username, password=raw_password)
    if user is not None:
        login(request, user)
        if request.POST["next"] != "":
            redirect = request.POST["next"]
            return HttpResponseRedirect(redirect)
        else:
            return HttpResponseRedirect(reverse("sphynx:index"))

    else:
        login_context = {
            'errormsg': 'Invalid username or password!'
        }
        return render(request, "forum/auth.html", login_context)


@login_required
def newThread(request, id):
    if request.method == "POST":
        tredir = HttpResponseRedirect(reverse('sphynx:newthread', kwargs={'id': id}))
        try:
            title = request.POST["title"]
            body = request.POST["body"]
        except KeyError:
            return tredir
        
        if len(title.strip()) < 5 or len(title.strip()) > 25:
            return tredir
        if len(body.strip()) < 15 or len(body.strip()) > 500:
            return tredir
        
        if grecaptcha_verify(request)['status'] == False:
            return tredir
        catobj = get_object_or_404(PostCategory, pk=id)
        ntobj = Thread(title=title, category=catobj, icon=0, body=body, author=request.user)
        ntobj.save()
        return ntobj.getRedirect()


    else:
        thread_category = get_object_or_404(PostCategory, pk=id)
        new_context = {
            'category': thread_category,
        }
        return render(request, "forum/newthread.html", new_context)

@login_required
def edit(request, id):
    tredir = HttpResponseRedirect(reverse('sphynx:edit', kwargs={'id': id}))
    thread = get_object_or_404(Thread, pk=id)
    if not thread.hasPermissionToEdit(request.user):
        return HttpResponseForbidden()
        
    if request.method == 'POST':
        try:
            title = request.POST["title"]
            body = request.POST["body"]
        except KeyError:
            return tredir
        if grecaptcha_verify(request)['status'] == False:
            return tredir

        thread.title = title
        thread.body = body
        thread.edited_on = timezone.now()
        thread.save()
        return thread.getRedirect()
        
    else:

        thread_category = thread.category
        new_context = {
            'category': thread_category,
            'thread': thread
        }
        return render(request, "forum/newthread.html", new_context)
        

@login_required
def comment(request, id):
    thread = get_object_or_404(Thread, pk=id)
    credir = thread.getRedirect()
    if request.method != 'POST':
        return credir
    try:
        body = request.POST["commentbody"]
    except KeyError:
        return credir
    
    if len(body.strip()) < 15 or len(body.strip()) > 500:
        return credir
    
    ncobj = Comment(thread=thread, body=body, author=request.user)
    ncobj.save()
    return credir
    
