import os, time, json, sys, threading
from queue import Queue
import itchat
from itchat.content import *
from itchat.utils import test_connect
from django_web.models import WxRecord
from django_web.Logger import logger


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 验证码存储路径
qrCode_dir = os.path.join(BASE_DIR, 'static\wx_login\qrcode.jpg')
# 登陆信息存储目录
login_status_dir = os.path.join(BASE_DIR, 'static\wx_login\itchat.pkl')
# 微信图片/文件存放目录
wx_files_dir = os.path.join(BASE_DIR, 'static\wx_files')

q = Queue(maxsize=100)

if_login = False
if_run = False
qruuid = None


def login_callback():
    global if_login
    if_login = True
    logger.info("登陆成功 ...")


def exit_callback():
    global if_login
    if_login = False
    logger.info("程序已登出 ...")


def qr_callback(uuid=None, status=None, qrcode=None):
    logger.info("二维码获取及存储 ...uuid:%s status:%s" % (uuid, status))
    with open(qrCode_dir, 'wb') as f:
        f.write(qrcode)


def get_qr():
    if not test_connect():
        logger.info("You can't get access to internet or wechat domain, so exit.")
        return None

    global qruuid
    qruuid = itchat.get_QRuuid()
    itchat.uuid = qruuid
    if os.path.exists(qrCode_dir):
        os.remove(qrCode_dir)
    itchat.get_QR(uuid=qruuid, picDir=qrCode_dir, qrCallback=qr_callback)
    return qruuid


def load_login():
    return itchat.load_login_status(fileDir=login_status_dir, loginCallback=login_callback, exitCallback=exit_callback)


def check_login():
    return itchat.check_login(qruuid)


