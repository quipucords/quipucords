"""Dummy scan manager module - a replacement on [Scan]Manager for tests."""

import multiprocessing
from contextlib import contextmanager
from datetime import datetime
from multiprocessing import Process


@contextmanager
def set_mp_start_method(start_method):
    """Set the multiprocessing start method for the yielded block."""
    current_start_method = multiprocessing.get_start_method()
    try:
        multiprocessing.set_start_method(start_method, force=True)
        yield
    finally:
        multiprocessing.set_start_method(current_start_method, force=True)


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
        self._start_dt = None
        self.timeout_seconds = 15

    def put(self, job):
        """Add job to queue."""
        self._queue.append(job)

    def is_alive(self):
        """Check if DummyScanManager is 'alive'."""
        return True

    @property
    def _timed_out(self):
        elapsed_time = datetime.now() - self._start_dt
        if elapsed_time.seconds > self.timeout_seconds:
            return True
        return False

    def work(self):
        """Execute scan queue synchronously."""
        self._start_dt = datetime.now()
        if self._timed_out:
            return
        while self._queue:
            current_job: Process = self._queue.pop()
            # Some uses of the Scan manager's work() attempts to fetch data
            # from OpenShift. In such test cases, we Mock the OpenShiftApi.
            # Note that Mocks do not work on MacOS as the default invocation
            # method is spawn instead of a fork. If using spawn, a new Python
            # interpreter is launched in which the Mocks are not honored so
            # we need to invoke the tested code via fork.
            with set_mp_start_method("fork"):
                current_job.start()
            while current_job.exitcode is None:
                if self._timed_out:
                    current_job.kill()
                    return

    def kill(self, job, command):  # pylint: disable=unused-argument
        """Mimic ScanManager kill method signature."""
