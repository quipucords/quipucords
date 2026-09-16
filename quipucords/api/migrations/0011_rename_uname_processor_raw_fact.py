from django.db import migrations


def rename_uname_processor_to_uname_machine(apps, schema_editor):
    """Rename stored ``uname_processor`` raw facts to ``uname_machine``."""
    RawFact = apps.get_model("api", "RawFact")
    RawFact.objects.filter(name="uname_processor").update(name="uname_machine")


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0010_remove_source_use_paramiko"),
    ]

    operations = [
        migrations.RunPython(rename_uname_processor_to_uname_machine),
    ]
