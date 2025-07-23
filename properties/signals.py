"""
Django signals for automatic cache invalidation.

This module contains signal handlers that automatically clear
cached property data when properties are created, updated, or deleted.

Signals ensure that cached data remains fresh and consistent
with the database state.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Property
from .utils import CACHE_KEYS
import logging

# Set up logging for signal operations
logger = logging.getLogger(__name__)


@receiver(post_save, sender=Property)
def invalidate_cache_on_property_save(sender, instance, created, **kwargs):
    """
    Signal handler for Property post_save.
    
    This function is automatically called after a Property is saved (created or updated).
    
    Args:
        sender: The model class (Property)
        instance: The actual Property instance that was saved
        created: Boolean indicating if this was a CREATE (True) or UPDATE (False)
        **kwargs: Additional signal arguments
    """
    action = "created" if created else "updated"
    
    logger.info(f"Property {action}: {instance.title} (ID: {instance.id})")
    logger.info("Invalidating property cache due to post_save signal")
    
    # Clear the all_properties cache
    cache.delete(CACHE_KEYS['ALL_PROPERTIES'])
    
    # Also clear the property count cache since it might have changed
    cache.delete(CACHE_KEYS['PROPERTY_COUNT'])
    
    # Clear any page-level caches that might exist
    # Note: Page caches have complex keys, so we'll let them expire naturally
    # or use cache.clear() for a complete flush (be careful in production)
    
    logger.info(f"Cache invalidated after property {action}")


@receiver(post_delete, sender=Property)
def invalidate_cache_on_property_delete(sender, instance, **kwargs):
    """
    Signal handler for Property post_delete.
    
    This function is automatically called after a Property is deleted.
    
    Args:
        sender: The model class (Property)
        instance: The Property instance that was deleted
        **kwargs: Additional signal arguments
    """
    logger.info(f"Property deleted: {instance.title} (ID: {instance.id})")
    logger.info("Invalidating property cache due to post_delete signal")
    
    # Clear the all_properties cache
    cache.delete(CACHE_KEYS['ALL_PROPERTIES'])
    
    # Also clear the property count cache since it definitely changed
    cache.delete(CACHE_KEYS['PROPERTY_COUNT'])
    
    logger.info("Cache invalidated after property deletion")


def clear_all_property_caches():
    """
    Utility function to clear all property-related caches.
    
    This function can be called manually when needed, or from other parts
    of the application that might affect property data.
    """
    logger.info("Manually clearing all property caches")
    
    caches_cleared = []
    
    # Clear queryset caches
    for cache_key in CACHE_KEYS.values():
        try:
            cache.delete(cache_key)
            caches_cleared.append(cache_key)
            logger.info(f"Cleared cache key: {cache_key}")
        except Exception as e:
            logger.error(f"Error clearing cache key {cache_key}: {str(e)}")
    
    return caches_cleared


# Additional signal handlers for related models (if you add them later)
# For example, if you have a Category model related to Property:

# @receiver(post_save, sender=Category)
# def invalidate_cache_on_category_change(sender, instance, **kwargs):
#     """Clear property cache when categories change since they might affect property lists"""
#     logger.info(f"Category changed: {instance.name}, clearing property cache")
#     cache.delete(CACHE_KEYS['ALL_PROPERTIES'])


# You can also create more granular cache invalidation
# For example, cache by location or price range:

def invalidate_location_cache(location):
    """
    Clear cache for a specific location.
    
    Useful if you implement location-specific caching in the future.
    """
    cache_key = f"properties_location_{location.lower().replace(' ', '_')}"
    cache.delete(cache_key)
    logger.info(f"Cleared location cache for: {location}")


def invalidate_price_range_cache(min_price, max_price):
    """
    Clear cache for a specific price range.
    
    Useful if you implement price-range specific caching in the future.
    """
    cache_key = f"properties_price_{min_price}_{max_price}"
    cache.delete(cache_key)
    logger.info(f"Cleared price range cache: ${min_price} - ${max_price}")


# Signal for debugging - logs all cache operations
@receiver(post_save, sender=Property)
def log_property_change(sender, instance, created, **kwargs):
    """
    Additional signal handler for logging property changes.
    
    This helps with debugging and monitoring property operations.
    """
    action = "created" if created else "updated"
    logger.info(
        f"Property {action} - "
        f"Title: {instance.title}, "
        f"Location: {instance.location}, "
        f"Price: ${instance.price}"
    )