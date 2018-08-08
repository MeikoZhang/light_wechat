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
if os.path.exists(qrCode_dir):
    os.remove(qrCode_dir)
# 登陆信息存储目录
login_status_dir = os.path.join(BASE_DIR, 'static\wx_login\itchat.pkl')
# 微信图片/文件存放目录
wx_files_dir = os.path.join(BASE_DIR, 'static\wx_files')

q = Queue(maxsize=100)

if_login = False
qruuid = None
head_img = None

load_user = None


def login_callback():
    global if_login
    if_login = True
    logger.info("登陆成功 ...")
    global load_user
    load_user = itchat.search_friends()


def exit_callback():
    global if_login
    if_login = False
    logger.info("程序已登出 ...")


def qr_callback(uuid=None, status=None, qrcode=None):
    logger.info("二维码获取及存储 ...uuid:%s status:%s" % (uuid, status))
    with open(qrCode_dir, 'wb') as f:
        f.write(qrcode)
    # qruuid = uuid
    # logger.info("qr_callback uuid:%s" % (uuid))
    # global qruuid
    # if qruuid != uuid:


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
        get_qr()
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

    class WebMessage(object):
        def __init__(self, _msg):
            self._msg = _msg

        def get_msg(self):
            return self._msg

    # 消息注册，好友文本消息
    @itchat.msg_register(TEXT)
    def text_reply(msg):
        logger.debug(json.dumps(msg))

        # q_msg = WebMessage('text', msg)
        # q.put(q_msg)

        msg_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(msg.createTime))
        msg_from = itchat.search_friends(userName=msg['FromUserName'])['NickName']
        msg_to = itchat.search_friends(userName=msg['ToUserName'])['NickName']
        msg_text = msg['Text']

        wx_record = WxRecord(is_group='0', msg_type=msg.type,
                             msg_time=msg_time, msg_from=msg_from, msg_to=msg_to, msg_text=msg_text)
        wx_record.save()

        q.put(WebMessage({'is_group': '0', 'msg_type': msg.type, 'msg_time': msg_time,
                          'msg_from': msg_from, 'msg_to': msg_to, 'msg_text': msg_text}))

        logger.debug("save to db type:%s time:%s from:%-15s  to: %-15s  content:%s"
                     % (msg.type, msg_time, msg_from, msg_to, msg_text))

    # 消息注册，好友图片/音频/视频/文件消息
    @itchat.msg_register([PICTURE, RECORDING, ATTACHMENT, VIDEO])
    def download_files(msg):
        msg.download(os.path.join(wx_files_dir, msg.fileName))

        msg_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(msg.createTime))
        msg_from = itchat.search_friends(userName=msg['FromUserName'])['NickName']
        msg_to = itchat.search_friends(userName=msg['ToUserName'])['NickName']
        msg_text = os.path.join(wx_files_dir, msg.fileName)

        wx_record = WxRecord(is_group='0', msg_type=msg.type,
                             msg_time=msg_time, msg_from=msg_from, msg_to=msg_to, msg_text=msg_text)
        wx_record.save()
        q.put(WebMessage({'is_group': '0', 'msg_type': msg.type, 'msg_time': msg_time,
                          'msg_from': msg_from, 'msg_to': msg_to, 'msg_text': msg_text}))
        logger.debug("save to db type:%s time:%s from:%-15s  to: %-15s  content:%s"
                     % (msg.type, msg_time, msg_from, msg_to, msg_text))

    # 消息注册，群文本消息
    @itchat.msg_register(TEXT, isGroupChat=True)
    def text_reply(msg):
        logger.debug(json.dumps(msg))

        msg_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(msg.createTime))
        msg_from = msg['ActualNickName']
        msg_to = msg['User']['NickName']
        msg_text = msg['Text']

        wx_record = WxRecord(is_group='1', msg_type=msg.type,
                             msg_time=msg_time, msg_from=msg_from, msg_to=msg_to, msg_text=msg_text)
        wx_record.save()
        q.put(WebMessage({'is_group': '1', 'msg_type': msg.type, 'msg_time': msg_time,
                          'msg_from': msg_from, 'msg_to': msg_to, 'msg_text': msg_text}))
        logger.debug("save to db type:%s time:%s from:%-15s  to: %-15s  content:%s"
                     % ('2', msg_time, msg_from, msg_to, msg_text))

    # 消息注册，群图片/音频/视频/文件消息
    @itchat.msg_register([PICTURE, RECORDING, ATTACHMENT, VIDEO], isGroupChat=True)
    def download_files(msg):
        msg.download(os.path.join(wx_files_dir, msg.fileName))

        msg_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(msg.createTime))
        msg_from = itchat.search_friends(userName=msg['FromUserName'])['NickName']
        msg_to = itchat.search_friends(userName=msg['ToUserName'])['NickName']
        msg_text = os.path.join(wx_files_dir, msg.fileName)

        wx_record = WxRecord(is_group='1', msg_type=msg.type,
                             msg_time=msg_time, msg_from=msg_from, msg_to=msg_to, msg_text=msg_text)
        wx_record.save()
        q.put(WebMessage({'is_group': '1', 'msg_type': msg.type, 'msg_time': msg_time,
                          'msg_from': msg_from, 'msg_to': msg_to, 'msg_text': msg_text}))
        logger.debug("save to db type:%s time:%s from:%-15s  to: %-15s  content:%s"
                     % (msg.type, msg_time, msg_from, msg_to, msg_text))

    # 新建线程跑任务
    def new_thread():
        itchat.run()

    threading.Thread(target=new_thread).start()
    logger.info("聊天记录同步中 ... ")
    return status


