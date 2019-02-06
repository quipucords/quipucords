# Generated by Django 2.1.5 on 2019-02-05 11:18
from django.db import migrations, models
import uuid
import json

# pylint: disable=no-name-in-module,import-error
from distutils.version import LooseVersion
from api.deployments_report.serializer import SystemFingerprintSerializer

def add_system_platform_id(apps, schema_editor):
    # Get old deployment reports
    DeploymentsReport = apps.get_model('api', 'DeploymentsReport')
    reports = DeploymentsReport.objects.all()
    cached_fingerprints = []
    for report in reports:
        if LooseVersion(report.report_version) < LooseVersion('0.0.47'):
            for system_fingerprint in report.system_fingerprints.all():
                serializer = SystemFingerprintSerializer(system_fingerprint)
                # json dumps/loads changes type of dictionary
                # removes massive memory growth for cached_fingerprints
                cached_fingerprints.append(json.loads(json.dumps(serializer.data)))
            report.cached_fingerprints = json.dumps(cached_fingerprints)
            report.cached_csv = None
            report.save()

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_insights_reports'),
    ]

    operations = [
        migrations.RenameField(
            model_name='deploymentsreport',
            old_name='cached_json',
            new_name='cached_fingerprints',
        ),
        migrations.AddField(
            model_name='systemfingerprint',
            name='system_platform_id',
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
        migrations.RunPython(add_system_platform_id),
    ]
