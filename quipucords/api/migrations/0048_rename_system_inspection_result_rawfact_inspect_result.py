# Generated by Django 4.2.10 on 2024-02-28 15:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0047_rename_systeminspectionresult_inspectresult"),
    ]

    operations = [
        migrations.RenameField(
            model_name="rawfact",
            old_name="system_inspection_result",
            new_name="inspect_result",
        ),
    ]
