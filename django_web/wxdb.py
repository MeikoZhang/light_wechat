from django_web.models import WxRecord


def get_all():

    # 1.查询出所有图书的信息
    all = WxRecord.objects.all()
    return all


def get_index(msg_type=None):
    re = WxRecord.objects.get(msg_type=msg_type)
    return re


def save(msg_type=None, msg_time=None, msg_from=None, msg_to=None, msg_text=None):
    # 1.创建BookInfo对象
    r = WxRecord()
    r.msg_type = msg_type
    r.msg_time = msg_time
    r.msg_from = msg_from
    r.msg_to = msg_to
    r.msg_text = msg_text

    # 2.保存进数据库
    res = r.save()
    return res


def delete(msg_type):
    # 1.通过bid获取图书对象
    rd = WxRecord.objects.get(msg_type=msg_type)

    # 2.删除
    res = rd.delete()
    return res

