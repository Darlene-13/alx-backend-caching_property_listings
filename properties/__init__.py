"""
Properties app initialization and configuration module.

This file tells Django to use our custom app configuration classs
which includes signal handlers for cache invalidation.
"""

default_app_config = 'properties.apps.PropertiesConfig'