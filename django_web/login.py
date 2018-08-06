import itchat
from itchat.content import *
import os
import time
import json
import threading
from queue import Queue
from django_web.models import WxRecord

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 验证码存储路径
qrcode_path = os.path.join(BASE_DIR, 'static\wx_login\qrcode.jpg')
# 登陆信息存储目录
login_file = os.path.join(BASE_DIR, 'static\wx_login\itchat.pkl')
# 微信图片/文件存放目录
wx_files_dir = os.path.join(BASE_DIR, 'static\wx_files')

# web页面获取消息队列
q = Queue(maxsize=100)

# 是否登陆
if_login = False

# 是否运行中
if_run = False

# 获取的uuid
qruuid = None


def loginCallback():
    print("登陆成功 ...")


def exitCallback():
    print("程序已登出 ...")


def qrCallback(uuid=None, status=None, qrcode=None):
    print("二维码获取及存储 ...uuid:%s status:%s" % (uuid, status))
    with open(qrcode_path, 'wb') as f:
        f.write(qrcode)


def getQR():
    global qruuid
    qruuid = itchat.get_QRuuid()
    itchat.uuid = qruuid
    if os.path.exists(qrcode_path):
        os.remove(qrcode_path)
    itchat.get_QR(uuid=qruuid, picDir=qrcode_path, qrCallback=qrCallback)
    return qruuid


def load_login():
    # return itchat.load_login_status(fileDir=loginDir, loginCallback=loginCallback, exitCallback=exitCallback)
    return itchat.load_login_status(fileDir=login_file, loginCallback=loginCallback, exitCallback=exitCallback)


def check_login():
    return itchat.check_login(qruuid)


def login():
    print('-------get login status')
    status = itchat.check_login(qruuid)
    print('-------status'+status)

    if status == '200':
        print('-------get login success')
    elif status == '201':
        print('Please press confirm')
        return status
    elif status == '408':
        print('Reloading QR Code')
        return status

    # 获取登陆人信息
    user_info = itchat.web_init()
    print('Login successfully as %s' % user_info['User']['NickName'])

    # 手机web微信登陆状态显示
    itchat.show_mobile_login()
    print('-------show mobile login')

    # 获取最新近聊列表
    itchat.get_contact(update=True)
    print('-------get contact complete')

    # 获取最新好友列表
    itchat.get_friends(update=True)
    print('-------get friends complete')

    # 获取最新群聊列表
    chatrooms = itchat.get_chatrooms(update=True)
    print('-------get chatrooms complete')

    # 更新群聊详细信息(人员列表)
    for chatroom in chatrooms:
        # print(json.dumps(chatroom))
        itchat.update_chatroom(userName=chatroom['UserName'])
    print('-------update chatrooms members complete')

    print('-------get login success')
    # 保存登陆状态
    itchat.dump_login_status(fileDir=login_file)

    # 启动心跳连接
    itchat.start_receiving()
    print('-------start receiving,itchat class:' + str(itchat))

    class QMessage(object):
        def __init__(self, _type, _msg):
            self._type = _type
            self._msg = _msg

        def get_type(self):
            return self._type

        def get_msg(self):
            return self._msg

    @itchat.msg_register(TEXT)
    def text_reply(msg):
        print(json.dumps(msg))
        q_msg = QMessage('1', msg)
        q.put(q_msg)

        msg_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(msg.createTime))
        msg_from = itchat.search_friends(userName=msg['FromUserName'])['NickName']
        msg_to = itchat.search_friends(userName=msg['ToUserName'])['NickName']
        msg_text = msg['Text']
        WxRecord.objects.create(msg_type='1', msg_time=msg_time, msg_from=msg_from, msg_to=msg_to, msg_text=msg_text)

    @itchat.msg_register(TEXT, isGroupChat=True)
    def text_reply(msg):
        print(json.dumps(msg))
        q_msg = QMessage('2', msg)
        q.put(q_msg)

        msg_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(msg.createTime))
        msg_from = msg['ActualNickName']
        msg_to = msg['User']['NickName']
        msg_text = msg['Text']
        WxRecord.objects.create(msg_type='2', msg_time=msg_time, msg_from=msg_from, msg_to=msg_to, msg_text=msg_text)

    @itchat.msg_register([PICTURE, RECORDING, ATTACHMENT, VIDEO])
    def download_files(msg):
        msg.download(os.path.join(wx_files_dir,msg.fileName))
        typeSymbol = {
            PICTURE: 'img',
            VIDEO: 'vid', }.get(msg.type, 'fil')
        return '@%s@%s' % (typeSymbol, msg.fileName)
    # itchat.run(blockThread=False)

    def new_thread():
        itchat.run()

    threading.Thread(target=new_thread).start()
    print("正在监控中 ... ")
    return status


def get_msg():
    print("---------- get msg from queue ...")
    try:
        q_msg = q.get(timeout=25)
    except Exception:
        q_msg = None

    if q_msg is None:
        return None
    msg = q_msg.get_msg()
    if q_msg.get_type() == '1':
        msg_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(msg.createTime))
        msg_from = itchat.search_friends(userName=msg['FromUserName'])['NickName']
        msg_to = itchat.search_friends(userName=msg['ToUserName'])['NickName']
        msg_text = msg['Text']
        print('好友消息 ... time:%s from:%-15s  to: %-15s  content:%s' % (msg_time, msg_from, msg_to, msg_text))
    else:
        msg_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(msg.createTime))
        msg_from = msg['ActualNickName']
        msg_to = msg['User']['NickName']
        # chatgroupname = itchat.search_chatrooms(userName=msg['ToUserName'])['NickName']
        msg_text = msg['Text']
        print('群内消息 ... time:%s from:%-15s  to:%-15s  content:%s' % (msg_time, msg_from, msg_to, msg_text))
    return {'msg_type': q_msg.get_type(), 'msg_time': msg_time, 'msg_from': msg_from,
            'msg_to': msg_to, 'msg_text': msg_text}


