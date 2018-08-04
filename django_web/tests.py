# Create your tests here.
from django.test import TestCase
from django_web.models import WxRecord


class ModelTest(TestCase):

    # 初始化：分别创建一条发布会（Event）和一条嘉宾（Guest）的数据。
    def setUp(self):
        WxRecord.objects.create(msg_type='1', msg_time='2018-08-04 14:22:42',
                                msg_from='凉城', msg_to='六岁就微信', msg_text='感觉')

    # 下面开始写测试用例了
    # 通过get的方法，查询插入的发布会数据，并根据地址判断
    def test_event_models(self):
        result = WxRecord.objects.get(msg_type='1')
        self.assertEqual(result.msg_type, "1")

    def test_all_models(self):
        result = WxRecord.objects.all()
        for r in result:
            print("type:%s time:%s from:%-15s  to: %-15s  content:%s"
                  % (r.msg_type, r.msg_time, r.msg_from, r.msg_to, r.msg_text))

    # 写完测试用例后，执行测试用例。这里与unittest的运行方法也不一样。
    # Django提供了“test”命令来运行测试。（用cmd执行 见下截图）

