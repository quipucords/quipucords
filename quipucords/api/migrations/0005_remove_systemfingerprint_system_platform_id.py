# Generated by Django 2.2.3 on 2019-08-05 19:56

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0004_virtual_host_name"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="systemfingerprint",
            name="system_platform_id",
        ),
    ]
