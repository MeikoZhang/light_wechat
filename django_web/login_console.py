from django.test import TestCase

# Create your tests here.
import itchat
import time
import sys
from itchat.content import *
import os
import json
from queue import Queue


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
picDir = os.path.join(BASE_DIR,'static\wx_files\qrcode.jpg')
loginDir = os.path.join(BASE_DIR,'static\wx_files\itchat.pkl')

q = Queue(maxsize=100)

if_login = False
if_run = False
qr_uuid = None


def login(if_login):
    if_login = True


def logout(self, if_run):
    self.logout = False
    if_run = True


def qrcb(uuid=None, status=None, qrcode=None):
    with open(picDir, 'wb') as f:
        f.write(qrcode)


def output_info(msg):
    print('[INFO] %s' % msg)


def open_QR():
    for get_count in range(10):
        output_info('Getting uuid')
        uuid = itchat.get_QRuuid()
        while uuid is None:
            uuid = itchat.get_QRuuid()
            time.sleep(1)
        output_info('Getting QR Code')
        if itchat.get_QR(uuid):
            break
        elif get_count >= 9:
            output_info('Failed to get QR Code, please restart the program')
            sys.exit()
    output_info('Please scan the QR Code')
    return uuid


def login():
    uuid = open_QR()
    print('-------get qrcode')
    waitForConfirm = False
    while 1:
        status = itchat.check_login(uuid)
        if status == '200':
            break
        elif status == '201':
            if waitForConfirm:
                output_info('Please press confirm')
                waitForConfirm = True
        elif status == '408':
            output_info('Reloading QR Code')
            uuid = open_QR()
            waitForConfirm = False

    print('-------get login success')

    # 保存登陆状态
    itchat.dump_login_status(fileDir=loginDir)

    # 获取登陆人信息
    userInfo = itchat.web_init()
    print('Login successfully as %s' % userInfo['User']['NickName'])

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

    # 启动心跳连接
    itchat.start_receiving()
    print('-------start receiving,itchat class:'+str(itchat))

    # 消息注册 好友消息
    @itchat.msg_register(TEXT)
    def text_reply(msg):
        # print(json.dumps(msg))
        q.put(msg)
        fromuser = itchat.search_friends(userName=msg['FromUserName'])['NickName']
        print(itchat.search_friends(userName=msg['ToUserName']))
        touser = itchat.search_friends(userName=msg['ToUserName'])['NickName']
        msgtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(msg.createTime))
        msgtext = msg['Text']
        print('time:%s from:%s  to: %s  content:%s' % (msgtime, fromuser, touser, msgtext))

    # 消息注册 群聊消息
    @itchat.msg_register(TEXT, isGroupChat=True)
    def text_reply(msg):
        print(json.dumps(msg))
        # chatgroupname = msg['User']['NickName']
        print(itchat.search_chatrooms(userName=msg['ToUserName']))
        chatgroupname = itchat.search_chatrooms(userName=msg['ToUserName'])['NickName']
        chatusername = msg['ActualNickName']
        msgtext = msg['Text']
        msgtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(msg.createTime))
        print('time:%s from:%s  group:%s  content:%s' % (msgtime, chatusername, chatgroupname, msgtext))

    @itchat.msg_register([PICTURE, RECORDING, ATTACHMENT, VIDEO])
    def download_files(msg):
        file = msg.download(os.path.join(BASE_DIR,'static\wx_files', msg.fileName))
        typeSymbol = {
            PICTURE: 'img',
            VIDEO: 'vid', }.get(msg.type, 'fil')
        return '@%s@%s' % (typeSymbol, msg.fileName)

    # itchat.run(blockThread=False)
    itchat.run()

    # def newThread():
    #     itchat.run()
    # threading.Thread(target=newThread).start()
    # print("正在监控中 ... ")
    # while True:
    #     print("---------- get msg from queue ...")
    #     queuemsg = q.get()
    #     fromuser = itchat.search_friends(userName=queuemsg['FromUserName'])['NickName']
    #     print(itchat.search_friends(userName=queuemsg['ToUserName']))
    #     touser = itchat.search_friends(userName=queuemsg['ToUserName'])['NickName']
    #     msgtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(queuemsg.createTime))
    #     msgtext = queuemsg['Text']
    #     print('msg from queue ... time:%s from:%s  to: %s  content:%s' % (msgtime, fromuser, touser, msgtext))

login()
