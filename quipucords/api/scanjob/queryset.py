"""Module for ScanTaskQuerySet."""

from django.db.models import Case, F, Q, QuerySet, Sum, When

from api.scantask.model import ScanTask


class ScanJobQuerySet(QuerySet):
    """Custom QuerySet for ScanJob."""

    def with_counts(self):
        """Annotate ScanJob with system counts from associated tasks."""
        return self.annotate(
            systems_count=Sum(
                "tasks__systems_count",
                filter=Q(tasks__scan_type=ScanTask.SCAN_TYPE_CONNECT),
                default=0,
            ),
            systems_scanned=Sum(
                "tasks__systems_scanned",
                # only counts of tasks with the same scan_type should be considered
                filter=Q(tasks__scan_type=F("scan_type")),
                default=0,
            ),
            # case required for following annotations because inpection type scansjobs
            # sum failed/unreachable values from both connect and inspect tasks, while
            # connection type scanjobs only look for connection tasks
            systems_failed=Case(
                When(
                    scan_type=ScanTask.SCAN_TYPE_INSPECT,
                    then=Sum(
                        "tasks__systems_failed",
                        filter=Q(
                            tasks__scan_type__in=(
                                ScanTask.SCAN_TYPE_CONNECT,
                                ScanTask.SCAN_TYPE_INSPECT,
                            )
                        ),
                        default=0,
                    ),
                ),
                default=Sum(
                    "tasks__systems_failed",
                    filter=Q(tasks__scan_type=F("scan_type")),
                    default=0,
                ),
            ),
            systems_unreachable=Case(
                When(
                    scan_type=ScanTask.SCAN_TYPE_INSPECT,
                    then=Sum(
                        "tasks__systems_unreachable",
                        filter=Q(
                            tasks__scan_type__in=(
                                ScanTask.SCAN_TYPE_CONNECT,
                                ScanTask.SCAN_TYPE_INSPECT,
                            )
                        ),
                        default=0,
                    ),
                ),
                default=Sum(
                    "tasks__systems_unreachable",
                    filter=Q(tasks__scan_type=F("scan_type")),
                    default=0,
                ),
            ),
        )
