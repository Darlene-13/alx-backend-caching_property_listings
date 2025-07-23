"""
Django app configuration for the properties app.

This module configures the properties app and ensures that
signal handlers are imported and registered when Django starts.
"""

import logging
from django.apps import AppConfig


class PropertiesConfig(AppConfig):
    """
    Configuration for the properties app.
    
    This class defines the app configuration and handles
    initialization tasks like importing signal handlers.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'properties'
    verbose_name = 'Property Listings'

    def ready(self):
        """
        Called when Django starts and the app is ready.

        This method is used to import and register signal handlers
        safely with Django's signal dispatcher.
        """
        try:
            # Import signal handlers to register them
            from . import signals

            logger = logging.getLogger(__name__)
            logger.info("Property signals imported and registered successfully")

        except ImportError as e:
            logger = logging.getLogger(__name__)
            logger.error(f"ImportError while importing property signals: {str(e)}")
            raise

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Unexpected error during signal registration: {str(e)}")
            raise

    def __str__(self):
        """
        String representation of the app configuration.

        Returns:
            str: Human-readable name of the app.
        """
        return self.verbose_name

    def get_version(self):
        """
        Get the current version of the properties app.

        Returns:
            str: The current version of the app.
        """
        return "1.0.0"

    def get_description(self):
        """
        Get a brief description of the properties app.

        Returns:
            str: A brief description of the app.
        """
        return "This app manages property listings and related functionality."
