"""Migrate DeploymentsReport cached fields from DB columns to files on disk."""

import json
from sys import stdout
from time import time

from django.conf import settings
from django.db import migrations, models

import api.deployments_report.model

CACHED_FILE_NAME_FORMAT = "deployments-report-{id}-{unixtime}.{extension}"


def migrate_deployments_report_cached_fields(apps, schema_editor):
    """Migrate DeploymentsReport cached_csv and cached_fingerprints to files."""
    data_dir = settings.QUIPUCORDS_CACHED_REPORTS_DATA_DIR
    data_dir.mkdir(parents=True, exist_ok=True)
    DeploymentsReport = apps.get_model("api", "DeploymentsReport")
    any_dirty = False
    for deployments_report in DeploymentsReport.objects.all():
        dirty = False
        if deployments_report.cached_csv:
            file_path = data_dir / CACHED_FILE_NAME_FORMAT.format(
                id=deployments_report.id, unixtime=time(), extension="csv"
            )
            with file_path.open("w") as f:
                stdout.write(
                    f"\n  Migrating DeploymentsReport {deployments_report.id} "
                    f"cached_csv to {file_path}",
                )
                f.write(deployments_report.cached_csv)
            deployments_report.cached_csv_path = file_path
            dirty = True
        if deployments_report.cached_fingerprints:
            file_path = data_dir / CACHED_FILE_NAME_FORMAT.format(
                id=deployments_report.id, unixtime=time(), extension="json"
            )
            with file_path.open("w") as f:
                stdout.write(
                    f"\n  Migrating DeploymentsReport {deployments_report.id} "
                    f"cached_fingerprints to {file_path}",
                )
                json.dump(deployments_report.cached_fingerprints, f)
            deployments_report.cached_fingerprints_path = file_path
            dirty = True
        if dirty:
            any_dirty = True
            deployments_report.save()
    if any_dirty:
        stdout.write("\n  ...")


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0053_alter_report_report_version"),
    ]

    operations = [
        migrations.AddField(
            model_name="deploymentsreport",
            name="cached_csv_file_path",
            field=models.FilePathField(
                blank=True,
                max_length=255,
                null=True,
                path=api.deployments_report.model.cached_files_path,
            ),
        ),
        migrations.AddField(
            model_name="deploymentsreport",
            name="cached_fingerprints_file_path",
            field=models.FilePathField(
                blank=True,
                max_length=255,
                null=True,
                path=api.deployments_report.model.cached_files_path,
            ),
        ),
        migrations.RunPython(
            migrate_deployments_report_cached_fields,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RemoveField(
            model_name="deploymentsreport",
            name="cached_csv",
        ),
        migrations.RemoveField(
            model_name="deploymentsreport",
            name="cached_fingerprints",
        ),
    ]
