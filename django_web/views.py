from django.shortcuts import render
import django_web.login as weblogin
from django.http import HttpResponse
from django.template import RequestContext, loader

# Create your views here.
def index(request):
    return render(request, 'record.html')

def test(request):
    return render(request, 'test.html')

def qrcode(request):
    weblogin.getQR()
    return render(request, 'login.html')

def login(request):
    status = weblogin.login()
    return HttpResponse(status)

def get_msg(request):
    msg= weblogin.get_msg()
    return HttpResponse(msg)