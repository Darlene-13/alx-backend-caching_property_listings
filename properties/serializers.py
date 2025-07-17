from rest_framework import serializers
from decimal import Decimal
from .models import Property


class PropertySerializer(serializers.ModelSerializer):
    """
    Full serializer for Property model with validation.
    Used for create, update, and detailed retrieve operations.
    """
    
    # Add computed fields
    price_formatted = serializers.SerializerMethodField()
    age_days = serializers.SerializerMethodField()
    
    class Meta:
        model = Property
        fields = [
            'id', 
            'title', 
            'description', 
            'price', 
            'price_formatted',
            'location', 
            'created_at',
            'age_days'
        ]
        read_only_fields = ['id', 'created_at', 'price_formatted', 'age_days']
    
    def get_price_formatted(self, obj):
        """Format price with currency symbol"""
        return f"${obj.price:,.2f}"
    
    def get_age_days(self, obj):
        """Calculate how many days since property was created"""
        from django.utils import timezone
        return (timezone.now() - obj.created_at).days
    
    def validate_price(self, value):
        """Validate that price is positive and reasonable"""
        if value <= 0:
            raise serializers.ValidationError("Price must be positive")
        
        if value > Decimal('10000000'):  # 10 million limit
            raise serializers.ValidationError("Price cannot exceed $10,000,000")
        
        return value
    
    def validate_title(self, value):
        """Validate title requirements"""
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long")
        
        if len(value.strip()) > 255:
            raise serializers.ValidationError("Title cannot exceed 255 characters")
        
        return value.strip()
    
    def validate_location(self, value):
        """Validate location requirements"""
        if not value or not value.strip():
            raise serializers.ValidationError("Location cannot be empty")
        
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Location must be at least 2 characters long")
        
        return value.strip()
    
    def validate_description(self, value):
        """Validate description requirements"""
        if not value or not value.strip():
            raise serializers.ValidationError("Description cannot be empty")
        
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Description must be at least 10 characters long")
        
        return value.strip()
    
    def validate(self, data):
        """Cross-field validation"""
        # Check if title and location are not identical
        if data.get('title') and data.get('location'):
            if data['title'].lower() == data['location'].lower():
                raise serializers.ValidationError(
                    "Title and location cannot be identical"
                )
        
        return data
    
    def create(self, validated_data):
        """Custom create method"""
        return Property.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        """Custom update method"""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class PropertyListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for property listings.
    Used for list views where you need less detail for better performance.
    """
    
    price_formatted = serializers.SerializerMethodField()
    short_description = serializers.SerializerMethodField()
    
    class Meta:
        model = Property
        fields = [
            'id', 
            'title', 
            'price', 
            'price_formatted',
            'location', 
            'short_description',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'price_formatted', 'short_description']
    
    def get_price_formatted(self, obj):
        """Format price with currency symbol"""
        return f"${obj.price:,.2f}"
    
    def get_short_description(self, obj):
        """Return truncated description for list view"""
        if len(obj.description) > 100:
            return obj.description[:100] + "..."
        return obj.description


class PropertyCreateSerializer(serializers.ModelSerializer):
    """
    Serializer specifically for creating properties.
    Can have different validation rules for creation vs updates.
    """
    
    class Meta:
        model = Property
        fields = ['title', 'description', 'price', 'location']
    
    def validate_title(self, value):
        """Check for duplicate titles during creation"""
        if Property.objects.filter(title__iexact=value.strip()).exists():
            raise serializers.ValidationError(
                "A property with this title already exists"
            )
        return value.strip()
    
    def validate(self, data):
        """Additional validation for creation"""
        # You can add custom business logic here
        return data


class PropertyUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer specifically for updating properties.
    Allows partial updates and different validation rules.
    """
    
    class Meta:
        model = Property
        fields = ['title', 'description', 'price', 'location']
    
    def validate_title(self, value):
        """Check for duplicate titles during update (exclude current instance)"""
        if value and value.strip():
            existing = Property.objects.filter(title__iexact=value.strip())
            if self.instance:
                existing = existing.exclude(id=self.instance.id)
            
            if existing.exists():
                raise serializers.ValidationError(
                    "A property with this title already exists"
                )
        
        return value.strip() if value else value


class PropertyStatsSerializer(serializers.Serializer):
    """
    Serializer for property statistics.
    Not tied to a model, used for custom data structures.
    """
    
    total_properties = serializers.IntegerField()
    average_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    highest_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    lowest_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    recent_properties_count = serializers.IntegerField()
    
    def to_representation(self, instance):
        """Custom representation for stats"""
        data = super().to_representation(instance)
        
        # Format prices
        for price_field in ['average_price', 'highest_price', 'lowest_price']:
            if data[price_field]:
                data[f"{price_field}_formatted"] = f"${data[price_field]:,.2f}"
        
        return data