# Generated by Django 4.2.14 on 2024-07-17 19:19

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0054_remove_deploymentsreport_cached_csv_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="systemfingerprint",
            name="user_login_history",
        ),
    ]
