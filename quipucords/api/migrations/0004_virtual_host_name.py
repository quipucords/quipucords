# Generated by Django 2.2.2 on 2019-07-23 15:36

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0003_system_platform_id"),
    ]

    operations = [
        migrations.RenameField(
            model_name="systemfingerprint",
            old_name="vm_host",
            new_name="virtual_host_name",
        ),
    ]
