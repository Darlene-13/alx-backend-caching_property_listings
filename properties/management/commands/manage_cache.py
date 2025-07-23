"""
Django management command for cache operations.

Usage:
python manage.py manage_cache --status
python manage.py manage_cache --clear
python manage.py manage_cache --warm
"""

from django.core.management.base import BaseCommand
from properties.utils import get_cache_info, invalidate_property_cache, warm_cache


class Command(BaseCommand):
    help = 'Manage property cache operations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--status',
            action='store_true',
            help='Show cache status information',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all property cache entries',
        )
        parser.add_argument(
            '--warm',
            action='store_true',
            help='Pre-populate cache with property data',
        )

    def handle(self, *args, **options):
        if options['status']:
            self.show_status()
        elif options['clear']:
            self.clear_cache()
        elif options['warm']:
            self.warm_cache()
        else:
            self.stdout.write(
                self.style.WARNING(
                    'Please specify an action: --status, --clear, or --warm'
                )
            )

    def show_status(self):
        """Display cache status information"""
        self.stdout.write(self.style.SUCCESS('Cache Status:'))
        
        cache_info = get_cache_info()
        
        for key, value in cache_info.items():
            if isinstance(value, dict):
                self.stdout.write(f"\n{key}:")
                for sub_key, sub_value in value.items():
                    self.stdout.write(f"  {sub_key}: {sub_value}")
            else:
                self.stdout.write(f"{key}: {value}")

    def clear_cache(self):
        """Clear all property cache entries"""
        success = invalidate_property_cache()
        
        if success:
            self.stdout.write(
                self.style.SUCCESS('Successfully cleared property cache')
            )
        else:
            self.stdout.write(
                self.style.ERROR('Error clearing property cache')
            )

    def warm_cache(self):
        """Pre-populate cache with property data"""
        self.stdout.write('Warming up cache...')
        
        result = warm_cache()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Cache warmed up successfully:\n'
                f'  Properties cached: {result["properties_cached"]}\n'
                f'  Count cached: {result["count_cached"]}'
            )
        )