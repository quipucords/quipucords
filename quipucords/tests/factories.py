"""factories to help testing Quipucords."""

# all factory.post_generate methods here will inevitably trigger a false positive for
# "invalid-first-argument-name-for-method" (N805) check. let's simply disable it
# completely for this file to avoid repetition.
# ruff: noqa: N805

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

    class Meta:
        """Factory options."""

        model = "api.Report"

    @factory.post_generation
    def scanjob(obj: models.Report, create: bool, extracted: models.ScanJob, **kwargs):
        """Add ScanJob instance to Report."""
        if not create:
            return
        if extracted:
            extracted.report = obj
            extracted.save()
            return
        ScanJobFactory(report=obj)

    @staticmethod
    def get_or_create_inspect_task(report: models.Report):
        """Get or create a inspect task."""
        try:
            scan_job = report.scanjob
        except models.Report.scanjob.RelatedObjectDoesNotExist:
            scan_job = ScanJobFactory(report=None)
            scan_job.report = report
            scan_job.save()

        scan_task = (
            scan_job.tasks.filter(scan_type=models.ScanTask.SCAN_TYPE_INSPECT)
            .order_by("sequence_number")
            .first()
        )

        if not scan_task:
            scan_task = ScanTaskFactory(
                job=scan_job, scan_type=models.ScanTask.SCAN_TYPE_INSPECT
            )
        return scan_task

    @factory.post_generation
    def generate_raw_facts(
        obj: models.Report, create: bool, extracted: list[DataSources], **kwargs
    ):
        """Create RawFacts with the "extracted" source types."""
        if not create or not extracted:
            return
        source_types = kwargs.get("source_types") or _faker.random_elements(
            DataSources.values
        )
        fact_number = _faker.pyint(min_value=2, max_value=10)

        scan_task = ReportFactory.get_or_create_inspect_task(obj)
        for source_type in source_types:
            inspect_group = InspectGroupFactory(source_type=source_type)
            inspect_group.tasks.add(scan_task)
            for fact_dict in raw_facts_generator(source_type, fact_number):
                inspect_result = InspectResultFactory(inspect_group=inspect_group)
                raw_facts = [
                    models.RawFact(name=k, value=v, inspect_result=inspect_result)
                    for k, v in fact_dict.items()
                ]
                models.RawFact.objects.bulk_create(raw_facts)

    @factory.post_generation
    def sources(obj: models.Report, create: bool, extracted: list[dict], **kwargs):
        """Import "sources" (same as old details report "source") as RawFacts."""
        if not create or not extracted:
            return
        scan_task = ReportFactory.get_or_create_inspect_task(obj)
        for source_dict in extracted:
            inspect_group = InspectGroupFactory(
                source_type=source_dict["source_type"],
                source_name=source_dict["source_name"],
                server_id=source_dict["server_id"],
                server_version=source_dict["report_version"],
            )
            inspect_group.tasks.add(scan_task)
            for fact_dict in source_dict["facts"]:
                inspect_result = InspectResultFactory(inspect_group=inspect_group)
                raw_facts = [
                    models.RawFact(name=k, value=v, inspect_result=inspect_result)
                    for k, v in fact_dict.items()
                ]
                models.RawFact.objects.bulk_create(raw_facts)


class JobConnectionResultFactory(DjangoModelFactory):
    """Factory for JobConnectionResult model."""

    class Meta:
        """Factory options."""

        model = models.JobConnectionResult


class ScanJobFactory(DjangoModelFactory):
    """Factory for ScanJob."""

    start_time = factory.Faker("past_datetime")
    end_time = factory.Faker("date_time_between", start_date="-15d")

    connection_results = factory.SubFactory(JobConnectionResultFactory)

    class Meta:
        """Factory options."""

        model = "api.ScanJob"

    @factory.post_generation
    def report(obj: models.ScanJob, create: bool, extracted: models.Report, **kwargs):
        """Add a report to created ScanJob."""
        if not create:
            return
        if extracted:
            obj.report = extracted
            obj.save()
            return


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

    scan_type = models.ScanTask.SCAN_TYPE_INSPECT
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

    @factory.post_generation
    def with_raw_facts(
        obj: models.ScanTask, create: bool, extracted: list[dict], **kwargs
    ):
        """Import raw facts to this ScanTask instance."""
        if not create or not extracted:
            return

        inspect_group = InspectGroupFactory()
        inspect_group.tasks.add(obj)
        for fact_dict in extracted:
            inspect_result = InspectResultFactory(inspect_group=inspect_group)
            raw_facts = [
                models.RawFact(name=k, value=v, inspect_result=inspect_result)
                for k, v in fact_dict.items()
            ]
            models.RawFact.objects.bulk_create(raw_facts)


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


class InspectGroupFactory(DjangoModelFactory):
    """Factory for InspectGroupFactory."""

    source_name = factory.Faker("ipv4")
    source_type = factory.Faker("random_element", elements=DataSources.values)
    server_id = factory.Faker("uuid4")
    server_version = factory.Faker("bothify", text="#.#.##+????????")

    class Meta:
        """Factory options."""

        model = "api.InspectGroup"


class InspectResultFactory(DjangoModelFactory):
    """Factory for InspectResultFactory."""

    name = factory.Faker("ipv4")
    inspect_group = factory.SubFactory(InspectGroupFactory)

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
