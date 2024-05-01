"""Common base model for all other models."""

from django.db import models


class BaseModel(models.Model):
    """Abstract model to add automatic created_at and updated_at fields."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        """Metadata for base model."""

        abstract = True
        ordering = ("created_at",)
