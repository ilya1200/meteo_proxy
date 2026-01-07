Production-Ready Weather Proxy
1. Functional Scope
● Service: Build a REST API that acts as a proxy for a public weather provider (e.g., Open-Meteo).
● Endpoints:
○ GET /weather?city={city_name}: Returns weather data (cached or fresh).
○ GET /health: Returns service health status.
● Caching: Implement caching to store third-party responses and minimize external calls.
2. Observability & Logging
● Implement structured logging.
● Requests should be traceable and correlatable.
● Ensure key metrics such as request duration and upstream status codes are logged.
3. Reliability & Resilience
● Implement specific error handling for external API failures.
● Implement a Retry mechanism or Circuit Breaker pattern for the external provider.
4. Infrastructure & Containerization
● Provide a production-ready Dockerfile (optimized image size/security).
● Provide a docker-compose.yml to spin up the application and any sidecars (e.g., Redis).
● Ensure the environment runs successfully with a single command.
5. CI/CD & Quality
● Create a CI configuration file that:
○ Runs code linters.
○ Runs the test suite.
○ Builds the Docker image.
● Manage dependencies using standard tools.
6. Testing
● Unit Tests: Cover core business logic.
● Integration Tests: Verify API endpoints (mocking the external weather provider).
● Ensure high test coverage.
7. Documentation
● Provide a README.md containing:
○ Local setup and run instructions.
○ Architectural design decisions.
○ A list of improvements you would make given more time.
Bonus Points (DevOps Focus)
● Helm Chart: Wrap the application in a basic Helm chart for Kubernetes deployment.
● Public Deployment: Deploy the service to a cloud provider (e.g., Render, Railway, Fly.io, or AWS Free Tier) and provide a live URL.
● Metrics: Expose a /metrics endpoint compatible with Prometheus (tracking request latency and count).
● Graceful Shutdown: Ensure the application handles SIGTERM signals correctly to allow zero-downtime deployments.