# 获取消息
def get_msg():
    if not if_login:
        logger.info("status not login, reloading...")
        reload_status = login()
        if reload_status == '200':
            logger.info("status not login, reloading success")
        else:
            return {'status': 'not login, reloading failed'}

    logger.info("getting msg from webQueue ...")
    try:
        q_msg = q.get(timeout=25)
    except Exception:
        logger.error("getting from queue error")
        q_msg = None

    if q_msg is None:
        return None

    msg = q_msg.get_msg()

    msg_type_list = {TEXT: '文本消息', PICTURE: '图片消息',
                     RECORDING: '语音消息', ATTACHMENT: '附件消息', VIDEO: '视频消息'}
    msg_type = msg_type_list.get(msg.get('msg_type'))
    msg_text = msg.get('msg_text') if msg_type == '文本消息' else msg_type
    msg_time = msg.get('msg_time')
    msg_from = msg.get('msg_from')
    msg_to = msg.get('msg_to')

    msg_group = msg.get('is_group')
    if msg_group == '0':
        logger.info('好友消息 ... time:%s from:%-15s  to: %-15s  content:%s' %
                    (msg_time, msg_from, msg_to, msg_text))
    else:
        logger.info('群内消息 ... time:%s from:%-15s  to:%-15s  content:%s' %
                    (msg_time, msg_from, msg_to, msg_text))
    return {'status': 'ok', 'msg_type': msg_type, 'msg_time': msg_time,
            'msg_from': msg_from, 'msg_to': msg_to, 'msg_text': msg_text}


def thread_auto_login():

    # 消息注册 好友消息
    @itchat.msg_register(TEXT)
    def text_reply(msg):
        print(json.dumps(msg))
        fromuser = itchat.search_friends(userName=msg['FromUserName'])['NickName']
        print(itchat.search_friends(userName=msg['ToUserName']))
        touser = itchat.search_friends(userName=msg['ToUserName'])['NickName']
        msgtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(msg.createTime))
        msgtext = msg['Text']
        print('time:%s from:%s  to: %s  content:%s' % (msgtime, fromuser, touser, msgtext))

    itchat.auto_login(hotReload=True, statusStorageDir=login_status_dir, picDir=qrCode_dir,
                      qrCallback=qr_callback,
                      loginCallback=login_callback, exitCallback=exit_callback)
    itchat.run(blockThread=False)
    global if_login
    if_login = True
    print('auto_login over')


def auto_login():
    print('thread_auto_login start')
    threading.Thread(target=thread_auto_login).start()
    print('thread_auto_login over')
    itchat.web_init


def login_status():
    return if_login;


def logout():
    global if_login
    if_login = False
    itchat.logout();

