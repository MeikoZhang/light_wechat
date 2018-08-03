import itchat
import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
picDir=os.path.join(BASE_DIR,'static\images\qrcode.jpg')
qruuid = None

def loginCallback():
    print("登陆成功 ...")

def exitCallback():
    print("程序已登出 ...")

def qrCallback(uuid=None, status=None, qrcode=None):
    print("二维码获取及存储 ...")
    with open(picDir, 'wb') as f:
        f.write(qrcode)

def getQR():
    qruuid = itchat.get_QRuuid()
    itchat.uuid=qruuid
    if os.path.exists(picDir):
        os.remove(picDir)
    itchat.get_QR(uuid=qruuid, picDir=picDir, qrCallback=qrCallback)

def login():
    status = itchat.check_login(qruuid)
    print('-------status'+status)
    userInfo = itchat.web_init()
    print('-------web init')
    itchat.show_mobile_login()
    print('-------show mobile login')
    itchat.get_contact()
    print('-------get contract success')
    print('Login successfully as %s' % userInfo['User']['NickName'])
    itchat.start_receiving()
    print('-------start receiving,itchat' + str(itchat))
    return status

def get_msg():
    print('get msg ing....')
    msg = itchat.get_msg()
    return json.dumps(msg)
