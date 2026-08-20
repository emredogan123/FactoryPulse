# ADR-001: Start with a Modular Monolith

- Status: Accepted
- Date: 2026-08-20

## Context

FactoryPulse has a three-week MVP deadline and one developer. The product includes identity, production, quality, simulation, analytics, alerts, and ML capabilities. A distributed architecture would add service discovery, network failure handling, multiple deployments, duplicated configuration, and harder local testing before product behavior is validated.

## Decision

Implement one FastAPI deployment organized into domain modules with explicit service and repository boundaries. Keep training scripts separable from API request handling. Use PostgreSQL as the authoritative operational store.

## Consequences

### Positive

- Faster end-to-end delivery
- Simpler transactions and local development
- Easier integration testing
- Clear path to a working portfolio demo

### Negative

- Modules share a deployment lifecycle
- Resource-heavy training cannot run inside normal API requests
- Future extraction requires stable module interfaces

## Rejected alternatives

### Microservices from Day 1

Rejected because operational complexity would dominate the three-week MVP and would not demonstrate business value.

### Kafka as a mandatory dependency

Rejected for the MVP because a reproducible simulator and persisted events are sufficient. Event streaming remains a documented future extension.

