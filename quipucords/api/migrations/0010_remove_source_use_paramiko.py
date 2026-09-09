from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0009_credential_vault_secret_key"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="source",
            name="use_paramiko",
        ),
    ]
