from django.shortcuts import render
from django.views.decorators.cache import cache_page
from django.http import JsonResponse
from django.core.cache import cache
from django.conf import settings
from .models import Property
from .utils import get_all_properties, get_property_count, get_cache_info, invalidate_property_cache
import time

# Cache the view for 15 minutes (60 seconds * 15 = 900 seconds)
@cache_page(60 * 15)
def property_list(request):
    """
    View to display all properties with Redis caching.
    
    This view now uses low-level caching for the queryset (1 hour)
    AND page-level caching for the HTTP response (15 minutes).
    
    Benefits of this dual caching approach:
    - Queryset cache (1 hour): Reduces database queries
    - Page cache (15 minutes): Reduces view processing time
    """
    # Use our cached utility function instead of direct database query
    # This will either return cached data or fetch from DB and cache it
    properties = get_all_properties()
    
    # Get property count (also cached separately for efficiency)
    total_count = get_property_count()
    
    # Check if this is an API request (JSON response)
    if request.headers.get('Accept') == 'application/json':
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


def cache_status(request):
    """
    Debug view to check cache status - useful for development
    """
    cache_key = f"views.decorators.cache.cache_page.{request.get_full_path()}.{request.LANGUAGE_CODE}.{settings.TIME_ZONE}"
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


def delete_test_properties(request):
    """
    View to clean up test properties created by test_signal_invalidation.
    """
    if request.method == 'POST':
        # Delete test properties
        deleted_count = Property.objects.filter(title__startswith='Test Property').delete()[0]
        
        return JsonResponse({
            'success': True,
            'message': f'Deleted {deleted_count} test properties',
            'deleted_count': deleted_count,
            'note': 'If signals are working, cache should be cleared automatically',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return JsonResponse({
        'error': 'Only POST requests are allowed',
        'usage': 'Send a POST request to delete test properties'
    })


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