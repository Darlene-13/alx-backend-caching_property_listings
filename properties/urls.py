from django.urls import path
from . import views

# App namespace for URL reversing
app_name = 'properties'

urlpatterns = [
    # Property list view - cached for 15 minutes (page) + 1 hour (queryset)
    path('', views.property_list, name='property_list'),
    
    # Property list without any caching - for performance comparison
    path('no-cache/', views.property_list_no_cache, name='property_list_no_cache'),
    
    # Cache management and debugging endpoints
    path('cache-status/', views.cache_status, name='cache_status'),
    path('cache-clear/', views.cache_clear, name='cache_clear'),
    path('cache-test/', views.cache_test, name='cache_test'),
    
    # Redis metrics and analysis
    path('redis-metrics/', views.redis_metrics, name='redis_metrics'),
    path('cache-load-test/', views.cache_load_test, name='cache_load_test'),
    
    # Signal testing endpoints
    path('test-signals/', views.test_signal_invalidation, name='test_signals'),
    
    # You can add more property-related URLs here in the future, such as:
    # path('<int:property_id>/', views.property_detail, name='property_detail'),
    # path('search/', views.property_search, name='property_search'),
    # path('create/', views.property_create, name='property_create'),
]