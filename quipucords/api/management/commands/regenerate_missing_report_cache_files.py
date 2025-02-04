"""Regenerate missing DeploymentsReport cache files."""

from django.core.management.base import BaseCommand, CommandError

from api.deployments_report.model import DeploymentsReport
from api.deployments_report.tasks import generate_and_save_cached_csv
from utils.misc import is_valid_cache_file


class Command(BaseCommand):
    """Django management command to regenerate missing DeploymentsReport cache files."""

    help = "Regenerate missing DeploymentsReport cache files"

    def write_info(self, message):
        """Write info message to stdout."""
        self.stdout.write(message)

    def write_warning(self, message):
        """Write warning message to stdout."""
        self.stdout.write(self.style.WARNING(message))

    def write_success(self, message):
        """Write success message to stdout."""
        self.stdout.write(self.style.SUCCESS(message))

    def find_reports_with_missing_cached_data(self) -> tuple[set, set]:
        """
        Find reports with missing cached data and return their IDs.

        Returned tuple contains 1) the set of IDs with missing fingerprints
        and 2) the set of IDs with missing CSV data.
        """
        missing_fingerprints_ids = set()
        missing_csv_ids = set()
        deployments_reports = DeploymentsReport.objects.filter(
            status=DeploymentsReport.STATUS_COMPLETE
        ).values("id", "cached_fingerprints_file_path", "cached_csv_file_path")
        self.write_info(
            f"Found {len(deployments_reports)} completed DeploymentsReports to check."
        )
        for deployments_report in deployments_reports:
            # Note: We check for presence of value before checking is_valid_cache_file.
            # If the value is None, then the file was never written, and we do not care.

            if deployments_report[
                "cached_fingerprints_file_path"
            ] and not is_valid_cache_file(
                deployments_report["cached_fingerprints_file_path"]
            ):
                self.write_warning(
                    f"{deployments_report['cached_fingerprints_file_path']} is missing "
                    f"for DeploymentsReport {deployments_report['id']}."
                )
                missing_fingerprints_ids.add(deployments_report["id"])

            if deployments_report["cached_csv_file_path"] and not is_valid_cache_file(
                deployments_report["cached_csv_file_path"]
            ):
                self.write_warning(
                    f"{deployments_report['cached_csv_file_path']} is missing "
                    f"for DeploymentsReport {deployments_report['id']}."
                )
                missing_csv_ids.add(deployments_report["id"])

        return missing_fingerprints_ids, missing_csv_ids

    def generate_fingerprints(
        self, deployments_report_ids: set[int]
    ) -> tuple[list, list]:
        """Generate cached fingerprints for the given deployments report IDs."""
        success_ids = []
        failure_ids = []
        deployments_report_ids = sorted(list(deployments_report_ids))
        for _id in deployments_report_ids:
            deployments_report = DeploymentsReport.objects.get(pk=_id)
            self.write_info(f"Rerunning fingerprint task for {deployments_report}")
            try:
                deployments_report._rerun_latest_fingerprint(wait=True)
                success_ids.append(_id)
            except Exception as e:  # noqa: BLE001
                self.stdout.write(self.style.ERROR(str(e)))
                failure_ids.append(_id)

        return success_ids, failure_ids

    def generate_csvs(self, deployments_report_ids: set[int]) -> tuple[list, list]:
        """Generate cached CSV files for the given deployments report IDs."""
        success_ids = []
        failure_ids = []
        for _id in sorted(list(deployments_report_ids)):
            success = generate_and_save_cached_csv(_id)
            success_ids.append(_id) if success else failure_ids.append(_id)

        return success_ids, failure_ids

    def handle(self, *args, **options):
        """Handle this command."""
        missing_fingerprints_ids, missing_csv_ids = (
            self.find_reports_with_missing_cached_data()
        )

        fingerprint_successes, fingerprint_failures = self.generate_fingerprints(
            missing_fingerprints_ids
        )
        csv_successes, csv_failures = self.generate_csvs(missing_csv_ids)

        for _id in fingerprint_successes:
            self.write_success(
                f"Generated cached_fingerprints_file_path for DeploymentsReport {_id}"
            )
        for _id in fingerprint_failures:
            self.write_warning(
                "Failed to generate cached_fingerprints_file_path for "
                f"DeploymentsReport {_id}"
            )
        for _id in csv_successes:
            self.write_success(
                f"Generated cached_csv_file_path for DeploymentsReport {_id}"
            )
        for _id in csv_failures:
            self.write_warning(
                f"Failed to generate cached_csv_file_path for DeploymentsReport {_id}"
            )

        if fingerprint_failures or csv_failures:
            raise CommandError(
                f"Failed to generate {len(fingerprint_failures)} fingerprint files. "
                f"Failed to generate {len(csv_failures)} CSV files. "
            )
