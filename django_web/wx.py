import itchat
import os
import django_web.tests as dwt

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
picDir=os.path.join(BASE_DIR,'static\images\qrcode.jpg')

def qrcb(uuid=None, status=None, qrcode=None):
    with open(picDir, 'wb') as f:
        f.write(qrcode)

def login():
    qruuid = itchat.get_QRuuid()
    if os.path.exists(picDir):
        os.remove(picDir)

    itchat.get_QR(uuid=qruuid, picDir=picDir, qrCallback=qrcb)

def check():
    isLoggedIn = False
    while not isLoggedIn:
        status = itchat.check_login()
        if status == '200':
            isLoggedIn = True
        elif status == '201':
            if isLoggedIn is not None:
                isLoggedIn = None
        elif status != '408':
            break
        if isLoggedIn:
            break
    print('loginstatus ...%s' %(status))

dwt.login()