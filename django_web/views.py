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
    weblogin.getQR()
    return render(request, 'login.html')


def login(request):
    status = weblogin.login()
    print('login return status : '+status)
    return HttpResponse(status)


def get_msg(request):
    msg = weblogin.get_msg()
    if msg is None:
        return HttpResponse("", content_type="application/json; charset=utf-8")
    return HttpResponse(json.dumps(msg), content_type="application/json; charset=utf-8")
