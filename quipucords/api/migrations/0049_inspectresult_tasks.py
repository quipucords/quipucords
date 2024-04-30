from django.db import migrations, models


def bind_inspect_result_to_scantask(apps, schema_editor):
    """Bind InspectResult to ScanTask."""
    InspectResult = apps.get_model("api", "InspectResult")
    M2MModel = InspectResult.tasks.through  # noqa: N806
    m2m_instances = []
    for result in InspectResult.objects.prefetch_related(
        "task_inspection_result__scantask"
    ).all():
        task_id = result.task_inspection_result.scantask.id
        m2m_instances.append(M2MModel(inspectresult_id=result.id, scantask_id=task_id))
    M2MModel.objects.bulk_create(m2m_instances)


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0048_rename_system_inspection_result_rawfact_inspect_result"),
    ]

    operations = [
        migrations.AddField(
            model_name="inspectresult",
            name="tasks",
            field=models.ManyToManyField(
                related_name="inspect_results", to="api.scantask"
            ),
        ),
        migrations.RunPython(
            bind_inspect_result_to_scantask,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
