# Generated by Django 2.2.6 on 2019-11-27 19:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_systemfingerprint_cloud_provider'),
    ]

    operations = [
        migrations.AddField(
            model_name='systemfingerprint',
            name='user_delete_history',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='systemfingerprint',
            name='user_info',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='systemfingerprint',
            name='user_login_history',
            field=models.TextField(null=True),
        ),
    ]
