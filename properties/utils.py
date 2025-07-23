"""
Utility functions for property caching and data management.

This module contains functions that implement low-level caching
using Django's cache framework with Redis backend.
"""

from django.core.cache import cache
from django.db import models
from .models import Property
import logging
import django_redis

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


def get_redis_cache_metrics():
    """
    Retrieve and analyze Redis cache hit/miss metrics.
    
    This function connects to Redis via django_redis, retrieves keyspace
    statistics, calculates hit ratios, and returns comprehensive metrics
    for cache performance analysis.
    
    Returns:
        dict: Cache metrics including hits, misses, hit ratio, and additional stats
    """
    try:
        # Get the Redis connection from django_redis
        redis_client = django_redis.get_redis_connection("default")
        
        logger.info("Retrieving Redis cache metrics...")
        
        # Get Redis INFO statistics
        # The INFO command returns comprehensive Redis server statistics
        redis_info = redis_client.info()
        
        # Extract keyspace hit/miss statistics
        keyspace_hits = redis_info.get('keyspace_hits', 0)
        keyspace_misses = redis_info.get('keyspace_misses', 0)
        
        # Calculate total operations and hit ratio
        total_operations = keyspace_hits + keyspace_misses
        hit_ratio = (keyspace_hits / total_operations * 100) if total_operations > 0 else 0
        miss_ratio = (keyspace_misses / total_operations * 100) if total_operations > 0 else 0
        
        # Get additional useful Redis metrics
        used_memory = redis_info.get('used_memory', 0)
        used_memory_human = redis_info.get('used_memory_human', 'N/A')
        connected_clients = redis_info.get('connected_clients', 0)
        total_connections_received = redis_info.get('total_connections_received', 0)
        total_commands_processed = redis_info.get('total_commands_processed', 0)
        redis_version = redis_info.get('redis_version', 'Unknown')
        uptime_in_seconds = redis_info.get('uptime_in_seconds', 0)
        
        # Calculate uptime in a human-readable format
        uptime_days = uptime_in_seconds // 86400
        uptime_hours = (uptime_in_seconds % 86400) // 3600
        uptime_minutes = (uptime_in_seconds % 3600) // 60
        
        # Get database-specific keyspace info (db0, db1, etc.)
        keyspace_info = {}
        for key, value in redis_info.items():
            if key.startswith('db'):
                keyspace_info[key] = value
        
        # Compile comprehensive metrics
        metrics = {
            'cache_performance': {
                'keyspace_hits': keyspace_hits,
                'keyspace_misses': keyspace_misses,
                'total_operations': total_operations,
                'hit_ratio_percent': round(hit_ratio, 2),
                'miss_ratio_percent': round(miss_ratio, 2),
                'performance_rating': get_performance_rating(hit_ratio)
            },
            'memory_usage': {
                'used_memory_bytes': used_memory,
                'used_memory_human': used_memory_human,
            },
            'connection_stats': {
                'connected_clients': connected_clients,
                'total_connections_received': total_connections_received,
                'total_commands_processed': total_commands_processed,
            },
            'server_info': {
                'redis_version': redis_version,
                'uptime_seconds': uptime_in_seconds,
                'uptime_human': f"{uptime_days}d {uptime_hours}h {uptime_minutes}m",
            },
            'keyspace_info': keyspace_info,
            'analysis': {
                'cache_efficiency': analyze_cache_efficiency(hit_ratio),
                'recommendations': get_cache_recommendations(hit_ratio, total_operations)
            }
        }
        
        # Log the metrics for monitoring
        logger.info(f"Redis cache metrics retrieved successfully:")
        logger.info(f"  Hit ratio: {hit_ratio:.2f}%")
        logger.info(f"  Total operations: {total_operations}")
        logger.info(f"  Memory usage: {used_memory_human}")
        logger.info(f"  Connected clients: {connected_clients}")
        
        return {
            'success': True,
            'metrics': metrics,
            'timestamp': uptime_in_seconds  # Use Redis uptime as timestamp reference
        }
        
    except Exception as e:
        error_msg = f"Error retrieving Redis cache metrics: {str(e)}"
        logger.error(error_msg)
        
        return {
            'success': False,
            'error': error_msg,
            'metrics': None,
            'recommendations': [
                'Check if Redis server is running',
                'Verify Redis connection settings in Django settings',
                'Ensure django-redis is properly configured'
            ]
        }


def get_performance_rating(hit_ratio):
    """
    Get a performance rating based on hit ratio.
    
    Args:
        hit_ratio (float): Cache hit ratio percentage
        
    Returns:
        str: Performance rating
    """
    if hit_ratio >= 90:
        return "Excellent"
    elif hit_ratio >= 80:
        return "Very Good"
    elif hit_ratio >= 70:
        return "Good"
    elif hit_ratio >= 50:
        return "Fair"
    else:
        return "Poor"


def analyze_cache_efficiency(hit_ratio):
    """
    Analyze cache efficiency and provide insights.
    
    Args:
        hit_ratio (float): Cache hit ratio percentage
        
    Returns:
        str: Analysis of cache efficiency
    """
    if hit_ratio >= 90:
        return "Cache is performing excellently. Most requests are served from cache."
    elif hit_ratio >= 80:
        return "Cache is performing very well. Good balance of cached and fresh data."
    elif hit_ratio >= 70:
        return "Cache is performing adequately but could be optimized."
    elif hit_ratio >= 50:
        return "Cache performance is below optimal. Consider reviewing cache strategy."
    else:
        return "Cache performance is poor. Cache configuration needs immediate attention."


def get_cache_recommendations(hit_ratio, total_operations):
    """
    Get recommendations for cache optimization.
    
    Args:
        hit_ratio (float): Cache hit ratio percentage
        total_operations (int): Total cache operations
        
    Returns:
        list: List of recommendations
    """
    recommendations = []
    
    if hit_ratio < 50:
        recommendations.extend([
            "Consider increasing cache timeout values",
            "Review cache key patterns for efficiency",
            "Implement cache warming strategies",
            "Analyze which data should be cached vs. fetched fresh"
        ])
    elif hit_ratio < 70:
        recommendations.extend([
            "Fine-tune cache timeout values",
            "Consider implementing cache warming for frequently accessed data",
            "Review cache invalidation patterns"
        ])
    elif hit_ratio < 90:
        recommendations.extend([
            "Good performance, minor optimizations possible",
            "Monitor for patterns in cache misses",
            "Consider pre-loading critical data"
        ])
    else:
        recommendations.append("Excellent cache performance. Continue monitoring.")
    
    if total_operations < 100:
        recommendations.append("Low cache usage detected. Consider increasing cache utilization.")
    
    return recommendations