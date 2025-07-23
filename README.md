# Django Property Caching System

A comprehensive Django application demonstrating advanced Redis caching strategies with property listings. This project implements multi-level caching, signal-based cache invalidation, and Redis performance monitoring.

## 🚀 Features

- **Multi-level Caching**: Page-level (15 minutes) + Queryset-level (1 hour) caching
- **Signal-based Cache Invalidation**: Automatic cache clearing when data changes
- **Redis Performance Monitoring**: Hit/miss ratios, memory usage, and performance analysis
- **Comprehensive API**: REST endpoints for cache management and testing
- **Docker Integration**: Containerized PostgreSQL and Redis services
- **Cache Management Tools**: Django management commands and web interface

## 📋 Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Cache Strategy](#cache-strategy)
- [Testing](#testing)
- [Performance Monitoring](#performance-monitoring)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Django App    │    │      Redis      │    │   PostgreSQL    │
│                 │    │                 │    │                 │
│ • Views         │◄──►│ • Page Cache    │    │ • Property Data │
│ • Models        │    │ • Queryset Cache│    │ • User Data     │
│ • Signals       │    │ • Session Data  │    │ • Migrations    │
│ • Utils         │    │ • Metrics       │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Cache Layers

1. **Page Cache** (15 minutes): Caches entire HTTP responses
2. **Queryset Cache** (1 hour): Caches database query results
3. **Signal Invalidation**: Automatic cache clearing on data changes

## 🔧 Prerequisites

- Python 3.8+
- Django 4.2+
- Docker & Docker Compose
- Git

## 📥 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd alx-backend-caching_property_listings
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Start Docker Services

```bash
docker-compose up -d
```

### 5. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Sample Data

```bash
python manage.py shell < create_test_properties.py
```

### 7. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 8. Start Development Server

```bash
python manage.py runserver 8001
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://postgres:postgres123@localhost:5432/property_listings
REDIS_URL=redis://localhost:6379/1
```

### Docker Services

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:latest
    environment:
      POSTGRES_DB: property_listings
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres123
    ports:
      - "5432:5432"

  redis:
    image: redis:latest
    ports:
      - "6379:6379"
```

### Django Settings

Key configurations in `settings.py`:

```python
# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://localhost:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SERIALIZER': 'django_redis.serializers.pickle.PickleSerializer',
        }
    }
}

# Database Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'property_listings',
        'USER': 'postgres',
        'PASSWORD': 'postgres123',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## 🎯 Usage

### Basic Operations

```bash
# Check cache status
python manage.py manage_cache --status

# Clear all caches
python manage.py manage_cache --clear

# Warm up cache
python manage.py manage_cache --warm

# Test signal invalidation
python manage.py manage_cache --test-signals

# View Redis metrics
python manage.py manage_cache --metrics
```

### Web Interface

- **Property List**: http://localhost:8001/properties/
- **Admin Panel**: http://localhost:8001/admin/
- **Redis Metrics**: http://localhost:8001/properties/redis-metrics/

## 🔌 API Endpoints

### Property Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/properties/` | List all properties (cached) |
| GET | `/properties/?format=json` | List properties as JSON |
| GET | `/properties/no-cache/` | List properties (bypass cache) |

### Cache Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/properties/cache-status/` | Show cache status |
| POST | `/properties/cache-clear/` | Clear all caches |
| GET | `/properties/cache-test/` | Test cache functionality |

### Redis Metrics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/properties/redis-metrics/` | Redis performance dashboard |
| GET | `/properties/redis-metrics/?format=json` | Redis metrics as JSON |
| POST | `/properties/cache-load-test/` | Generate cache load for testing |

### Signal Testing

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/properties/test-signals/` | Test automatic cache invalidation |

## 📊 Cache Strategy

### Cache Keys

```python
CACHE_KEYS = {
    'ALL_PROPERTIES': 'all_properties',
    'PROPERTY_COUNT': 'property_count',
}
```

### Cache Timeouts

```python
CACHE_TIMEOUTS = {
    'PROPERTIES': 3600,  # 1 hour
    'COUNT': 1800,       # 30 minutes
}
```

### Cache Flow

1. **Request arrives** → Check page cache (15 min)
2. **Page cache miss** → Execute view logic
3. **Check queryset cache** (1 hour) in `get_all_properties()`
4. **Queryset cache miss** → Query database
5. **Store in both caches** → Return response

### Signal-Based Invalidation

```python
@receiver(post_save, sender=Property)
def invalidate_cache_on_property_save(sender, instance, created, **kwargs):
    cache.delete(CACHE_KEYS['ALL_PROPERTIES'])
    cache.delete(CACHE_KEYS['PROPERTY_COUNT'])

