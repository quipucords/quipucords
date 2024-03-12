# Generated by Django 4.2.10 on 2024-02-28 13:16

from django.db import migrations


def rename_id_seq(apps, schema_editor):
    """Rename SystemInspectionResult sequence to InspectResult."""
    if schema_editor.connection.vendor != "postgresql":
        # this problem only affects postgresql - on SQLite the sequence is properly
        # renamed
        return
    # Due to an at least 7yr old bug with django [1], migrations.RenameModel is not
    # enough; we need to manually rename its sequence name for consistency
    # [1]: https://stackoverflow.com/q/34515818/6200095
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            (
                "ALTER SEQUENCE api_systeminspectionresult_id_seq "
                "RENAME TO api_inspectresult_id_seq"
            )
        )


def reverse_rename_id_seq(apps, schema_editor):
    """Rollback rename_id_seq."""
    if schema_editor.connection.vendor != "postgresql":
        return

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            (
                "ALTER SEQUENCE api_inspectresult_id_seq "
                "RENAME TO api_systeminspectionresult_id_seq"
            )
        )


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0046_merge_scan_options_with_scan"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="SystemInspectionResult",
            new_name="InspectResult",
        ),
        migrations.RunPython(rename_id_seq, reverse_code=reverse_rename_id_seq),
    ]