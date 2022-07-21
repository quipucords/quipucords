# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""factories to help testing Quipucords."""
import random

import factory
from factory.django import DjangoModelFactory


class SystemFingerprintFactory(DjangoModelFactory):
    """SystemFingerprint factory."""

    name = factory.Faker("hostname")
    os_name = "Red Hat Enterprise Linux"
    ip_addresses = factory.List([factory.Faker("ipv4")])
    architecture = factory.Iterator(["x86_64", "ARM"])

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


class ScanJobFactory(DjangoModelFactory):
    """Factory for ScanJob."""

    start_time = factory.Faker("past_datetime")
    end_time = factory.Faker("date_time_between", start_date="-15d")

    details_report = factory.SubFactory(DetailsReportFactory, scanjob=None)

    class Meta:
        """Factory options."""

        model = "api.ScanJob"
