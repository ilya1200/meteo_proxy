# Project Brief: Production-Ready Weather Proxy

## Project Overview
Build a production-ready REST API that acts as a proxy for the Open-Meteo weather service, demonstrating DevOps best practices including containerization, observability, resilience patterns, and CI/CD.

## Core Requirements

### 1. Functional Scope
- **Service Type**: REST API proxy for Open-Meteo weather provider
- **Endpoints**:
  - `GET /weather?city={city_name}` - Returns weather data (cached or fresh)
  - `GET /health` - Returns service health status
- **Caching**: Store third-party responses to minimize external calls

### 2. Observability & Logging
- Structured logging
- Request traceability and correlation
- Key metrics: request duration, upstream status codes

### 3. Reliability & Resilience
- Specific error handling for external API failures
- Retry mechanism or Circuit Breaker pattern

### 4. Infrastructure & Containerization
- Production-ready Dockerfile (optimized size/security)
- docker-compose.yml for application + sidecars (e.g., Redis)
- Single-command startup

### 5. CI/CD & Quality
- CI configuration with:
  - Code linters
  - Test suite execution
  - Docker image build
- Standard dependency management

### 6. Testing
- Unit Tests: Core business logic
- Integration Tests: API endpoints (mocked external provider)
- High test coverage

### 7. Documentation
- README.md with:
  - Local setup and run instructions
  - Architectural design decisions
  - List of future improvements

## Bonus Points (DevOps Focus)
- Helm Chart for Kubernetes deployment
- Public deployment (Render, Railway, Fly.io, AWS Free Tier)
- `/metrics` endpoint (Prometheus-compatible)
- Graceful shutdown (SIGTERM handling)

## Technical Stack
- **Language**: Python 3.12+
- **Framework**: Flask
- **Cache**: Redis (via docker-compose)
- **External API**: Open-Meteo (https://api.open-meteo.com/v1/forecast)

## External API Reference
Open-Meteo API endpoint:
```
https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m
```
- No API key required for non-commercial use (<10,000 daily calls)
- Returns JSON with hourly weather data