@receiver(post_delete, sender=Property)
def invalidate_cache_on_property_delete(sender, instance, **kwargs):
    cache.delete(CACHE_KEYS['ALL_PROPERTIES'])
    cache.delete(CACHE_KEYS['PROPERTY_COUNT'])
```

## 🧪 Testing

### Manual Testing

```bash
# Test basic cache functionality
curl http://localhost:8001/properties/cache-test/

# Test property list
curl http://localhost:8001/properties/

# Test JSON API
curl -H "Accept: application/json" http://localhost:8001/properties/

# Test cache clearing
curl -X POST http://localhost:8001/properties/cache-clear/

# Test signal invalidation
curl -X POST http://localhost:8001/properties/test-signals/
```

### Postman Testing

Import the provided Postman collection:

1. Copy the collection JSON from the project
2. Import into Postman
3. Set environment variable: `BASE_URL = http://127.0.0.1:8001`
4. Run the test sequence

### Performance Testing

```bash
# Generate cache load
curl -X POST http://localhost:8001/properties/cache-load-test/

# Check performance metrics
curl http://localhost:8001/properties/redis-metrics/?format=json
```

## 📈 Performance Monitoring

### Redis Metrics

The system provides comprehensive Redis monitoring:

- **Hit Ratio**: Percentage of requests served from cache
- **Memory Usage**: Current Redis memory consumption
- **Connection Stats**: Client connections and command processing
- **Performance Rating**: Automatic performance assessment
- **Recommendations**: Optimization suggestions

### Example Metrics Response

```json
{
  "success": true,
  "metrics": {
    "cache_performance": {
      "keyspace_hits": 150,
      "keyspace_misses": 50,
      "hit_ratio_percent": 75.0,
      "performance_rating": "Good"
    },
    "memory_usage": {
      "used_memory_human": "1.2M"
    },
    "analysis": {
      "cache_efficiency": "Cache is performing adequately but could be optimized.",
      "recommendations": [
        "Fine-tune cache timeout values",
        "Consider implementing cache warming"
      ]
    }
  }
}
```

### Performance Benchmarks

| Cache Type | Response Time | Hit Ratio Target |
|------------|---------------|------------------|
| Page Cache | ~10ms | >90% |
| Queryset Cache | ~20ms | >80% |
| Database Query | ~100ms | N/A |

## 🔍 Troubleshooting

### Common Issues

#### 1. Connection Refused Error

```bash
# Check if Docker services are running
docker-compose ps

# Restart services if needed
docker-compose restart
```

#### 2. CSRF Token Errors

Add `@csrf_exempt` decorator to API views:

```python
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def your_api_view(request):
    # Your view logic
```

#### 3. Cache Not Working

```bash
# Test Redis connection
docker-compose exec redis redis-cli ping

# Check Django cache settings
python manage.py shell -c "
from django.core.cache import cache
cache.set('test', 'hello', 30)
print(cache.get('test'))
"
```

#### 4. Migration Issues

```bash
# Reset migrations if needed
python manage.py migrate properties zero
python manage.py makemigrations properties
python manage.py migrate
```

### Debug Mode

Enable detailed logging in `settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'properties.utils': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'properties.signals': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}
```

## 📁 Project Structure

```
alx-backend-caching_property_listings/
├── alx-backend-caching_property_listings/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── properties/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── utils.py
│   ├── signals.py
│   ├── templates/
│   │   └── properties/
│   │       └── property_list.html
│   ├── management/
│   │   └── commands/
│   │       └── manage_cache.py
│   └── migrations/
├── docker-compose.yml
├── requirements.txt
├── manage.py
└── README.md
```

## 🛠️ Key Files

- **`models.py`**: Property model definition
- **`views.py`**: API endpoints and caching logic
- **`utils.py`**: Cache management utilities and Redis metrics
- **`signals.py`**: Automatic cache invalidation
- **`apps.py`**: App configuration and signal registration
- **`urls.py`**: URL routing configuration
- **`management/commands/manage_cache.py`**: CLI cache management

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation
- Ensure cache performance isn't degraded

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Django community for excellent caching framework
- Redis team for high-performance caching solution
- Docker team for containerization platform

## 📞 Support

For support, please:

1. Check the troubleshooting section
2. Review the API documentation
3. Open an issue on GitHub
4. Contact the development team

---

**Built with ❤️ using Django, Redis, and PostgreSQL**