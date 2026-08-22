# LLF Dashboard Architecture — V0.7

## Backend layers

API router -> Service -> Repository -> PostgreSQL

### API
HTTP concerns only: validation, auth dependency, response.

### Services
Business rules:
- duplicate shift prevention
- required parameter validation
- abnormal detection
- remarks requirement
- numeric validation

### Repositories
SQL/data access only.

### Schemas
Pydantic request models.

### Core
Configuration and security.

## Normalized data model

Line
  -> Equipment
      -> EquipmentParameter -> Parameter
      -> ShiftRecord -> Reading

This separates:
- what a parameter is
- which equipment uses it
- how it behaves on that equipment
- the shift instance
- the actual reading

That allows the same canonical parameter to be reused across hundreds of equipment.

## Scale path

Prototype:
React + FastAPI + PostgreSQL + Docker Compose

Production:
Reverse proxy / HTTPS
React static frontend
FastAPI workers
Managed PostgreSQL
Alembic migrations
Object storage if report files are persisted
Redis/job queue only if heavy report generation is later required
Central logs/metrics

Do not add Redis, queues or microservices until usage requires them.
