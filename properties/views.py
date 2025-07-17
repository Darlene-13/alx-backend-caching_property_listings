from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from .models import Property


@cache_page(60 * 15)  # Cache for 15 minutes
def property_list(request):
    """
    View to return all properties with Redis caching for 15 minutes.
    """
    try:
        # Get all properties from the database
        properties = Property.objects.all().values(
            'id', 'title', 'description', 'price', 'location', 
            'bedrooms', 'bathrooms', 'area', 'created_at', 'updated_at'
        )
        
        # Convert QuerySet to list for JSON serialization
        properties_list = list(properties)
        
        return JsonResponse({
            'status': 'success',
            'count': len(properties_list),
            'properties': properties_list
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)