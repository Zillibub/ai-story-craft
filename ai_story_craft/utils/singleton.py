"""Singleton meta-class."""


class Singleton(type):
    """Singleton meta-class."""

    _instances: dict = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

    def clear(cls):
        """Clear singleton instances."""
        cls._instances = {}
