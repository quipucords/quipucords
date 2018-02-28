#
# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Test util for the scan features."""

from api.models import (Scan,
                        ScanOptions,
                        ExtendedProductSearchOptions,
                        DisableOptionalProductsOptions,
                        ScanTask,
                        ScanJob)


def create_scan_job(source,
                    scan_type=ScanTask.SCAN_TYPE_CONNECT,
                    scan_name='test',
                    scan_options=None):
    """Create a new scan job.

    :param source: the source for the scan job
    :param scan_type: Either connect or inspect
    :param scan_options: Job scan options
    :return: the scan job and task
    """
    # Create scan configuration
    scan = Scan(name=scan_name,
                scan_type=scan_type)
    scan.save()

    # Add source to scan
    if source is not None:
        scan.sources.add(source)

    # Add options to scan
    options_to_use = scan_options
    if options_to_use is None:
        extended_options = ExtendedProductSearchOptions()
        extended_options.save()
        optional_products = DisableOptionalProductsOptions()
        optional_products.save()
        options_to_use = ScanOptions(
            disable_optional_products=optional_products,
            enabled_extended_product_search=extended_options)
        options_to_use.save()

    scan.options = options_to_use
    scan.save()

    # Create Job
    scan_job = ScanJob(scan=scan)
    scan_job.save()

    scan_job.queue()

    scan_task = scan_job.tasks.first()
    if scan_type == ScanTask.SCAN_TYPE_INSPECT:
        scan_task.complete()
        scan_task = scan_job.tasks.last()

    return scan_job, scan_task
