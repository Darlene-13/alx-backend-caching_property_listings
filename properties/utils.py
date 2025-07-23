"""
Utility functions for property caching and data management.

This module contains functions that implement low-level caching
using Django's cache framework with Redis backend.
"""

from django.core.cache import cache
from django.db import models
from .models import Property
import logging

# Set up logging for cache operations
logger = logging.getLogger(__name__)

# Cache keys - centralized for easy management
CACHE_KEYS = {
    'ALL_PROPERTIES': 'all_properties',
    'PROPERTY_COUNT': 'property_count',
}

# Cache timeouts (in seconds)
CACHE_TIMEOUTS = {
    'PROPERTIES': 3600,  # 1 hour (60 * 60)
    'COUNT': 1800,       # 30 minutes (60 * 30)
}


def get_all_properties():
    """
    Get all properties with Redis caching for 1 hour.
    
    This function implements Django's low-level cache API to:
    1. Check if properties are already cached in Redis
    2. If cached data exists, return it (fast path)
    3. If no cached data, fetch from database
    4. Store the fresh data in Redis for 1 hour
    5. Return the queryset
    
    Returns:
        QuerySet: All Property objects, either from cache or database
    """
    cache_key = CACHE_KEYS['ALL_PROPERTIES']
    
    # Step 1: Try to get cached data from Redis
    logger.info(f"Checking cache for key: {cache_key}")
    cached_properties = cache.get(cache_key)
    
    if cached_properties is not None:
        logger.info("Cache HIT: Returning cached properties")
        return cached_properties
    
    # Step 2: Cache miss - fetch from database
    logger.info("Cache MISS: Fetching properties from database")
    
    # Fetch all properties, ordered by creation date (newest first)
    # Using select_related() if you have foreign keys, or prefetch_related() for many-to-many
    queryset = Property.objects.all().order_by('-created_at')
    
    # Convert QuerySet to list to make it cacheable
    # QuerySets are lazy and can't be pickled (cached) directly
    properties_list = list(queryset)
    
    # Step 3: Store in Redis cache for 1 hour (3600 seconds)
    cache_timeout = CACHE_TIMEOUTS['PROPERTIES']
    cache.set(cache_key, properties_list, cache_timeout)
    
    logger.info(f"Cached {len(properties_list)} properties for {cache_timeout} seconds")
    
    return properties_list


def get_property_count():
    """
    Get total property count with caching.
    
    Separate function for count to avoid loading all objects
    when we only need the count.
    
    Returns:
        int: Total number of properties
    """
    cache_key = CACHE_KEYS['PROPERTY_COUNT']
    
    # Check cache first
    cached_count = cache.get(cache_key)
    
    if cached_count is not None:
        logger.info("Cache HIT: Returning cached property count")
        return cached_count
    
    # Cache miss - get count from database
    logger.info("Cache MISS: Fetching property count from database")
    count = Property.objects.count()
    
    # Cache for 30 minutes
    cache.set(cache_key, count, CACHE_TIMEOUTS['COUNT'])
    
    logger.info(f"Cached property count: {count}")
    return count


def invalidate_property_cache():
    """
    Invalidate (clear) all property-related cache entries.
    
    Call this function when properties are added, updated, or deleted
    to ensure cached data stays fresh.
    
    This function is also called automatically by Django signals.
    
    Returns:
        dict: Information about what caches were cleared
    """
    cleared_caches = []
    errors = []
    
    try:
        # Delete specific cache keys
        for cache_name, cache_key in CACHE_KEYS.items():
            try:
                result = cache.delete(cache_key)
                cleared_caches.append({
                    'name': cache_name,
                    'key': cache_key,
                    'cleared': result  # True if key existed and was deleted
                })
                logger.info(f"Cache cleared: {cache_name} ({cache_key})")
            except Exception as e:
                error_msg = f"Error clearing {cache_name}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        logger.info("Property cache invalidation completed")
        
        return {
            'success': len(errors) == 0,
            'cleared_caches': cleared_caches,
            'errors': errors,
            'total_cleared': len(cleared_caches)
        }
        
    except Exception as e:
        error_msg = f"Critical error during cache invalidation: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'cleared_caches': cleared_caches,
            'errors': [error_msg],
            'total_cleared': len(cleared_caches)
        }


def get_cache_info():
    """
    Get information about current cache status.
    
    Useful for debugging and monitoring cache performance.
    
    Returns:
        dict: Cache status information
    """
    return {
        'all_properties_cached': cache.get(CACHE_KEYS['ALL_PROPERTIES']) is not None,
        'property_count_cached': cache.get(CACHE_KEYS['PROPERTY_COUNT']) is not None,
        'cache_keys': CACHE_KEYS,
        'cache_timeouts': CACHE_TIMEOUTS,
    }


def warm_cache():
    """
    Pre-populate cache with property data.
    
    Call this function to proactively load data into cache,
    useful for improving performance before peak usage times.
    """
    logger.info("Warming up property cache...")
    
    # This will fetch from database and cache the results
    properties = get_all_properties()
    count = get_property_count()
    
    logger.info(f"Cache warmed up with {len(properties)} properties")
    return {
        'properties_cached': len(properties),
        'count_cached': count
    }