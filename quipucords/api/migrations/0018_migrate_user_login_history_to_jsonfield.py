# Generated by Django 3.2.17 on 2023-03-16 12:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0017_convert_to_jsonfield"),
    ]

    operations = [
        migrations.AlterField(
            model_name="systemfingerprint",
            name="user_login_history",
            field=models.JSONField(blank=True, null=True),
        ),
    ]
