# Import necessary modules for cache handling
from django.shortcuts import render
from django.views.decorators.cache import cache_page, cache_control, never_cache
from django.views.decorators.vary import vary_on_headers
from django.http import JsonResponse
from django.core.cache import cache
from django.conf import settings
from .models import Property
from .utils import get_all_properties, get_property_count, get_cache_info, invalidate_property_cache, get_redis_cache_metrics
import time
from django.views.decorators.csrf import csrf_exempt


# Cache the view for 15 minutes (60 seconds * 15 = 900 seconds)
# Also vary on Accept header to cache HTML and JSON responses separately
@cache_page(60 * 15)
@vary_on_headers('Accept')
def property_list(request):
    """
    View to display all properties with Redis caching.
    
    This view now uses low-level caching for the queryset (1 hour)
    AND page-level caching for the HTTP response (15 minutes).
    
    Benefits of this dual caching approach:
    - Queryset cache (1 hour): Reduces database queries
    - Page cache (15 minutes): Reduces view processing time
    
    The @vary_on_headers('Accept') decorator ensures that HTML and JSON
    responses are cached separately.
    """
    try:
        # Use our cached utility function instead of direct database query
        # This will either return cached data or fetch from DB and cache it
        properties = get_all_properties()
        
        # Get property count (also cached separately for efficiency)
        total_count = get_property_count()
        
        # Check if this is an API request (JSON response)
        if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
            # Return JSON response for API calls
            properties_data = []
            for property_obj in properties:
                properties_data.append({
                    'id': property_obj.id,
                    'title': property_obj.title,
                    'description': property_obj.description,
                    'price': str(property_obj.price),  # Convert Decimal to string for JSON
                    'location': property_obj.location,
                    'created_at': property_obj.created_at.isoformat()
                })
            
            return JsonResponse({
                'properties': properties_data,
                'count': len(properties_data),
                'cached': True,  # Indicates this response might be cached
                'cache_info': {
                    'queryset_cache': '1 hour',
                    'page_cache': '15 minutes'
                }
            })
        
        # Return HTML response for browser requests
        context = {
            'properties': properties,
            'total_count': total_count,
            'cache_info': {
                'queryset_cached_for': '1 hour',
                'page_cached_for': '15 minutes',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        }
        return render(request, 'properties/property_list.html', context)
        
    except Exception as e:
        # Handle any caching or database errors gracefully
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in property_list view: {str(e)}")
        
        # Fallback to direct database query if caching fails
        properties = Property.objects.all().order_by('-created_at')
        
        if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
            properties_data = []
            for property_obj in properties:
                properties_data.append({
                    'id': property_obj.id,
                    'title': property_obj.title,
                    'description': property_obj.description,
                    'price': str(property_obj.price),
                    'location': property_obj.location,
                    'created_at': property_obj.created_at.isoformat()
                })
            
            return JsonResponse({
                'properties': properties_data,
                'count': len(properties_data),
                'cached': False,
                'error': 'Cache error, served from database',
                'cache_info': {
                    'queryset_cache': 'failed',
                    'page_cache': 'failed'
                }
            })
        
        context = {
            'properties': properties,
            'total_count': properties.count(),
            'cache_info': {
                'note': 'Cache error, served directly from database',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        }
        return render(request, 'properties/property_list.html', context)


def property_list_no_cache(request):
    """
    Version of property list that bypasses all caching - useful for comparing performance
    """
    # Direct database query without any caching
    properties = Property.objects.all().order_by('-created_at')
    
    if request.headers.get('Accept') == 'application/json':
        properties_data = []
        for property_obj in properties:
            properties_data.append({
                'id': property_obj.id,
                'title': property_obj.title,
                'description': property_obj.description,
                'price': str(property_obj.price),
                'location': property_obj.location,
                'created_at': property_obj.created_at.isoformat()
            })
        
        return JsonResponse({
            'properties': properties_data,
            'count': len(properties_data),
            'cached': False,
            'note': 'This response bypasses all caching'
        })
    
    context = {
        'properties': properties,
        'total_count': properties.count(),
        'cache_info': {
            'note': 'This page bypasses all caching',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    }
    return render(request, 'properties/property_list.html', context)

def cache_status(request):
    """
    Debug view to check cache status - useful for development
    """
    # Fix the language code access
    from django.utils import translation
    language_code = translation.get_language() or 'en'
    
    cache_key = f"views.decorators.cache.cache_page.{request.get_full_path()}.{language_code}.{settings.TIME_ZONE}"
    cached_data = cache.get(cache_key)
    
    # Get cache info from our utils
    cache_info = get_cache_info()
    
    return JsonResponse({
        'page_cache': {
            'backend': str(settings.CACHES['default']['BACKEND']),
            'location': settings.CACHES['default']['LOCATION'],
            'page_is_cached': cached_data is not None,
            'cache_key_example': cache_key[:50] + '...',  # Truncated for readability
        },
        'queryset_cache': cache_info,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    })


@csrf_exempt
def cache_clear(request):
    """
    View to manually clear property cache - useful for development/admin
    """
    if request.method == 'POST':
        result = invalidate_property_cache()
        return JsonResponse({
            'success': result['success'],
            'message': 'Property cache cleared successfully' if result['success'] else 'Errors occurred while clearing cache',
            'details': result,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return JsonResponse({
        'error': 'Only POST requests are allowed',
        'usage': 'Send a POST request to this endpoint to clear the property cache'
    })

@csrf_exempt
def test_signal_invalidation(request):
    """
    View to test signal-based cache invalidation.
    
    This view creates a test property to demonstrate automatic cache clearing.
    """
    if request.method == 'POST':
        from decimal import Decimal
        import random
        
        # Check if cache has data before creating property
        cache_before = get_cache_info()
        
        # Create a test property (this should trigger our signals)
        test_property = Property.objects.create(
            title=f"Test Property {random.randint(1000, 9999)}",
            description="This is a test property created to demonstrate signal-based cache invalidation.",
            price=Decimal('1500.00'),
            location="Test Location"
        )
        
        # Check cache status after creation
        cache_after = get_cache_info()
        
        return JsonResponse({
            'success': True,
            'message': 'Test property created successfully',
            'property': {
                'id': test_property.id,
                'title': test_property.title,
                'price': str(test_property.price)
            },
            'cache_before': cache_before,
            'cache_after': cache_after,
            'note': 'If signals are working, cache should be cleared automatically',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return JsonResponse({
        'error': 'Only POST requests are allowed',
        'usage': 'Send a POST request to create a test property and see signal-based cache invalidation in action'
    })


def cache_test(request):
    """
    Simple view to test cache functionality without complex serialization
    """
    from django.core.cache import cache
    import time
    
    # Test basic cache operations
    test_key = 'cache_test_key'
    test_value = f'Cache test at {time.strftime("%Y-%m-%d %H:%M:%S")}'
    
    # Set a value in cache
    cache.set(test_key, test_value, 60)  # Cache for 1 minute
    
    # Get the value back
    cached_value = cache.get(test_key)
    
    return JsonResponse({
        'cache_working': cached_value == test_value,
        'original_value': test_value,
        'cached_value': cached_value,
        'cache_backend': str(settings.CACHES['default']['BACKEND']),
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    })


def redis_metrics(request):
    """
    View to display Redis cache hit/miss metrics and performance analysis.
    """
    # Get comprehensive Redis metrics
    metrics_result = get_redis_cache_metrics()
    
    if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
        return JsonResponse(metrics_result)
    
    # For HTML requests, return formatted data
    context = {
        'metrics_result': metrics_result,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Create a simple HTML response if no template exists
    if metrics_result['success']:
        metrics = metrics_result['metrics']
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Redis Cache Metrics</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }}
                .metric-card {{ background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 6px; padding: 20px; margin: 15px 0; }}
                .metric-title {{ color: #2c3e50; font-size: 1.2em; font-weight: bold; margin-bottom: 10px; }}
                .metric-value {{ font-size: 1.4em; color: #27ae60; font-weight: bold; }}
                .performance-rating {{ padding: 8px 16px; border-radius: 4px; color: white; display: inline-block; }}
                .excellent {{ background: #27ae60; }}
                .very-good {{ background: #3498db; }}
                .good {{ background: #f39c12; }}
                .fair {{ background: #e67e22; }}
                .poor {{ background: #e74c3c; }}
                .recommendations {{ background: #ecf0f1; padding: 15px; border-radius: 4px; margin-top: 15px; }}
                .recommendations ul {{ margin: 10px 0; padding-left: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Redis Cache Performance Metrics</h1>
                <div class="metric-card">
                    <div class="metric-title">Cache Performance</div>
                    <div class="metric-value">{metrics['cache_performance']['hit_ratio_percent']}% Hit Ratio</div>
                    <div class="performance-rating {metrics['cache_performance']['performance_rating'].lower().replace(' ', '-')}">
                        {metrics['cache_performance']['performance_rating']}
                    </div>
                    <p><strong>Hits:</strong> {metrics['cache_performance']['keyspace_hits']:,}</p>
                    <p><strong>Misses:</strong> {metrics['cache_performance']['keyspace_misses']:,}</p>
                    <p><strong>Total Operations:</strong> {metrics['cache_performance']['total_operations']:,}</p>
                </div>
                
                <div class="metric-card">
                    <div class="metric-title">Memory Usage</div>
                    <p><strong>Used Memory:</strong> {metrics['memory_usage']['used_memory_human']}</p>
                </div>
                
                <div class="metric-card">
                    <div class="metric-title">Server Information</div>
                    <p><strong>Redis Version:</strong> {metrics['server_info']['redis_version']}</p>
                    <p><strong>Uptime:</strong> {metrics['server_info']['uptime_human']}</p>
                    <p><strong>Connected Clients:</strong> {metrics['connection_stats']['connected_clients']}</p>
                </div>
                
                <div class="metric-card">
                    <div class="metric-title">Cache Efficiency Analysis</div>
                    <p>{metrics['analysis']['cache_efficiency']}</p>
                    
                    <div class="recommendations">
                        <strong>Recommendations:</strong>
                        <ul>
        """
        
        for rec in metrics['analysis']['recommendations']:
            html_content += f"<li>{rec}</li>"
        
        html_content += """
                        </ul>
                    </div>
                </div>
                
                <div style="margin-top: 30px;">
                    <a href="/properties/" style="color: #3498db;">← Back to Properties</a> |
                    <a href="/properties/cache-status/" style="color: #3498db;">Cache Status</a> |
                    <a href="?format=json" style="color: #3498db;">View as JSON</a>
                </div>
            </div>
        </body>
        </html>
        """
        
        from django.http import HttpResponse
        return HttpResponse(html_content)
    else:
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Redis Metrics Error</title></head>
        <body style="font-family: Arial, sans-serif; margin: 40px;">
            <h1>Error Retrieving Redis Metrics</h1>
            <p style="color: #e74c3c;">{metrics_result['error']}</p>
            <h3>Recommendations:</h3>
            <ul>
        """
        
        for rec in metrics_result.get('recommendations', []):
            error_html += f"<li>{rec}</li>"
        
        error_html += """
            </ul>
            <a href="/properties/">← Back to Properties</a>
        </body>
        </html>
        """
        
        from django.http import HttpResponse
        return HttpResponse(error_html)

@csrf_exempt
def cache_load_test(request):
    """
    View to generate cache load for testing metrics.
    """
    if request.method == 'POST':
        import random
        
        # Generate some cache operations to test metrics
        operations = []
        
        for i in range(50):  # Generate 50 cache operations
            test_key = f"load_test_key_{random.randint(1, 20)}"  # Limited key range to ensure some hits
            test_value = f"test_value_{i}"
            
            # Set value
            cache.set(test_key, test_value, 300)  # 5 minutes
            operations.append(f"SET {test_key}")
            
            # Get value (should be a hit)
            cached_value = cache.get(test_key)
            if cached_value:
                operations.append(f"HIT {test_key}")
            else:
                operations.append(f"MISS {test_key}")
            
            # Random gets (some will miss)
            random_key = f"random_key_{random.randint(1, 100)}"
            random_value = cache.get(random_key)
            if random_value:
                operations.append(f"HIT {random_key}")
            else:
                operations.append(f"MISS {random_key}")
        
        return JsonResponse({
            'success': True,
            'message': f'Generated {len(operations)} cache operations for testing',
            'operations_count': len(operations),
            'note': 'Check /properties/redis-metrics/ to see updated statistics',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return JsonResponse({
        'error': 'Only POST requests are allowed',
        'usage': 'Send a POST request to generate cache load for testing metrics'
    })