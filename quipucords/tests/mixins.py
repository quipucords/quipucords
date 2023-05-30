"""Mixins to help testing quipucords."""

from django.contrib.auth import get_user_model
from faker import Faker

fake = Faker()


class LoggedUserMixin:
    """Mixin that logs a qpc user to TestCases."""

    @classmethod
    def _create_user(cls):
        user = get_user_model()(username=fake.user_name())
        user.set_password(fake.password())
        user.save()
        return user

    def setUp(self):
        """Set up data for test case."""
        self.user = self._create_user()
        self.client.force_login(self.user)
