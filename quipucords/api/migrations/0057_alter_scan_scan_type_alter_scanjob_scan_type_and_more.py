# Generated by Django 4.2.20 on 2025-04-11 18:49

from django.db import migrations, models


def bind_connection_results_from_connect_to_inspect_tasks(apps, schema_editor):
    """Bind ConnectionResults from old connect ScanTasks to inspect ScanTasks."""
    ScanTask = apps.get_model("api", "ScanTask")
    for inspect_task in ScanTask.objects.filter(scan_type="inspect"):
        prerequisites = inspect_task.prerequisites.all()
        if not prerequisites:
            continue
        # Although "prerequisites" suggests many, in practice there is only one.
        connect_task = prerequisites[0]
        old_connection_result = connect_task.connection_result
        connect_task.connection_result = None
        connect_task.save()
        inspect_task.connection_result = old_connection_result
        inspect_task.prerequisites.set([])
        inspect_task.save()
        connect_task.delete()


def delete_old_connect_type_scan_tasks(apps, schema_editor):
    """Delete old connect-type ScanTask objects."""
    ScanTask = apps.get_model("api", "ScanTask")
    ScanTask.objects.filter(scan_type="connect").delete()


def delete_old_connect_type_scan_jobs(apps, schema_editor):
    """Delete old connect-type ScanJob objects."""
    ScanJob = apps.get_model("api", "ScanJob")
    ScanJob.objects.filter(scan_type="connect").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0056_report_inspect_groups"),
    ]

    operations = [
        migrations.RunPython(
            bind_connection_results_from_connect_to_inspect_tasks,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RunPython(
            delete_old_connect_type_scan_tasks,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RunPython(
            delete_old_connect_type_scan_jobs,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="scan",
            name="scan_type",
            field=models.CharField(
                choices=[("inspect", "inspect")], default="inspect", max_length=9
            ),
        ),
        migrations.AlterField(
            model_name="scanjob",
            name="scan_type",
            field=models.CharField(
                choices=[("inspect", "inspect"), ("fingerprint", "fingerprint")],
                default="inspect",
                max_length=12,
            ),
        ),
        migrations.AlterField(
            model_name="scantask",
            name="scan_type",
            field=models.CharField(
                choices=[("inspect", "inspect"), ("fingerprint", "fingerprint")],
                max_length=12,
            ),
        ),
    ]
