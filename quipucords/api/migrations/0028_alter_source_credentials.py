# Generated by Django 4.1.7 on 2023-03-27 17:24

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0027_migrate_search_directories_to_jsonfield"),
    ]

    operations = [
        migrations.AlterField(
            model_name="source",
            name="credentials",
            field=models.ManyToManyField(related_name="sources", to="api.credential"),
        ),
    ]
