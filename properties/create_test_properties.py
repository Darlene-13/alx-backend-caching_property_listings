"""
Script to create test properties for demonstration.
Run this with: python manage.py shell < create_test_properties.py
"""

from properties.models import Property
from decimal import Decimal

# Sample property data
test_properties = [
    {
        'title': 'Modern Downtown Apartment',
        'description': 'Beautiful 2-bedroom apartment in the heart of downtown with city views.',
        'price': Decimal('1250.00'),
        'location': 'Downtown'
    },
    {
        'title': 'Cozy Suburban House',
        'description': 'Family-friendly 3-bedroom house with a large backyard and garage.',
        'price': Decimal('1800.00'),
        'location': 'Suburbia'
    },
    {
        'title': 'Luxury Waterfront Condo',
        'description': 'Stunning waterfront condominium with premium amenities and ocean views.',
        'price': Decimal('3200.00'),
        'location': 'Waterfront District'
    },
    {
        'title': 'Student-Friendly Studio',
        'description': 'Affordable studio apartment perfect for students, close to university.',
        'price': Decimal('850.00'),
        'location': 'University Area'
    },
    {
        'title': 'Executive Penthouse',
        'description': 'Exclusive penthouse with 360-degree city views and private terrace.',
        'price': Decimal('5500.00'),
        'location': 'Financial District'
    }
]

# Create properties if they don't exist
for prop_data in test_properties:
    property_obj, created = Property.objects.get_or_create(
        title=prop_data['title'],
        defaults=prop_data
    )
    if created:
        print(f"Created property: {property_obj.title}")
    else:
        print(f"Property already exists: {property_obj.title}")

print(f"\nTotal properties in database: {Property.objects.count()}")
print("Test data creation complete!")