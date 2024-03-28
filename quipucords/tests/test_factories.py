"""factories to help testing Quipucords."""

from unittest import mock

import pytest

from api.models import DeploymentsReport, Source, SystemFingerprint
from constants import DataSources
from tests.factories import (
    DeploymentReportFactory,
    ReportFactory,
    SourceFactory,
)


@pytest.mark.django_db
class TestDeploymentsReportFactoryFingerprints:
    """Test DeploymentsReportFactory.number_of_fingerprints method."""

    @pytest.mark.parametrize(
        "factory_method", [DeploymentReportFactory.create, DeploymentReportFactory]
    )
    def test_create_setting_number(self, factory_method):
        """Test setting number_of fingerprints when creating a deployment report."""
        deployment_report = factory_method(number_of_fingerprints=10)
        assert len(deployment_report.system_fingerprints.all()) == 10
        assert DeploymentsReport.objects.all().count() == 1
        assert SystemFingerprint.objects.all().count() == 10

    def test_build_setting_number(self):
        """Check for failure when setting number of fingerprints with build method."""
        with pytest.raises(ValueError):
            DeploymentReportFactory.build(number_of_fingerprints=1)

    @mock.patch("tests.factories.random.randint", return_value=1)
    def test_create_with_defaults(self, patched_randint):
        """Test related fingerprint creation without default values."""
        DeploymentReportFactory.create()
        assert patched_randint.mock_calls == [mock.call(1, 5)]
        assert DeploymentsReport.objects.all().count() == 1
        assert SystemFingerprint.objects.all().count() == 1

    @mock.patch("tests.factories.random.randint")
    def test_build_with_defaults(self, patched_randint):
        """Check no fingerprints are created when using build."""
        instance = DeploymentReportFactory.build()
        assert patched_randint.mock_calls == []
        assert instance.id is None
        assert DeploymentsReport.objects.all().count() == 0
        assert SystemFingerprint.objects.all().count() == 0
        # saving deployment won't create fingerprints
        instance.save()
        assert instance.id
        assert SystemFingerprint.objects.all().count() == 0

    def test_create_batch_setting_number(self):
        """Test creating a bach of deployment reports also creates fingerprints."""
        instances = DeploymentReportFactory.create_batch(
            size=10, number_of_fingerprints=10
        )

        assert instances[0].system_fingerprints.count() == 10
        assert DeploymentsReport.objects.all().count() == 10
        assert SystemFingerprint.objects.all().count() == 100


@pytest.mark.django_db
class TestDeploymentReportFactoryReportID:
    """Test DeploymentReport.set_report_id post generation method."""

    @pytest.mark.parametrize(
        "factory_method", [DeploymentReportFactory, DeploymentReportFactory.create]
    )
    def test_create(self, factory_method):
        """Check report_id matches model pk."""
        deployments_report = factory_method()
        assert deployments_report.id

    def test_create_batch(self):
        """Check report_id matches model pk using create_batch method."""
        deployments_reports = DeploymentReportFactory.create_batch(size=2)
        assert all(d.id for d in deployments_reports)


@pytest.mark.django_db
class TestSourceFactory:
    """Test SourceFactory."""

    def test_default(self):
        """Test SourceFactory default behavior."""
        source = SourceFactory()
        assert isinstance(source, Source)
        assert source.id

    def test_default_ssl(self):
        """Test SourceFactory default ssl options set to none."""
        source = SourceFactory()
        assert isinstance(source, Source)
        assert source.id
        assert source.ssl_cert_verify is None
        assert source.disable_ssl is None
        assert source.use_paramiko is None


@pytest.mark.django_db
class TestReportFactory:
    """Test ReportFactory."""

    @pytest.mark.dbcompat
    @pytest.mark.parametrize("source_type", DataSources.values)
    def test_source_generation(self, source_type):
        """Test automatic generation of Details facts is not breaking anything."""
        report = ReportFactory(
            generate_raw_facts=True, generate_raw_facts__source_types=[source_type]
        )
        assert len(report.sources) == 1
        assert len(report.sources[0]["facts"]) > 1

    @pytest.mark.dbcompat
    def test_source_generation_qty_per_source(self, faker):
        """Test source generation quantity per source."""
        qty_per_source = faker.pyint(min_value=6, max_value=10)
        qty_of_sources = len(DataSources.names)
        report = ReportFactory(
            generate_raw_facts=True,
            generate_raw_facts__source_types=DataSources.values,
            generate_raw_facts__qty_per_source=qty_per_source,
        )
        assert len(report.sources) == qty_of_sources
        # we expect the +1 because of OpenShift type, which has an extra "system"
        expected_number_of_results = qty_of_sources * qty_per_source + 1
        assert (
            sum(len(source["facts"]) for source in report.sources)
            == expected_number_of_results
        )
