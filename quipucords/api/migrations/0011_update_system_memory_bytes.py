# Generated by Django 3.2.14 on 2022-09-01 19:34

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0010_systemfingerprint_system_memory_bytes"),
    ]

    operations = [
        migrations.AlterField(
            model_name="systemfingerprint",
            name="system_memory_bytes",
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
    ]
