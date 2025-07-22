from django.core.cache import cache
from django.core.serializers import serialize
from django.core.serializers.json import DjangoJSONEncoder
import json
import logging
from .models import Property

logger = logging.getLogger(__name__)


def get_all_properties():
    """
    Get all properties from cache or database.
    
    This function implements low-level caching using Django's cache API.
    It checks Redis for cached property data and fetches from database
    if not found, then caches the result for 1 hour.
    
    Returns:
        QuerySet: All Property objects
    """
    cache_key = 'all_properties'
    
    # Try to get properties from cache
    cached_properties = cache.get(cache_key)
    
    if cached_properties is not None:
        logger.info("Properties retrieved from cache")
        return cached_properties
    
    # If not in cache, fetch from database
    logger.info("Properties not found in cache, fetching from database")
    queryset = Property.objects.all().order_by('-created_at')
    
    # Convert queryset to list to make it serializable for caching
    properties_list = list(queryset)
    
    # Store in cache for 1 hour (3600 seconds)
    cache.set(cache_key, properties_list, 3600)
    logger.info(f"Cached {len(properties_list)} properties for 1 hour")
    
    return properties_list


def invalidate_properties_cache():
    """
    Invalidate the properties cache.
    
    This function should be called whenever properties are
    created, updated, or deleted to ensure cache consistency.
    """
    cache_key = 'all_properties'
    cache.delete(cache_key)
    logger.info("Properties cache invalidated")


def get_property_by_id(property_id):
    """
    Get a specific property by ID with caching.
    
    Args:
        property_id (int): The ID of the property to retrieve
        
    Returns:
        Property: The property object or None if not found
    """
    cache_key = f'property_{property_id}'
    
    # Try to get property from cache
    cached_property = cache.get(cache_key)
    
    if cached_property is not None:
        logger.info(f"Property {property_id} retrieved from cache")
        return cached_property
    
    # If not in cache, fetch from database
    try:
        property_obj = Property.objects.get(id=property_id)
        
        # Store in cache for 30 minutes (1800 seconds)
        cache.set(cache_key, property_obj, 1800)
        logger.info(f"Property {property_id} cached for 30 minutes")
        
        return property_obj
    except Property.DoesNotExist:
        logger.warning(f"Property {property_id} not found")
        return None


def get_properties_by_location(location):
    """
    Get properties filtered by location with caching.
    
    Args:
        location (str): The location to filter properties by
        
    Returns:
        list: List of Property objects in the specified location
    """
    cache_key = f'properties_location_{location.lower().replace(" ", "_")}'
    
    # Try to get properties from cache
    cached_properties = cache.get(cache_key)
    
    if cached_properties is not None:
        logger.info(f"Properties for location '{location}' retrieved from cache")
        return cached_properties
    
    # If not in cache, fetch from database
    queryset = Property.objects.filter(
        location__icontains=location
    ).order_by('-created_at')
    
    properties_list = list(queryset)
    
    # Store in cache for 45 minutes (2700 seconds)
    cache.set(cache_key, properties_list, 2700)
    logger.info(f"Cached {len(properties_list)} properties for location '{location}'")
    
    return properties_list


def cache_statistics():
    """
    Get cache statistics for monitoring.
    
    Returns:
        dict: Cache statistics including hit/miss ratios
    """
    try:
        # Test cache connectivity
        cache.set('cache_test', 'test_value', 10)
        test_result = cache.get('cache_test')
        
        return {
            'cache_connected': test_result == 'test_value',
            'cache_backend': cache.__class__.__name__,
            'all_properties_cached': cache.get('all_properties') is not None,
        }
    except Exception as e:
        logger.error(f"Cache statistics error: {e}")
        return {
            'cache_connected': False,
            'error': str(e)
        }