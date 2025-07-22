from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db.models import Q
import logging

from .models import Property
from .utils import (
    get_all_properties,
    get_property_by_id,
    get_properties_by_location,
    invalidate_properties_cache,
    cache_statistics
)

logger = logging.getLogger(__name__)

@cache_page(60*15)
def property_list(request):
    """
    Display a list of all properties using cached data.
    
    This view uses the get_all_properties() function which implements
    low-level caching with Redis for 1 hour.
    """
    try:
        # Use the cached function to get all properties
        properties = get_all_properties()
        
        # Handle search functionality
        search_query = request.GET.get('search', '')
        location_filter = request.GET.get('location', '')
        
        if search_query:
            # Filter the cached results
            properties = [
                prop for prop in properties 
                if search_query.lower() in prop.title.lower() or 
                   search_query.lower() in prop.description.lower()
            ]
        
        if location_filter:
            # Use location-specific caching for better performance
            properties = get_properties_by_location(location_filter)
        
        # Implement pagination
        paginator = Paginator(properties, 12)  # Show 12 properties per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'properties': page_obj,
            'search_query': search_query,
            'location_filter': location_filter,
            'total_count': len(properties),
        }
        
        logger.info(f"Property list rendered with {len(properties)} properties")
        return render(request, 'properties/property_list.html', context)
        
    except Exception as e:
        logger.error(f"Error in property_list view: {e}")
        messages.error(request, "An error occurred while loading properties.")
        return render(request, 'properties/property_list.html', {'properties': []})


def property_detail(request, property_id):
    """
    Display details of a specific property using cached data.
    """
    try:
        # Use the cached function to get property by ID
        property_obj = get_property_by_id(property_id)
        
        if property_obj is None:
            logger.warning(f"Property {property_id} not found")
            messages.error(request, "Property not found.")
            return render(request, 'properties/property_not_found.html')
        
        context = {
            'property': property_obj,
        }
        
        logger.info(f"Property detail rendered for property {property_id}")
        return render(request, 'properties/property_detail.html', context)
        
    except Exception as e:
        logger.error(f"Error in property_detail view: {e}")
        messages.error(request, "An error occurred while loading the property.")
        return render(request, 'properties/property_detail.html')


@require_http_methods(["GET"])
def properties_api(request):
    """
    API endpoint to get all properties as JSON using cached data.
    """
    try:
        properties = get_all_properties()
        
        # Convert to JSON-serializable format
        properties_data = []
        for prop in properties:
            properties_data.append({
                'id': prop.id,
                'title': prop.title,
                'description': prop.description,
                'price': float(prop.price),
                'location': prop.location,
                'created_at': prop.created_at.isoformat(),
            })
        
        return JsonResponse({
            'status': 'success',
            'count': len(properties_data),
            'data': properties_data,
            'cached': True
        })
        
    except Exception as e:
        logger.error(f"Error in properties_api view: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to retrieve properties'
        }, status=500)


@require_http_methods(["GET"])
def property_api_detail(request, property_id):
    """
    API endpoint to get a specific property as JSON using cached data.
    """
    try:
        property_obj = get_property_by_id(property_id)
        
        if property_obj is None:
            return JsonResponse({
                'status': 'error',
                'message': 'Property not found'
            }, status=404)
        
        property_data = {
            'id': property_obj.id,
            'title': property_obj.title,
            'description': property_obj.description,
            'price': float(property_obj.price),
            'location': property_obj.location,
            'created_at': property_obj.created_at.isoformat(),
        }
        
        return JsonResponse({
            'status': 'success',
            'data': property_data,
            'cached': True
        })
        
    except Exception as e:
        logger.error(f"Error in property_api_detail view: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to retrieve property'
        }, status=500)


@require_http_methods(["POST"])
def invalidate_cache(request):
    """
    Admin endpoint to manually invalidate the properties cache.
    """
    try:
        invalidate_properties_cache()
        
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({
                'status': 'success',
                'message': 'Cache invalidated successfully'
            })
        else:
            messages.success(request, "Cache invalidated successfully!")
            return render(request, 'properties/cache_status.html')
            
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({
                'status': 'error',
                'message': 'Failed to invalidate cache'
            }, status=500)
        else:
            messages.error(request, "Failed to invalidate cache.")
            return render(request, 'properties/cache_status.html')


@require_http_methods(["GET"])
def cache_status(request):
    """
    Display cache status and statistics.
    """
    try:
        stats = cache_statistics()
        
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({
                'status': 'success',
                'data': stats
            })
        else:
            context = {
                'cache_stats': stats,
            }
            return render(request, 'properties/cache_status.html', context)
            
    except Exception as e:
        logger.error(f"Error getting cache status: {e}")
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({
                'status': 'error',
                'message': 'Failed to get cache status'
            }, status=500)
        else:
            messages.error(request, "Failed to get cache status.")
            return render(request, 'properties/cache_status.html')


def properties_by_location(request, location):
    """
    Display properties filtered by location using cached data.
    """
    try:
        properties = get_properties_by_location(location)
        
        # Implement pagination
        paginator = Paginator(properties, 12)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'properties': page_obj,
            'location': location,
            'total_count': len(properties),
        }
        
        logger.info(f"Properties by location '{location}' rendered with {len(properties)} properties")
        return render(request, 'properties/properties_by_location.html', context)
        
    except Exception as e:
        logger.error(f"Error in properties_by_location view: {e}")
        messages.error(request, f"An error occurred while loading properties for {location}.")
        return render(request, 'properties/properties_by_location.html', {'properties': []})