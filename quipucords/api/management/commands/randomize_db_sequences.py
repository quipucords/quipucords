"""Randomize database sequences."""

import random

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    """Django management command for randomizing db sequences."""

    help = "Randomize database sequences"

    def handle(self, *args, **options):
        """Execute the logic for this command."""
        # shamelessly inspired on https://pytest-django.readthedocs.io/en/latest/database.html#randomize-database-sequences
        query_map = {
            "sqlite": (
                "UPDATE sqlite_sequence SET seq = {random_id} "
                "WHERE name = '{table_name}';"
            ),
            "postgresql": (
                "ALTER SEQUENCE {table_name}_id_seq RESTART WITH {random_id};"
            ),
        }
        query = query_map[connection.vendor]

        with connection.cursor() as cursor:
            for model_name in apps.all_models["api"]:
                model = apps.get_model("api", model_name)
                random_id = self._get_random_id(model)
                table_name = model._meta.db_table
                cursor.execute(query.format(random_id=random_id, table_name=table_name))

    def _get_random_id(self, model):
        """
        Get a random id for a given model.

        The random id is guaranteed to be > than MAX(model.id)
        """
        max_id = self._get_max_id(model)
        random_id = random.randint(10000, 20000)
        return random_id + max_id

    def _get_max_id(self, model):
        value_dict = model.objects.order_by("-id").values("id").first()
        if value_dict:
            return value_dict["id"]
        return 0
