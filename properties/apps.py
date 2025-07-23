from django.apps import AppConfig
import logging

class PropertiesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'properties'
    verbose_name = 'Property Listings'

    def ready(self):
        """
        Register signal handlers when the app is ready.
        This ensures they are connected to Django's signal dispatcher.
        """
        try:
            import properties.signals  # ✅ THIS IS REQUIRED
            logger = logging.getLogger(__name__)
            logger.info("Property signals imported and registered successfully.")
        except ImportError as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to import signals module: {e}")
            raise
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Unexpected error during signal registration: {e}")
            raise

    def __str__(self):
        return self.verbose_name

    def get_version(self):
        return "1.0.0"

    def get_description(self):
        return "This app manages property listings and related functionality."