def login():
    if load_login():
        global if_login
        if_login = True
        logger.info('loan login status success')
        return '200'

    logger.info('begin to login ...')
    status = itchat.check_login(qruuid)
    logger.info('check login status'+status)

    if status == '200':
        if_login = True
        logger.info('check login, status success')
    elif status == '201':
        logger.info('check login, need confirm')
        return status
    elif status == '408':
        logger.info('check login, qrCode timeout')
        return status

    # 获取登陆人信息
    user_info = itchat.web_init()
    logger.info('Login successfully as %s' % user_info['User']['NickName'])

    # 手机web微信登陆状态显示
    itchat.show_mobile_login()
    logger.info('show mobile login')

    # 获取最新近聊列表
    itchat.get_contact(update=True)
    logger.info('get contact complete')

    # 获取最新好友列表
    itchat.get_friends(update=True)
    logger.info('get friends complete')

    # 获取最新群聊列表
    chat_rooms = itchat.get_chatrooms(update=True)
    logger.info('get chatRooms complete')

    # 更新群聊详细信息(人员列表)
    for chat_room in chat_rooms:
        logger.debug(json.dumps(chat_room))
        itchat.update_chatroom(userName=chat_room['UserName'])
    logger.info('update chatRooms members complete')

    # 保存登陆状态
    itchat.dump_login_status(fileDir=login_status_dir)
    logger.info('save the login success to %s' % login_status_dir)

    # 启动心跳连接
    itchat.start_receiving()
    logger.info('start receiving and heartbeat')

    # web页面获取信息的队列
    class WebMessage(object):
        def __init__(self, _type, _msg):
            self._type = _type
            self._msg = _msg

        def get_type(self):
            return self._type

        def get_msg(self):
            return self._msg

    # 消息注册，好友文本消息
    @itchat.msg_register(TEXT)
    def text_reply(msg):
        logger.debug(json.dumps(msg))

        q_msg = WebMessage('text', msg)
        q.put(q_msg)

        msg_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(msg.createTime))
        msg_from = itchat.search_friends(userName=msg['FromUserName'])['NickName']
        msg_to = itchat.search_friends(userName=msg['ToUserName'])['NickName']
        msg_text = msg['Text']
        WxRecord.objects.create(msg_type='1', msg_time=msg_time, msg_from=msg_from, msg_to=msg_to, msg_text=msg_text)
        logger.debug("save to db type:%s time:%s from:%-15s  to: %-15s  content:%s"
                     % ('text', msg_time, msg_from, msg_to, msg_text))

    # 消息注册，好友图片/音频/视频/文件消息
    @itchat.msg_register([PICTURE, RECORDING, ATTACHMENT, VIDEO])
    def download_files(msg):
        msg.download(os.path.join(wx_files_dir, msg.fileName))

        msg_type = {PICTURE: 'img', VIDEO: 'vid', }.get(msg.type, 'fil')
        msg_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(msg.createTime))
        msg_from = itchat.search_friends(userName=msg['FromUserName'])['NickName']
        msg_to = itchat.search_friends(userName=msg['ToUserName'])['NickName']
        msg_text = os.path.join(wx_files_dir, msg.fileName)
        WxRecord.objects.create(msg_type='1', msg_time=msg_time, msg_from=msg_from, msg_to=msg_to, msg_text=msg_text)
        logger.debug("save to db type:%s time:%s from:%-15s  to: %-15s  content:%s"
                     % (msg_type, msg_time, msg_from, msg_to, msg_text))

    # 消息注册，群文本消息
    @itchat.msg_register(TEXT, isGroupChat=True)
    def text_reply(msg):
        logger.debug(json.dumps(msg))

        q_msg = WebMessage('2', msg)
        q.put(q_msg)

        msg_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(msg.createTime))
        msg_from = msg['ActualNickName']
        msg_to = msg['User']['NickName']
        msg_text = msg['Text']
        WxRecord.objects.create(msg_type='2', msg_time=msg_time, msg_from=msg_from, msg_to=msg_to, msg_text=msg_text)
        logger.debug("save to db type:%s time:%s from:%-15s  to: %-15s  content:%s"
                     % ('2', msg_time, msg_from, msg_to, msg_text))

    # 消息注册，群图片/音频/视频/文件消息
    @itchat.msg_register([PICTURE, RECORDING, ATTACHMENT, VIDEO], isGroupChat=True)
    def download_files(msg):
        msg.download(os.path.join(wx_files_dir, msg.fileName))

        msg_type = {PICTURE: 'img', VIDEO: 'vid', }.get(msg.type, 'fil')
        msg_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(msg.createTime))
        msg_from = itchat.search_friends(userName=msg['FromUserName'])['NickName']
        msg_to = itchat.search_friends(userName=msg['ToUserName'])['NickName']
        msg_text = os.path.join(wx_files_dir, msg.fileName)
        WxRecord.objects.create(msg_type='1', msg_time=msg_time, msg_from=msg_from, msg_to=msg_to, msg_text=msg_text)
        logger.debug("save to db type:%s time:%s from:%-15s  to: %-15s  content:%s"
                     % (msg_type, msg_time, msg_from, msg_to, msg_text))

    # 新建线程跑任务
    def new_thread():
        itchat.run()

    threading.Thread(target=new_thread).start()
    logger.info("聊天记录同步中 ... ")
    return status


def get_msg():
    if not if_login:
        logger.info("status not login, reloading...")
        reload_status = login()
        if reload_status != '200':
            logger.info("status not login, reloading failed")
            return {'msg_text': 'status not login'}
        logger.info("reload login success ...")

    logger.info("getting msg from webQueue ...")
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
        logger.info('好友消息 ... time:%s from:%-15s  to: %-15s  content:%s' % (msg_time, msg_from, msg_to, msg_text))
    else:
        msg_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(msg.createTime))
        msg_from = msg['ActualNickName']
        msg_to = msg['User']['NickName']
        # chatgroupname = itchat.search_chatrooms(userName=msg['ToUserName'])['NickName']
        msg_text = msg['Text']
        logger.info('群内消息 ... time:%s from:%-15s  to:%-15s  content:%s' % (msg_time, msg_from, msg_to, msg_text))
    return {'msg_type': q_msg.get_type(), 'msg_time': msg_time, 'msg_from': msg_from,
            'msg_to': msg_to, 'msg_text': msg_text}
