"""
Django management command for cache operations.

Usage:
python manage.py manage_cache --status
python manage.py manage_cache --clear
python manage.py manage_cache --warm
"""

from django.core.management.base import BaseCommand
from properties.utils import get_cache_info, invalidate_property_cache, warm_cache, get_redis_cache_metrics


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
        parser.add_argument(
            '--test-signals',
            action='store_true',
            help='Test signal-based cache invalidation',
        )
        parser.add_argument(
            '--metrics',
            action='store_true',
            help='Show Redis cache hit/miss metrics and performance analysis',
        )

    def handle(self, *args, **options):
        if options['status']:
            self.show_status()
        elif options['clear']:
            self.clear_cache()
        elif options['warm']:
            self.warm_cache()
        elif options['test_signals']:
            self.test_signals()
        elif options['metrics']:
            self.show_metrics()
        else:
            self.stdout.write(
                self.style.WARNING(
                    'Please specify an action: --status, --clear, --warm, --test-signals, or --metrics'
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
        result = invalidate_property_cache()
        
        if result['success']:
            self.stdout.write(
                self.style.SUCCESS('Successfully cleared property cache')
            )
            for cache_info in result['cleared_caches']:
                self.stdout.write(f"  Cleared: {cache_info['name']}")
        else:
            self.stdout.write(
                self.style.ERROR('Error clearing property cache')
            )
            for error in result['errors']:
                self.stdout.write(f"  Error: {error}")

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

    def test_signals(self):
        """Test signal-based cache invalidation"""
        from properties.models import Property
        from decimal import Decimal
        import random
        
        self.stdout.write('Testing signal-based cache invalidation...')
        
        # First, warm the cache
        self.stdout.write('1. Warming cache...')
        warm_cache()
        
        # Check cache status
        cache_info_before = get_cache_info()
        self.stdout.write(f'2. Cache status before: {cache_info_before}')
        
        # Create a test property (should trigger signal)
        self.stdout.write('3. Creating test property (should trigger signal)...')
        test_property = Property.objects.create(
            title=f"Signal Test Property {random.randint(1000, 9999)}",
            description="Created to test signal-based cache invalidation",
            price=Decimal('999.99'),
            location="Signal Test Location"
        )
        
        # Check cache status after creation
        cache_info_after = get_cache_info()
        self.stdout.write(f'4. Cache status after creation: {cache_info_after}')
        
        # Delete the test property (should also trigger signal)
        self.stdout.write('5. Deleting test property (should trigger signal)...')
        test_property.delete()
        
        # Final cache status
        cache_info_final = get_cache_info()
        self.stdout.write(f'6. Final cache status: {cache_info_final}')
        
        self.stdout.write(
            self.style.SUCCESS(
                'Signal test completed! Check the cache status changes above.'
            )
        )

    def show_metrics(self):
        """Display Redis cache hit/miss metrics and performance analysis"""
        self.stdout.write(self.style.SUCCESS('Redis Cache Metrics:'))
        self.stdout.write('=' * 50)
        
        metrics_result = get_redis_cache_metrics()
        
        if metrics_result['success']:
            metrics = metrics_result['metrics']
            
            # Cache Performance
            perf = metrics['cache_performance']
            self.stdout.write(f"\n{self.style.SUCCESS('Cache Performance:')}")
            self.stdout.write(f"  Hit Ratio: {perf['hit_ratio_percent']}%")
            self.stdout.write(f"  Performance Rating: {perf['performance_rating']}")
            self.stdout.write(f"  Keyspace Hits: {perf['keyspace_hits']:,}")
            self.stdout.write(f"  Keyspace Misses: {perf['keyspace_misses']:,}")
            self.stdout.write(f"  Total Operations: {perf['total_operations']:,}")
            
            # Memory Usage
            memory = metrics['memory_usage']
            self.stdout.write(f"\n{self.style.SUCCESS('Memory Usage:')}")
            self.stdout.write(f"  Used Memory: {memory['used_memory_human']}")
            
            # Server Info
            server = metrics['server_info']
            self.stdout.write(f"\n{self.style.SUCCESS('Server Information:')}")
            self.stdout.write(f"  Redis Version: {server['redis_version']}")
            self.stdout.write(f"  Uptime: {server['uptime_human']}")
            
            # Connection Stats
            conn = metrics['connection_stats']
            self.stdout.write(f"\n{self.style.SUCCESS('Connection Statistics:')}")
            self.stdout.write(f"  Connected Clients: {conn['connected_clients']}")
            self.stdout.write(f"  Total Connections: {conn['total_connections_received']:,}")
            self.stdout.write(f"  Total Commands: {conn['total_commands_processed']:,}")
            
            # Analysis
            analysis = metrics['analysis']
            self.stdout.write(f"\n{self.style.SUCCESS('Analysis:')}")
            self.stdout.write(f"  {analysis['cache_efficiency']}")
            
            # Recommendations
            self.stdout.write(f"\n{self.style.SUCCESS('Recommendations:')}")
            for i, rec in enumerate(analysis['recommendations'], 1):
                self.stdout.write(f"  {i}. {rec}")
                
        else:
            self.stdout.write(
                self.style.ERROR(f"Error retrieving metrics: {metrics_result['error']}")
            )
            if 'recommendations' in metrics_result:
                self.stdout.write(f"\n{self.style.WARNING('Troubleshooting:')}")
                for rec in metrics_result['recommendations']:
                    self.stdout.write(f"  - {rec}")