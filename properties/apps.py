"""
Django app configuration for the properties app.

This module configures the properties app and ensures that
signal handlers are imported and registered when Django starts.
"""

from django.apps import AppConfig


class PropertiesConfig(AppConfig):
    """
    Configuration for the properties app.
    
    This class defines the app configuration and handles
    initialization tasks like importing signal handlers.
    """
    
    # Use BigAutoField for primary keys (Django 3.2+)
    default_auto_field = 'django.db.models.BigAutoField'
    
    # App name - should match the app directory name
    name = 'properties'
    
    # Human-readable name for the app (appears in Django admin)
    verbose_name = 'Property Listings'

    def ready(self):
        """
        Called when Django starts and the app is ready.
        
        This method is the perfect place to import signal handlers
        to ensure they are registered with Django's signal dispatcher.
        
        IMPORTANT: This method can be called multiple times during
        Django's startup, so make sure any code here is safe to run
        multiple times.
        """
        try:
            # Import signal handlers
            # This registers the @receiver decorated functions with Django
            from . import signals
            
            # Optional: You can also import specific signal functions if needed
            # from .signals import invalidate_cache_on_property_save, invalidate_cache_on_property_delete
            
            # Log that signals have been imported (optional, for debugging)
            import logging
            logger = logging.getLogger(__name__)
            logger.info("Property signals imported and registered successfully")
            
        except ImportError as e:
            # Log any import errors for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error importing property signals: {str(e)}")
            
            # Re-raise the error so Django knows something went wrong
            raise
        
        except Exception as e:
            # Catch any other errors during signal registration
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Unexpected error during signal registration: {str(e)}")
            raise