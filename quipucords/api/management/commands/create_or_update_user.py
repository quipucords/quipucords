"""Create or update user credentials."""

from argparse import RawTextHelpFormatter
from os import environ
from textwrap import dedent

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from quipucords.user import create_or_update_user

User = get_user_model()

DEFAULT_USERNAME = "admin"
DEFAULT_EMAIL = "admin@example.com"


class Command(BaseCommand):
    """
    Management command for (re)setting user credentials.

    Creates or updates the user based on the following environment variables:

    * QPC_SERVER_USERNAME (default: "{DEFAULT_USERNAME}")
    * QPC_SERVER_EMAIL (default: "{DEFAULT_EMAIL}")
    * QPC_SERVER_PASSWORD
    """

    help = dedent(
        __doc__.format(DEFAULT_USERNAME=DEFAULT_USERNAME, DEFAULT_EMAIL=DEFAULT_EMAIL)
    )
    requires_migrations_checks = True

    def create_parser(self, *args, **kwargs):
        """Reconfigure the parser to allow line breaks in the help text."""
        parser = super(Command, self).create_parser(*args, **kwargs)
        parser.formatter_class = RawTextHelpFormatter
        return parser

    def handle(self, *args, **options):
        """Execute the logic for this command."""
        username = environ.get("QPC_SERVER_USERNAME", DEFAULT_USERNAME)
        email = environ.get("QPC_SERVER_USER_EMAIL", DEFAULT_EMAIL)
        password = environ.get("QPC_SERVER_PASSWORD")

        created, updated, generated_password = create_or_update_user(
            username, email, password
        )

        if created or updated:
            if password and generated_password and password != generated_password:
                message = (
                    "QPC_SERVER_PASSWORD value failed password requirements. "
                    "Using a randomly generated password instead."
                )
                self.stdout.write(self.style.WARNING(message))
            verb = "Created" if created else "Updated"
            password_description = (
                f"random password: {generated_password}"
                if generated_password
                else "password from QPC_SERVER_PASSWORD"
            )
            message = f"{verb} user '{username}' with {password_description}"
            self.stdout.write(self.style.SUCCESS(message))
        else:
            message = f"User '{username}' already exists and was not updated."
            self.stdout.write(self.style.WARNING(message))
