from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
app_name = 'properties'

# DRF Router for Viewsets
router = DefaultRouter()
router.register(r'api', views.PropertyViewSet, basename='property-api')

urlpatterns = [
    
    #DRF viewsets
    path('api/', include(router.urls))

]