"""Quipucords/pydantic compatibility layer."""

# If you ever attempt to run this module on it's own it won't work because it shadows
# pydantic package (python interpreter will probably complain about circular imports).
# Running as part of compat package (like from `compat.pydantic import blabla`) will
# work as intended.
# Why make this choice then? well, naming things is hard. Calling this module
# "compat.pydantic" makes sense and makes it easy to find.

from pydantic import BaseModel as _BaseModel


class PydanticErrorProxy:
    """
    Pydantic Error class.

    Exceptions created with `raises` decorator will inherit from this one.
    """


def _error_proxy_encoder(error):
    return error.json()


class BaseModel(_BaseModel):
    """pydantic BaseModel with custom configuration for quipucords."""

    class Config:
        """pydantic model config."""

        json_encoders = {PydanticErrorProxy: _error_proxy_encoder}


def raises(error: Exception):
    """
    Allow exceptions to behave as pydantic models.

    This contraption is required because it is impossible to have an class
    inheriting both from `Exception` and pydantic `BaseModel` (metaclass conflict).

    Error attributes/methods have precedence over model. Be mindful about that.

    Highly based on this suggestion:
    https://github.com/pydantic/pydantic/issues/1875#issuecomment-783459329
    """

    def wrap(model_class: type):
        if not hasattr(model_class, "__raise__"):
            raise TypeError("Class decorated with `raises` must implement `__raise__`")

        class ErrorProxyMeta(type):
            def __getattr__(cls, attr):
                return getattr(model_class, attr)

        class ErrorProxy(error, PydanticErrorProxy, metaclass=ErrorProxyMeta):
            _model_class = model_class

            def __init__(self, **data):
                self.model_instance = model_class(**data)
                super().__init__(*self.model_instance.__raise__())

            def __getattr__(self, attr):
                return getattr(self.model_instance, attr)

            def __str__(self) -> str:
                return str(self.model_instance)

        ErrorProxy.__name__ = f"{model_class.__name__}Exception"
        ErrorProxy.__qualname__ = f"{model_class.__qualname__}Exception"

        return ErrorProxy

    return wrap
