"""Dummy scan manager module - a replacement on [Scan]Manager for tests."""

from scanner.job import ScanJobRunner


class SingletonMeta(type):
    """
    Metaclass designed to force classes to behave as singletons.

    Shamelesly copied from https://refactoring.guru/design-patterns/singleton
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """Return class instance."""
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class DummyScanManager(metaclass=SingletonMeta):
    """ScanManager for testing purposes."""

    def __init__(self):
        """Inititialize DummyScanManager."""
        self._queue = []

    def put(self, job):
        """Add job to queue."""
        self._queue.append(job)

    def is_alive(self):
        """Check if DummyScanManager is 'alive'."""
        return True

    def work(self):
        """Execute scan queue synchronously."""
        while self._queue:
            job_runner: ScanJobRunner = self._queue.pop()
            job_runner.start()

    def kill(self, job, command):
        """Mimic ScanManager kill method signature."""
