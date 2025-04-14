"""Module for ScanTaskQuerySet."""

from django.db.models import F, Q, QuerySet, Sum


class ScanJobQuerySet(QuerySet):
    """Custom QuerySet for ScanJob."""

    def with_counts(self):
        """Annotate ScanJob with system counts from associated tasks."""
        return self.annotate(
            systems_count=Sum(
                "tasks__systems_count",
                filter=Q(tasks__scan_type=F("scan_type")),
                default=0,
            ),
            systems_scanned=Sum(
                "tasks__systems_scanned",
                # only counts of tasks with the same scan_type should be considered
                filter=Q(tasks__scan_type=F("scan_type")),
                default=0,
            ),
            systems_failed=Sum(
                "tasks__systems_failed",
                filter=Q(tasks__scan_type=F("scan_type")),
                default=0,
            ),
            systems_unreachable=Sum(
                "tasks__systems_unreachable",
                filter=Q(tasks__scan_type=F("scan_type")),
                default=0,
            ),
        )
