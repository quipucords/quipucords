# Generated by Django 4.2 on 2023-05-08 19:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0030_alter_credential_cred_type_alter_source_source_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="scantask",
            name="systems_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="scantask",
            name="systems_failed",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="scantask",
            name="systems_scanned",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="scantask",
            name="systems_unreachable",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
