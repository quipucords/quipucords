"""Rename DetailsReport to Report."""

from django.db import migrations


def rename_details_report_sequence(apps, schema_editor):
    """Rename details_report_sequence to report_sequence."""
    if schema_editor.connection.vendor != "postgresql":
        # this problem only affects postgresql - on SQLite the sequence is properly
        # renamed
        return
    # Due to an at least 7yr old bug with django [1], renaming DeploymentsReport to
    # Report is not enough; we need to manually rename its sequence name for consistency
    #
    # [1]: https://stackoverflow.com/q/34515818/6200095
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            "ALTER SEQUENCE api_detailsreport_id_seq RENAME TO api_report_id_seq"
        )


def reverse_rename_details_report_sequence(apps, schema_editor):
    """Rollback `rename_details_report_sequence`."""
    if schema_editor.connection.vendor != "postgresql":
        return

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            "ALTER SEQUENCE api_report_id_seq RENAME TO api_detailsreport_id_seq"
        )


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0036_remove_deploymentsreport_report_id_and_more"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="DetailsReport",
            new_name="Report",
        ),
        migrations.RemoveField(
            model_name="report",
            name="report_type",
        ),
        migrations.RunPython(
            rename_details_report_sequence,
            reverse_code=reverse_rename_details_report_sequence,
        ),
    ]
