# Generated by Django 4.2.1 on 2023-06-07 22:09

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0031_alter_scantask_systems_count_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="credential",
            name="ssh_key",
            field=models.CharField(max_length=65536, null=True),
        ),
    ]
