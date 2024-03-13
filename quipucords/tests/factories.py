"""factories to help testing Quipucords."""

import random

import factory
from factory.django import DjangoModelFactory
from faker import Faker

from api import models
from api.serializers import SystemFingerprintSerializer
from api.status import get_server_id
from constants import DataSources
from tests.utils import fake_rhel, raw_facts_generator
from tests.utils.raw_facts_generator import fake_installed_products

_faker = Faker()


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
    ignored_types = {DataSources.OPENSHIFT, DataSources.ANSIBLE, DataSources.RHACS}
    return all_types - ignored_types


def generate_details_sources(obj):
    """Return raw facts for details report depending on source_type."""
    sources_list = []
    for source_type in obj.source_types:
        source = {
            "server_id": _faker.uuid4(),
            "source_name": _faker.slug(),
            "source_type": source_type,
            "report_version": _faker.uuid4(),
            "facts": list(raw_facts_generator(source_type, obj.facts_per_source)),
        }
        sources_list.append(source)
    return sources_list


class SystemFingerprintFactory(DjangoModelFactory):
    """SystemFingerprint factory."""

    name = factory.Faker("hostname")
    bios_uuid = factory.Faker("uuid4")
    os_release = factory.LazyFunction(fake_rhel)
    ip_addresses = factory.LazyAttribute(lambda o: o.ip_addresses_list)
    architecture = factory.Iterator(["x86_64", "ARM"])
    sources = factory.LazyAttribute(format_sources)
    installed_products = factory.LazyFunction(fake_installed_products)

    class Params:
        """Factory parameters."""

        source_type = factory.Iterator(system_fingerprint_source_types())
        ip_addresses_list = factory.List([factory.Faker("ipv4")])

    class Meta:
        """Factory options."""

        model = "api.SystemFingerprint"


class DeploymentReportFactory(DjangoModelFactory):
    """DeploymentReport factory."""

    report = factory.RelatedFactory(
        "tests.factories.ReportFactory",
        factory_related_name="deployment_report",
    )
    report_version = "REPORT_VERSION"
    status = models.DeploymentsReport.STATUS_COMPLETE

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
    def _set_cached_fingerprints(obj, *args, **kwargs):
        """Reproduce the logic responsible for DUPLICATION of fingerprints."""
        # only attempt to generate fingerprints for obj already saved to db
        # and with a "STATUS_COMPLETE"
        if obj.id and obj.status == models.DeploymentsReport.STATUS_COMPLETE:
            # TODO get RID of this OUTRAGEOUS logic.
            serializer = SystemFingerprintSerializer(
                obj.system_fingerprints.all(), many=True
            )
            # <rant> cached_fingerprints are the salt of earth </rant>
            # cached fingerprints is required for tests involving csv generation
            obj.cached_fingerprints = serializer.data


class ReportFactory(DjangoModelFactory):
    """Factory for Report."""

    deployment_report = factory.SubFactory(DeploymentReportFactory, report=None)
    scanjob = factory.RelatedFactory(
        "tests.factories.ScanJobFactory",
        factory_related_name="report",
    )
    sources = factory.LazyAttribute(generate_details_sources)

    class Meta:
        """Factory options."""

        model = "api.Report"

    class Params:
        """Factory parameters."""

        source_types = factory.Faker("random_elements", elements=DataSources.values)
        facts_per_source = factory.Faker("pyint", min_value=2, max_value=10)


class JobConnectionResultFactory(DjangoModelFactory):
    """Factory for JobConnectionResult model."""

    class Meta:
        """Factory options."""

        model = models.JobConnectionResult


class ScanJobFactory(DjangoModelFactory):
    """Factory for ScanJob."""

    start_time = factory.Faker("past_datetime")
    end_time = factory.Faker("date_time_between", start_date="-15d")

    report = factory.SubFactory(ReportFactory, scanjob=None)
    connection_results = factory.SubFactory(JobConnectionResultFactory)

    class Meta:
        """Factory options."""

        model = "api.ScanJob"


class ScanFactory(DjangoModelFactory):
    """Factory for Scan."""

    name = factory.Faker("bothify", text="Scan ????-######")
    scan_type = models.ScanTask.SCAN_TYPE_INSPECT
    most_recent_scanjob = factory.SubFactory(ScanJobFactory)

    class Meta:
        """Factory options."""

        model = "api.Scan"

    @classmethod
    def _create(cls, *args, **kwargs):
        """Override DjangoModelFactory internal create method."""
        sources = kwargs.pop("sources", [])
        scan = super()._create(*args, **kwargs)
        # simple M2M fields are not supported as attributes on factory boy, hence this
        scan.sources.add(*sources)
        if scan.most_recent_scanjob:
            # set scan x scanjob relationship (dear future reader: this was tried - and
            # miserably failed - with factory.SelfAttribute or factory.LazyAttribute)
            scan.most_recent_scanjob.scan = scan
            scan.most_recent_scanjob.save()
        return scan

    @factory.post_generation
    def number_of_sources(obj: models.Scan, create, extracted, **kwargs):
        """Create n sources associated to Scan."""
        if not create:
            return

        if not obj.sources.count() and extracted is None:
            # if no source was created, create at least one
            extracted = 1

        if extracted:
            sources = [SourceFactory() for _ in range(extracted)]
            obj.sources.add(*sources)


class TaskConnectionResultFactory(DjangoModelFactory):
    """Factory for TaskConnectionResult model."""

    job_connection_result_id = factory.SelfAttribute("..job.connection_results_id")

    class Meta:
        """Factory options."""

        model = models.TaskConnectionResult


class ScanTaskFactory(DjangoModelFactory):
    """Factory for ScanTask."""

    start_time = factory.Faker("past_datetime")
    end_time = factory.Faker("date_time_between", start_date="-15d")

    source = factory.SubFactory("tests.factories.SourceFactory")
    job = factory.SubFactory("tests.factories.ScanJobFactory")

    connection_result = factory.SubFactory(
        TaskConnectionResultFactory,
    )

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
            return _faker.password()
        return None


class SourceFactory(DjangoModelFactory):
    """Factory for Source model."""

    name = factory.Faker("slug")
    source_type = factory.Iterator(DataSources.values)

    class Meta:
        """Factory options."""

        model = models.Source

    @classmethod
    def _create(cls, *args, **kwargs):
        """Override DjangoModelFactory internal create method."""
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


class InspectResultFactory(DjangoModelFactory):
    """Factory for InspectResultFactory."""

    name = factory.Faker("ipv4")

    class Meta:
        """Factory options."""

        model = "api.InspectResult"


def generate_invalid_id(faker: factory.Faker) -> int:
    """Return a large number that likely does not exist as a real model object id."""
    return faker.pyint(min_value=990000, max_value=999999)


def generate_openssh_pkey(faker: factory.Faker) -> str:
    """Generate a random OpenSSH private key."""
    pkey = "-----BEGIN OPENSSH EXAMPLE KEY-----\n"
    for __ in range(5):
        pkey += f"{faker.lexify('?' * 70)}\n"
    pkey += "-----END OPENSSH EXAMPLE KEY-----\n"
    return pkey
