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

    @pytest.mark.parametrize("source_type", DataSources.values)
    def test_source_generation(self, source_type):
        """Test automatic generation of Details facts is not breaking anything."""
        report = ReportFactory.build(source_types=[source_type], deployment_report=None)
        # report.id is None since it is not saved to db yet
        assert report.id is None
        assert len(report.sources) == 1
        assert len(report.sources[0]["facts"]) > 1
        # ensure data can be properly serialized and saved
        report.save()
        report.refresh_from_db()
        assert report.id
        assert len(report.sources) == 1
        assert len(report.sources[0]["facts"]) > 1
