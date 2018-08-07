from django.db import models

# Create your models here.


class WxRecord(models.Model):
    # group :1  not group:0
    is_group = models.CharField(max_length=2)
    # text,img,vid,fil
    msg_type = models.CharField(max_length=50)
    # %Y-%m-%d %H:%M:%S
    msg_time = models.CharField(max_length=50)
    # who send the message
    msg_from = models.CharField(max_length=100)
    # who receive the message
    msg_to = models.CharField(max_length=100)
    # message content
    msg_text = models.CharField(max_length=2048)
