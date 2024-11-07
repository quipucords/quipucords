"""Report mixins."""

from functools import cached_property

from rest_framework.generics import get_object_or_404

from api.models import Report
from api.report.pagination import ReportPagination


class ReportViewMixin:
    """Mixin for paginated report views."""

    pagination_class = ReportPagination
    # lookup kwarg MUST be something that uniquely identifies a Report
    # good candidates: id, report_platform_id, pk, and report_id
    lookup_url_kwarg = "report_id"
    # child classes need to override report_type
    report_type = None
    # child classes also need to override lookup_field (this is set to None
    # to ensure an error will be thrown if no value is provided)
    lookup_field = None

    def get_report(self):
        """Return the report associated to this view."""
        lookup_url_kwarg = self._get_lookup_kwarg()
        # at this point all report views have the lookup_url_kwarg named "report_id"
        # (which doesn't exist in Report model). The following ensures the continuity
        # of this tradition
        report_identifier_key = (
            "pk" if lookup_url_kwarg == "report_id" else lookup_url_kwarg
        )
        return get_object_or_404(
            Report.objects.only("report_platform_id", "report_version"),
            **{report_identifier_key: self.kwargs[lookup_url_kwarg]},
        )

    def _get_lookup_kwarg(self):
        # shamelessly copied from DRF's GenericAPIView.get_object
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        assert lookup_url_kwarg in self.kwargs, (  # noqa: S101
            "Expected view %s to be called with a URL keyword argument "
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            "attribute on the view correctly."
            % (self.__class__.__name__, lookup_url_kwarg)
        )
        return lookup_url_kwarg

    @cached_property
    def paginator(self):
        """
        Return paginator instance.

        Overrides DRF's views paginator property to initialize ReportPagination with its
        custom arguments.
        """
        report = self.get_report()
        _paginator = self.pagination_class()
        _paginator.add_report_metadata(
            report_platform_id=report.report_platform_id,
            report_version=report.report_version,
            report_type=self.report_type,
        )
        return _paginator

    def get_queryset(self):
        """Filter queryset to only get results related to a report."""
        qs = super().get_queryset()
        return qs.filter(**{self.lookup_field: self.kwargs[self._get_lookup_kwarg()]})
