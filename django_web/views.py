from django.shortcuts import render
import django_web.login as weblogin
from django.http import HttpResponse
import json


# Create your views here.
def index(request):
    return render(request, 'record.html')


def test(request):
    return render(request, 'test.html')


def qrcode(request):
    weblogin.get_qr()
    return render(request, 'login.html')


def load_login(request):
    status = weblogin.load_login()
    return HttpResponse(status)


def check_login(request):
    status = weblogin.check_login()
    return HttpResponse(status)


def login(request):
    status = weblogin.login()
    return HttpResponse(status)


def get_msg(request):
    msg = weblogin.get_msg()
    return HttpResponse(json.dumps(msg) if msg is not None else "",
                        content_type="application/json; charset=utf-8")
