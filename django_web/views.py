from django.shortcuts import render
import django_web.login as weblogin
from django.http import HttpResponse
import json
from django.template import RequestContext, loader


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
    print('load_login return status : ' + json.dumps(status))
    return HttpResponse(status)


def check_login(request):
    status = weblogin.check_login()
    print('check_login return status : ' + status)
    return HttpResponse(status)


def login(request):
    status = weblogin.login()
    print('login return status : '+status)
    return HttpResponse(status)


def get_msg(request):
    msg = weblogin.get_msg()
    if msg is None:
        return HttpResponse("", content_type="application/json; charset=utf-8")
    return HttpResponse(json.dumps(msg), content_type="application/json; charset=utf-8")
