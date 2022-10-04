# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Test Source model methods."""

import pytest

from api.models import Credential, Source
from tests.factories import SourceFactory


@pytest.mark.django_db
def test_single_credential():
    """Test single_credential "green path"."""
    source: Source = SourceFactory()
    assert source.single_credential
    assert isinstance(source.single_credential, Credential)


@pytest.mark.django_db
def test_single_credential_with_multiple_credentials():
    """Test single_credential with multiple credentials."""
    source: Source = SourceFactory(number_of_credentials=10)
    with pytest.raises(Credential.MultipleObjectsReturned):
        source.single_credential  # pylint: disable=pointless-statement


@pytest.mark.django_db
def test_single_credential_without_credential():
    """Test single_credential property when source has no credential."""
    source: Source = SourceFactory(number_of_credentials=0)
    with pytest.raises(Credential.DoesNotExist):
        source.single_credential  # pylint: disable=pointless-statement
