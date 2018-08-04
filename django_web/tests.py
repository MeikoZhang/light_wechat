from django.test import TestCase

# Create your tests here.
import os
import django
from django_web.models import WxRecord


class ModelTest(TestCase):

    # 初始化：分别创建一条发布会（Event）和一条嘉宾（Guest）的数据。
    def setUp(self):
        WxRecord.objects.create(msg_type='1', msg_time='1', msg_from='1', msg_to='1', msg_text='1')

    # 下面开始写测试用例了
    # 通过get的方法，查询插入的发布会数据，并根据地址判断
    def test_event_models(self):
        result = WxRecord.objects.get(msg_type='1')
        self.assertEqual(result.msg_type, "1")

    # 写完测试用例后，执行测试用例。这里与unittest的运行方法也不一样。
    # Django提供了“test”命令来运行测试。（用cmd执行 见下截图）
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "light_wechat.settings")  # 关联默认设置
# django.setup()  # 装载Django
# wxdb.save('1', '1', '1', '1', '1')
