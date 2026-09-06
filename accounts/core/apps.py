from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configuration for the academic-year module."""

    name = 'accounts.core'
    # Keep the existing collection/content-type namespace as ``core``.
    label = 'core'
