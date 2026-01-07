# Weather Proxy Service

A production-ready REST API that acts as a proxy for the Open-Meteo weather service, demonstrating DevOps best practices including containerization, observability, resilience patterns, and CI/CD.

## Features

- ✅ **Weather API Proxy**: Get current weather data by city name
- ✅ **Caching**: Redis-based caching with configurable TTL
- ✅ **Resilience**: Circuit breaker and retry patterns for fault tolerance
- ✅ **Observability**: Structured JSON logging with correlation IDs
- ✅ **Metrics**: Prometheus-compatible `/metrics` endpoint
- ✅ **Containerization**: Production-ready Docker setup with multi-stage builds
- ✅ **CI/CD**: GitHub Actions pipeline with linting, testing, and Docker builds

## Quick Start

### Prerequisites

- Python 3.12+
- Docker and Docker Compose (for containerized deployment)
- Redis (for caching)

### Option 1: Docker Compose (Recommended)

Start the entire stack with a single command:

```bash
docker-compose up -d
```

The service will be available at `http://localhost:8000`.

### Option 2: Local Development

1. Create virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

2. Start Redis (required for caching):

```bash
docker run -d -p 6379:6379 redis:7-alpine
```

3. Run the development server:

```bash
flask --app weather_proxy.app:create_app run --debug
```

## API Endpoints

### GET /weather?city={city_name}

Get current weather for a city.

**Request:**
```bash
curl "http://localhost:8000/weather?city=Berlin"
```

**Response (200 OK):**
```json
{
  "city": "Berlin",
  "country": "Germany",
  "coordinates": {
    "latitude": 52.52,
    "longitude": 13.41
  },
  "current": {
    "temperature": 15.2,
    "temperature_unit": "°C",
    "apparent_temperature": 14.5,
    "humidity": 65,
    "weather_code": 3,
    "weather_description": "Overcast",
    "wind_speed": 12.5,
    "wind_speed_unit": "km/h",
    "precipitation": 0,
    "is_day": true
  },
  "cached": false,
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**Error Response (404):**
```json
{
  "error": {
    "code": "CITY_NOT_FOUND",
    "message": "Could not find city: InvalidCity",
    "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }
}
```

### GET /health

Service health check with dependency status.

**Request:**
```bash
curl "http://localhost:8000/health"
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "dependencies": {
    "redis": "connected",
    "open_meteo": "available"
  },
  "uptime_seconds": 3600.25
}
```

### GET /metrics

Prometheus metrics endpoint.

**Request:**
```bash
curl "http://localhost:8000/metrics"
```

**Response:**
```
# HELP weather_requests_total Total number of weather requests
# TYPE weather_requests_total counter
weather_requests_total{endpoint="/weather",method="GET",status="success"} 150

# HELP weather_request_duration_seconds Request duration in seconds
# TYPE weather_request_duration_seconds histogram
weather_request_duration_seconds_bucket{endpoint="/weather",method="GET",le="0.1"} 120
...
```

## Configuration

Environment variables (set in `env/.env` or via Docker):

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `production` | Flask environment mode |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `CACHE_TTL_SECONDS` | `300` | Cache TTL (5 minutes) |
| `OPEN_METEO_BASE_URL` | `https://api.open-meteo.com` | Open-Meteo API URL |
| `CIRCUIT_BREAKER_FAIL_MAX` | `5` | Failures before circuit opens |
| `CIRCUIT_BREAKER_RESET_TIMEOUT` | `60` | Seconds before circuit closes |
| `REQUEST_TIMEOUT_SECONDS` | `10` | HTTP request timeout |
| `RETRY_MAX_ATTEMPTS` | `3` | Max retry attempts |
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_FORMAT` | `json` | Log format (json/console) |

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    WEATHER PROXY SERVICE                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Flask API + Gunicorn                                      │  │
│  │  • Correlation ID middleware                               │  │
│  │  • Structured logging (structlog)                          │  │
│  │  • Prometheus metrics                                      │  │
│  └───────────────────────────────────────────────────────────┘  │
│                            │                                     │
│  ┌─────────────────────────▼─────────────────────────────────┐  │
│  │  Service Layer                                             │  │
│  │  WeatherService │ CacheService │ GeocodingService          │  │
│  └─────────────────────────┬─────────────────────────────────┘  │
│                            │                                     │
│  ┌─────────────────────────▼─────────────────────────────────┐  │
│  │  Resilience Layer                                          │  │
│  │  • Circuit breaker (pybreaker)                             │  │
│  │  • Retry with exponential backoff (tenacity)               │  │
│  └─────────────────────────┬─────────────────────────────────┘  │
└────────────────────────────│─────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
   ┌─────────┐         ┌──────────┐        ┌───────────┐
   │  Redis  │         │ Open-    │        │ Open-     │
   │  Cache  │         │ Meteo    │        │ Meteo     │
   │ (5min)  │         │ Weather  │        │ Geocoding │
   └─────────┘         └──────────┘        └───────────┘
```

### Key Design Decisions

1. **Caching Strategy**: Redis with 5-minute TTL per city. Cache keys are normalized to lowercase.

2. **Resilience Pattern**: Circuit breaker (5 failures → open, 60s reset) combined with retry (3 attempts, exponential backoff).

3. **Logging**: JSON structured logs with correlation IDs for request tracing across services.

4. **Security**: Non-root Docker user, minimal base image, health checks.

5. **Error Handling**: Graceful degradation - cache failures don't break requests, external API failures return meaningful errors.

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/weather_proxy --cov-report=html

# Run only unit tests
pytest tests/unit -v

# Run only integration tests
pytest tests/integration -v
```

### Linting

```bash
# Check code style
ruff check src tests

# Format code
ruff format src tests
```

### Project Structure

```
weather-proxy/
├── src/weather_proxy/
│   ├── __init__.py
│   ├── app.py              # Flask app factory
│   ├── config.py           # Configuration management
│   ├── routes/
│   │   ├── health.py       # /health endpoint
│   │   └── weather.py      # /weather endpoint
│   ├── services/
│   │   ├── cache_service.py
│   │   ├── geocoding_service.py
│   │   └── weather_service.py
│   ├── middleware/
│   │   ├── correlation.py  # Request correlation IDs
│   │   └── logging.py      # Structured logging
│   ├── resilience/
│   │   └── circuit_breaker.py
│   └── utils/
│       └── metrics.py      # Prometheus metrics
├── tests/
│   ├── unit/
│   └── integration/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── .github/workflows/ci.yml
```

## Future Improvements

Given more time, these enhancements would be valuable:

1. **Helm Chart**: Kubernetes deployment configuration for production scaling
2. **Rate Limiting**: Add request rate limiting to prevent abuse
3. **API Versioning**: Add /v1/ prefix for API versioning
4. **OpenAPI Spec**: Generate OpenAPI/Swagger documentation
5. **Async Workers**: Use async/await for better concurrency
6. **Multi-day Forecasts**: Extend API to support forecast data
7. **WebSocket Support**: Real-time weather updates
8. **Geographic Fallback**: Reverse geocoding support
9. **Distributed Tracing**: Add OpenTelemetry integration
10. **Feature Flags**: Add feature flag support for gradual rollouts

## License

MIT
