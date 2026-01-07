# Weather Proxy Service - Architecture Diagrams

## Diagrams

| Diagram | Description |
|---------|-------------|
| [component_diagram.mmd](component_diagram.mmd) | Internal packages and their relationships |
| [system_design_diagram.mmd](system_design_diagram.mmd) | High-level architecture with external systems |
| [flow_diagram.mmd](flow_diagram.mmd) | Request flow sequence diagram |
| [error_flow_diagram.mmd](error_flow_diagram.mmd) | Error handling flowchart |
| [circuit_breaker_diagram.mmd](circuit_breaker_diagram.mmd) | Circuit breaker state machine |
| [class_diagram.mmd](class_diagram.mmd) | Classes and relationships |

## Quick Architecture Overview

```mermaid
flowchart LR
    CLIENT["Client"] --> API["REST API<br/>Flask"]
    API --> SVC["Services"]
    SVC --> REDIS[("Redis")]
    SVC --> OPEN["Open-Meteo API"]
    
    style API fill:#4a90d9,color:#fff
    style REDIS fill:#d32f2f,color:#fff
    style OPEN fill:#1976d2,color:#fff
```

## Viewing

- **VS Code**: Install "Markdown Preview Mermaid Support" extension
- **GitHub**: Renders automatically
- **Online**: [Mermaid Live Editor](https://mermaid.live/)
