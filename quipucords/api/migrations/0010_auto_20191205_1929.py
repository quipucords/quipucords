# Generated by Django 2.2.6 on 2019-12-05 19:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0009_user_info'),
    ]

    operations = [
        migrations.AddField(
            model_name='deploymentsreport',
            name='cached_hashed_csv',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='deploymentsreport',
            name='cached_hashed_fingerprints',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='detailsreport',
            name='cached_hashed_csv',
            field=models.TextField(null=True),
        ),
    ]
