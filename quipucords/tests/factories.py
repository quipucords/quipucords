"""factories to help testing Quipucords."""
import random

import factory
from factory.django import DjangoModelFactory
from faker import Faker

from api import models
from api.status import get_server_id
from constants import DataSources


def format_sources(obj):
    """Format fingerprint sources.

    obj has access to params defined on SystemFingerprintFactory.Params
    """
    return [
        {
            "server_id": get_server_id(),
            "source_type": obj.source_type,
            "source_name": "testlab",
        }
    ]


def system_fingerprint_source_types():
    """Return default source types for fingerprints."""
    all_types = set(DataSources.values)
    # OpenShift/Ansible will be ignored by default for convenience on insights tests
    ignored_types = {DataSources.OPENSHIFT, DataSources.ANSIBLE}
    return all_types - ignored_types


class SystemFingerprintFactory(DjangoModelFactory):
    """SystemFingerprint factory."""

    name = factory.Faker("hostname")
    bios_uuid = factory.Faker("uuid4")
    os_release = "Red Hat Enterprise Linux release 8.5 (Ootpa)"
    ip_addresses = factory.LazyAttribute(lambda o: o.ip_addresses_list)
    architecture = factory.Iterator(["x86_64", "ARM"])
    sources = factory.LazyAttribute(format_sources)

    class Params:
        """Factory parameters."""

        source_type = factory.Iterator(system_fingerprint_source_types())
        ip_addresses_list = factory.List([factory.Faker("ipv4")])

    class Meta:
        """Factory options."""

        model = "api.SystemFingerprint"


class DeploymentReportFactory(DjangoModelFactory):
    """DeploymentReport factory."""

    details_report = factory.RelatedFactory(
        "tests.factories.DetailsReportFactory",
        factory_related_name="deployment_report",
    )
    report_version = "REPORT_VERSION"

    class Meta:
        """Factory options."""

        model = "api.DeploymentsReport"

    @factory.post_generation
    def number_of_fingerprints(obj, create, extracted, **kwargs):
        """Create fingerprints associated to deployment report instance."""
        if not create and not extracted:
            return
        if not create:
            raise ValueError(
                "Impossible to create related object in batch if not saved."
            )
        if extracted is None:
            extracted = random.randint(1, 5)
        SystemFingerprintFactory.create_batch(
            deployment_report=obj, size=extracted, **kwargs
        )

    @factory.post_generation
    def _set_report_id(obj, *args, **kwargs):
        """
        Reproduce the logic for report_id creation.

        Usually this type of thing could be with factory boy through lazy_attributes,
        but this would also require letting factory boy handling pk creation
        instead of deferring this responsibility to the database.
        """
        obj.report_id = obj.report_id or obj.pk  # noqa: W0201


class DetailsReportFactory(DjangoModelFactory):
    """Factory for DetailsReport."""

    deployment_report = factory.SubFactory(DeploymentReportFactory, details_report=None)
    scanjob = factory.RelatedFactory(
        "tests.factories.ScanJobFactory",
        factory_related_name="details_report",
    )

    class Meta:
        """Factory options."""

        model = "api.DetailsReport"


class JobConnectionResultFactory(DjangoModelFactory):
    """Factory for JobConnectionResult model."""

    class Meta:
        """Factory options."""

        model = models.JobConnectionResult


class JobInspectionResultFactory(DjangoModelFactory):
    """Factory for JobInspectionResult model."""

    class Meta:
        """Factory options."""

        model = models.JobInspectionResult


class ScanJobFactory(DjangoModelFactory):
    """Factory for ScanJob."""

    start_time = factory.Faker("past_datetime")
    end_time = factory.Faker("date_time_between", start_date="-15d")

    details_report = factory.SubFactory(DetailsReportFactory, scanjob=None)
    connection_results = factory.SubFactory(JobConnectionResultFactory)
    inspection_results = factory.SubFactory(JobInspectionResultFactory)

    class Meta:
        """Factory options."""

        model = "api.ScanJob"


class TaskConnectionResultFactory(DjangoModelFactory):
    """Factory for TaskConnectionResult model."""

    job_connection_result_id = factory.SelfAttribute("..job.connection_results_id")

    class Meta:
        """Factory options."""

        model = models.TaskConnectionResult


class TaskInspectionResultFactory(DjangoModelFactory):
    """Factory for TaskInspectionResult model."""

    job_inspection_result_id = factory.SelfAttribute("..job.inspection_results_id")

    class Meta:
        """Factory options."""

        model = models.TaskInspectionResult


class ScanTaskFactory(DjangoModelFactory):
    """Factory for ScanTask."""

    start_time = factory.Faker("past_datetime")
    end_time = factory.Faker("date_time_between", start_date="-15d")

    source = factory.SubFactory("tests.factories.SourceFactory")
    job = factory.SubFactory("tests.factories.ScanJobFactory")

    connection_result = factory.SubFactory(
        TaskConnectionResultFactory,
    )
    inspection_result = factory.SubFactory(TaskInspectionResultFactory)

    class Meta:
        """Factory options."""

        model = "api.ScanTask"


class CredentialFactory(DjangoModelFactory):
    """Factory for Credential model."""

    name = factory.Faker("slug")
    cred_type = factory.Iterator(DataSources.values)

    class Meta:
        """Factory options."""

        model = models.Credential

    @factory.lazy_attribute
    def auth_token(self):
        """Set auth_token lazily."""
        has_user_or_pass = bool(
            getattr(self, "username", None) or getattr(self, "password", None)
        )
        if self.cred_type == DataSources.OPENSHIFT and not has_user_or_pass:
            return Faker().password()
        return None


class SourceOptions(DjangoModelFactory):
    """Factory for SourceOptions model."""

    class Meta:
        """Factory options."""

        model = models.SourceOptions


class SourceFactory(DjangoModelFactory):
    """Factory for Source model."""

    name = factory.Faker("slug")
    source_type = factory.Iterator(DataSources.values)
    options = factory.SubFactory(SourceOptions)

    class Meta:
        """Factory options."""

        model = models.Source

    @classmethod
    def _create(cls, *args, **kwargs):
        """Override DjangoModelFactoy internal create method."""
        credentials = kwargs.pop("credentials", [])
        source = super()._create(*args, **kwargs)
        # simple M2M fields are not supported as attributes on factory boy, hence this
        source.credentials.add(*credentials)
        return source

    @factory.post_generation
    def number_of_credentials(obj: models.Source, create, extracted, **kwargs):
        """Create n credentials associated to Source."""
        if not create:
            return

        if not obj.credentials.count() and extracted is None:
            # if no credential was created, create at least one
            extracted = 1

        if extracted:
            credentials = [
                CredentialFactory(cred_type=obj.source_type) for _ in range(extracted)
            ]
            obj.credentials.add(*credentials)
