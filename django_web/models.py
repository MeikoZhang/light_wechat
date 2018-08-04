from django.db import models

# Create your models here.


class WxRecord(models.Model):
    msg_type = models.CharField(max_length=2)
    msg_time = models.CharField(max_length=50)
    msg_from = models.CharField(max_length=100)
    msg_to = models.CharField(max_length=100)
    msg_text = models.CharField(max_length=2048)
