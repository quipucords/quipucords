# Generated by Django 4.2.10 on 2024-03-01 19:45

import logging

import django.db.models.deletion
from django.db import migrations, models

logger = logging.getLogger(__name__)


def set_constraints_now(apps, schema_editor):
    """Set constraints now for postgresql."""
    if schema_editor.connection.vendor != "postgresql":
        # we only need this for postgresql because, according to django docs:
        # "On most database backends (all but PostgreSQL), Django will split the SQL
        # into individual statements prior to executing them."
        # https://docs.djangoproject.com/en/4.2/ref/migration-operations/#runsql
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")


def defer_constraints(apps, schema_editor):
    """Defer constraints for postgresql."""
    if schema_editor.connection.vendor != "postgresql":
        # we only need this for postgresql because, according to django docs:
        # "On most database backends (all but PostgreSQL), Django will split the SQL
        # into individual statements prior to executing them."
        # https://docs.djangoproject.com/en/4.2/ref/migration-operations/#runsql
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL DEFERRED")


def drop_all_scan_data(apps, schema_editor):
    """
    Wipe all scans results.

    We don't need a proper data migration, which would require some time fine tuning.
    """
    RawFact = apps.get_model("api", "RawFact")
    InspectResult = apps.get_model("api", "InspectResult")
    SystemConnectionResult = apps.get_model("api", "SystemConnectionResult")
    TaskConnectionResult = apps.get_model("api", "TaskConnectionResult")
    JobConnectionResult = apps.get_model("api", "JobConnectionResult")
    ScanTask = apps.get_model("api", "ScanTask")
    ScanJob = apps.get_model("api", "ScanJob")
    Scan = apps.get_model("api", "Scan")
    Report = apps.get_model("api", "Report")
    DeploymentsReport = apps.get_model("api", "DeploymentsReport")
    SystemFingerprint = apps.get_model("api", "SystemFingerprint")

    SystemFingerprint.objects.all().delete()
    DeploymentsReport.objects.all().delete()
    RawFact.objects.all().delete()
    InspectResult.objects.all().delete()
    SystemConnectionResult.objects.all().delete()
    TaskConnectionResult.objects.all().delete()
    JobConnectionResult.objects.all().delete()
    ScanTask.objects.all().delete()
    ScanJob.objects.all().delete()
    Report.objects.all().delete()
    Scan.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0050_remove_taskinspectionresult_job_inspection_result"),
    ]

    operations = [
        migrations.CreateModel(
            name="InspectGroup",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "source_type",
                    models.CharField(
                        choices=[
                            ("network", "network"),
                            ("vcenter", "vcenter"),
                            ("satellite", "satellite"),
                            ("openshift", "openshift"),
                            ("ansible", "ansible"),
                            ("rhacs", "rhacs"),
                        ],
                        max_length=12,
                    ),
                ),
                ("source_name", models.CharField(max_length=64)),
                ("server_id", models.CharField(max_length=36)),
                ("server_version", models.CharField(max_length=64)),
                (
                    "source",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="api.source",
                    ),
                ),
                (
                    "tasks",
                    models.ManyToManyField(
                        related_name="inspect_groups", to="api.scantask"
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="inspectresult",
            name="inspect_group",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="api.InspectGroup",
                related_name="inspect_results",
            ),
        ),
        migrations.RunPython(
            drop_all_scan_data,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RunPython(
            set_constraints_now, reverse_code=migrations.RunPython.noop
        ),
        migrations.RemoveField(
            model_name="report",
            name="sources",
        ),
        migrations.RemoveField(
            model_name="inspectresult",
            name="source",
        ),
        migrations.RemoveField(
            model_name="inspectresult",
            name="tasks",
        ),
        migrations.AlterField(
            model_name="inspectresult",
            name="inspect_group",
            field=models.ForeignKey(
                null=False,
                on_delete=django.db.models.deletion.CASCADE,
                to="api.InspectGroup",
                related_name="inspect_results",
            ),
        ),
        migrations.RunPython(defer_constraints, reverse_code=migrations.RunPython.noop),
    ]
