# Generated by Django 2.0.7 on 2018-08-04 05:41

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='WxRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('msg_type', models.CharField(max_length=2)),
                ('msg_time', models.CharField(max_length=50)),
                ('msg_from', models.CharField(max_length=100)),
                ('msg_to', models.CharField(max_length=100)),
                ('msg_text', models.CharField(max_length=2048)),
            ],
        ),
    ]
