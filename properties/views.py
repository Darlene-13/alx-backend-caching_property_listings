from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import Property
from .serializers import PropertySerializer, PropertyListSerializer


class PropertyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing properties with full CRUD operations and caching.
    
    Endpoints:
    - GET /api/v1/properties/ - List all properties (cached for 15 minutes)
    - POST /api/v1/properties/ - Create a new property
    - GET /api/v1/properties/{id}/ - Retrieve a specific property
    - PUT /api/v1/properties/{id}/ - Update a property
    - PATCH /api/v1/properties/{id}/ - Partial update of a property
    - DELETE /api/v1/properties/{id}/ - Delete a property
    """
    
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """Return properties ordered by creation date (newest first)"""
        return Property.objects.all().order_by('-created_at')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return PropertyListSerializer
        return PropertySerializer
    
    @method_decorator(cache_page(60 * 15))  # Cache for 15 minutes
    def list(self, request, *args, **kwargs):
        """
        List all properties with Redis caching for 15 minutes.
        """
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            
            return Response({
                'status': 'success',
                'count': len(serializer.data),
                'results': serializer.data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def retrieve(self, request, pk=None, *args, **kwargs):
        """Retrieve a single property by ID"""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            
            return Response({
                'status': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        except Property.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Property not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def create(self, request, *args, **kwargs):
        """Create a new property"""
        try:
            serializer = self.get_serializer(data=request.data)
            
            if serializer.is_valid():
                instance = serializer.save()
                
                # Clear cache after creating new property
                cache.clear()
                
                return Response({
                    'status': 'success',
                    'message': 'Property created successfully',
                    'data': PropertySerializer(instance).data
                }, status=status.HTTP_201_CREATED)
            
            else:
                return Response({
                    'status': 'error',
                    'message': 'Validation failed',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def update(self, request, pk=None, *args, **kwargs):
        """Update an existing property (PUT)"""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data)
            
            if serializer.is_valid():
                updated_instance = serializer.save()
                
                # Clear cache after updating property
                cache.clear()
                
                return Response({
                    'status': 'success',
                    'message': 'Property updated successfully',
                    'data': PropertySerializer(updated_instance).data
                }, status=status.HTTP_200_OK)
            
            else:
                return Response({
                    'status': 'error',
                    'message': 'Validation failed',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except Property.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Property not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def partial_update(self, request, pk=None, *args, **kwargs):
        """Partially update an existing property (PATCH)"""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            
            if serializer.is_valid():
                updated_instance = serializer.save()
                
                # Clear cache after updating property
                cache.clear()
                
                return Response({
                    'status': 'success',
                    'message': 'Property updated successfully',
                    'data': PropertySerializer(updated_instance).data
                }, status=status.HTTP_200_OK)
            
            else:
                return Response({
                    'status': 'error',
                    'message': 'Validation failed',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except Property.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Property not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def destroy(self, request, pk=None, *args, **kwargs):
        """Delete a property"""
        try:
            instance = self.get_object()
            property_title = instance.title
            instance.delete()
            
            # Clear cache after deleting property
            cache.clear()
            
            return Response({
                'status': 'success',
                'message': f'Property "{property_title}" deleted successfully'
            }, status=status.HTTP_200_OK)
        
        except Property.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Property not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    @method_decorator(cache_page(60 * 15))
    def recent(self, request):
        """
        Custom action: Get recently added properties
        Endpoint: GET /api/v1/properties/recent/
        """
        try:
            recent_properties = self.get_queryset()[:5]  # Get last 5 properties
            serializer = PropertyListSerializer(recent_properties, many=True)
            
            return Response({
                'status': 'success',
                'message': 'Recent properties retrieved successfully',
                'count': len(serializer.data),
                'results': serializer.data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Custom action: Get property statistics
        Endpoint: GET /api/v1/properties/stats/
        """
        try:
            queryset = self.get_queryset()
            total_properties = queryset.count()
            
            if total_properties > 0:
                avg_price = queryset.aggregate(
                    avg_price=models.Avg('price')
                )['avg_price']
                max_price = queryset.aggregate(
                    max_price=models.Max('price')
                )['max_price']
                min_price = queryset.aggregate(
                    min_price=models.Min('price')
                )['min_price']
            else:
                avg_price = max_price = min_price = 0
            
            return Response({
                'status': 'success',
                'data': {
                    'total_properties': total_properties,
                    'average_price': float(avg_price) if avg_price else 0,
                    'highest_price': float(max_price) if max_price else 0,
                    'lowest_price': float(min_price) if min_price else 0
                }
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PropertyReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ReadOnly ViewSet for properties - only list and retrieve operations.
    Useful for public API endpoints where you don't want modification.
    """
    
    queryset = Property.objects.all()
    serializer_class = PropertyListSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """Return properties ordered by creation date (newest first)"""
        return Property.objects.all().order_by('-created_at')
    
    @method_decorator(cache_page(60 * 15))  # Cache for 15 minutes
    def list(self, request, *args, **kwargs):
        """List all properties with caching"""
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            
            return Response({
                'status': 'success',
                'count': len(serializer.data),
                'results': serializer.data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def retrieve(self, request, pk=None, *args, **kwargs):
        """Retrieve a single property"""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            
            return Response({
                'status': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        except Property.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Property not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

