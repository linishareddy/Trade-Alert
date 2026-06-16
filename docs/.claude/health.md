# health

## Purpose
This module owns the basic API health check and environment status verifications.

## Public surface
- Routers: `/api/v1/health`
- Controllers: N/A
- Schemas: `HealthResponse`

## Key services
- N/A

## DB tables touched
- N/A

## Agents and prompts (if any)
- N/A

## Known gotchas / decisions
- Returns the current environment from settings.
