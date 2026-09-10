# Job Data Ingestion Platform

A backend service for ingesting, normalizing, filtering, and enriching software engineering job postings from external job-board APIs.

The platform currently integrates with Greenhouse job boards, identifies relevant software engineering opportunities, extracts structured job information, and exposes the resulting data through a FastAPI REST API.

The project also includes production-oriented observability using OpenTelemetry for distributed tracing, metrics, and structured logging.

---

## Overview

Job postings from different companies contain inconsistent titles, descriptions, experience requirements, visa information, and other metadata.

The Job Data Ingestion Platform provides a pipeline for converting this external job data into a consistent internal representation.

The current processing flow is:

```text
Greenhouse API
      │
      ▼
Fetch Job Postings
      │
      ▼
Normalize Job Data
      │
      ▼
Software Role Classification
      │
      ▼
Experience / Visa Detection
      │
      ▼
LLM Enrichment
      │
      ▼
Soft Filtering
      │
      ▼
Normalized API Response
```

The platform is currently focused on software engineering roles, particularly early-career opportunities.

---

## Features

### Job Ingestion

- Fetch job postings from Greenhouse job boards
- Ingest jobs for individual companies
- Ingest jobs across configured companies
- Handle unavailable Greenhouse boards
- Normalize external job data into a common schema

### Job Classification

The platform performs an initial classification before expensive enrichment operations.

It can:

- Identify software engineering roles
- Detect seniority from job titles
- Exclude senior, staff, principal, lead, management, and similar roles
- Identify junior, graduate, associate, new-grad, internship, and early-career roles

### Job Information Extraction

Job descriptions are analyzed to extract information such as:

- Minimum experience requirements
- Visa sponsorship information
- Experience level
- Relevant structured job attributes

### LLM Enrichment

Candidate jobs can be passed through the configured LLM integration to extract additional structured fields.

This provides a hybrid processing pipeline:

```text
Deterministic extraction
        +
LLM-based extraction
        +
Filtering
```

The deterministic filters reduce the number of irrelevant jobs sent to the LLM.

### Observability

The application is instrumented using OpenTelemetry.

Current telemetry includes:

- Distributed traces
- Application spans
- HTTP request traces
- Outbound HTTP client traces
- Structured logs
- HTTP request metrics
- Request duration histograms
- Active request metrics

Telemetry can be exported using OTLP to an OpenTelemetry-compatible observability backend such as New Relic.

---

## Technology Stack

| Area | Technology |
|---|---|
| Language | Python 3.13+ |
| API Framework | FastAPI |
| Validation | Pydantic |
| Configuration | Pydantic Settings |
| HTTP Client | Requests |
| Observability | OpenTelemetry |
| Telemetry Protocol | OTLP / HTTP Protobuf |
| APM / Observability Backend | New Relic |
| Job Source | Greenhouse Job Board API |
| Enrichment | LLM API |

---

## Project Structure

```text
job_ingestion_platform_backend/
│
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── job_board/
│   │
│   ├── core/
│   │   ├── context.py
│   │   ├── logging.py
│   │   └── settings.py
│   │
│   ├── infrastructure/
│   │   └── observability/
│   │       └── tracing.py
│   │
│   ├── middleware/
│   │   └── request_context.py
│   │
│   ├── service/
│   │   ├── job_board/
│   │   │   ├── greenhouse.py
│   │   │   └── schema.py
│   │   │
│   │   └── llm_integration/
│   │       └── llm_service.py
│   │
│   ├── utils/
│   │   └── job_fields.py
│   │
│   └── main.py
│
├── newrelic.ini
├── pyproject.toml
└── README.md
```

The structure may evolve as additional job sources and persistence mechanisms are introduced.

---

## Architecture

The application currently follows a layered structure.

```text
                 ┌─────────────────────┐
                 │      FastAPI        │
                 │      REST API       │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │     Middleware      │
                 │ Request Context     │
                 │ Observability       │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Job Board Services  │
                 └──────────┬──────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
       ┌─────────────────┐     ┌─────────────────┐
       │ Greenhouse API  │     │   LLM Service   │
       └─────────────────┘     └─────────────────┘
```

### Processing Strategy

The ingestion pipeline intentionally performs inexpensive deterministic operations before LLM enrichment.

```text
Job
 │
 ▼
Normalize
 │
 ▼
Software role?
 │
 ├── No ──► Reject
 │
 ▼
Seniority check
 │
 ├── Too senior ──► Reject
 │
 ▼
Extract known fields
 │
 ▼
LLM enrichment
 │
 ▼
Soft filter
 │
 ▼
Return candidate
```

This reduces unnecessary LLM requests and keeps the processing pipeline easier to reason about.

---

## Getting Started

### Prerequisites

Ensure you have:

- Python 3.13 or newer
- `pip`
- A Python virtual environment
- Required external API credentials

Check your Python version:

```bash
python3 --version
```

---

## Installation

Clone the repository:

```bash
git clone <repository-url>
cd job_ingestion_platform_backend
```

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

### macOS / Linux

```bash
source .venv/bin/activate
```

### Windows

```bash
.venv\Scripts\activate
```

Install the project:

```bash
pip install -e .
```

---

## Configuration

Application configuration is managed using `pydantic-settings`.

Create a `.env` file in the project root.

Example:

```env
APP_NAME="Job Data Ingestion Platform Backend"
ENVIRONMENT="development"

GREENHOUSE_URL="https://boards-api.greenhouse.io/v1/boards"

LLM_API_URL="<your-llm-endpoint>"
NVIDIA_API_KEY="<your-api-key>"

OTEL_SERVICE_NAME="Job Data Ingestion Platform Backend"
OTEL_EXPORTER_OTLP_ENDPOINT="https://otlp.nr-data.net"
OTEL_EXPORTER_OTLP_PROTOCOL="http/protobuf"
OTEL_EXPORTER_OTLP_HEADERS="api-key=<your-license-key>"
```

The exact variables required depend on the current `Settings` model.

> Never commit `.env`, API keys, license keys, or other credentials to source control.

---

## Running the Application

Start the development server:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

FastAPI interactive documentation is available at:

```text
http://127.0.0.1:8000/docs
```

Alternative API documentation is available at:

```text
http://127.0.0.1:8000/redoc
```

---

## API

The primary API is exposed under:

```text
/api/v1
```

Current job-board functionality includes operations for retrieving configured companies and querying job postings for a company.

For the complete and current API contract, use the generated OpenAPI documentation:

```text
/docs
```

---

## Health Check

The service exposes a health endpoint:

```http
GET /health
```

Example response:

```json
{
  "status": "Healthy"
}
```

The health endpoint currently verifies that the API process can serve requests. It does not currently represent a full dependency-readiness check.

---

## Observability

The application uses OpenTelemetry rather than coupling application instrumentation directly to a single observability vendor.

```text
Application
     │
     ├── Logs
     ├── Metrics
     └── Traces
          │
          ▼
    OpenTelemetry
          │
          ▼
        OTLP
          │
          ▼
      New Relic
```

### Tracing

FastAPI and outbound `requests` calls are instrumented.

A typical trace can contain:

```text
GET /api/v1/job-board/companies/{company}
│
├── Greenhouse HTTP request
│
└── enrich_and_filter_jobs
```

Custom spans can contain application-specific attributes such as:

```text
jobs.input_count
jobs.output_count
company
```

This makes it possible to identify where time is spent inside an ingestion request.

### Metrics

Application metrics include concepts such as:

```text
app.http.requests
app.http.request.duration
app.http.active_requests
```

These represent counters, histograms, and up/down counters used to understand request traffic, latency, and concurrency.

### Structured Logging

Application logs contain structured contextual fields such as:

```json
{
  "level": "INFO",
  "message": "Greenhouse jobs fetched",
  "service": "Job Data Ingestion Platform Backend",
  "environment": "development",
  "request_id": "...",
  "event": "greenhouse_jobs_fetched",
  "company": "cloudbeds",
  "total": 49
}
```

Request IDs are propagated through the request context so logs produced during the same request can be correlated.

---

## Code Quality

The project uses Ruff for Python linting and formatting.

Run the linter:

```bash
ruff check .
```

Automatically fix supported issues:

```bash
ruff check . --fix
```

Format the codebase:

```bash
ruff format .
```

The project targets modern Python syntax and can use features such as `StrEnum` where appropriate.

---

## Development Principles

The project currently follows several engineering principles:

**Normalize external data at system boundaries.** External APIs should be converted into internal models before application logic depends on them.

**Filter early.** Cheap deterministic checks should eliminate irrelevant jobs before expensive operations such as LLM calls.

**Keep vendor-specific infrastructure at the edges.** Application code emits OpenTelemetry telemetry rather than depending directly on New Relic throughout the business logic.

**Prefer structured telemetry.** Important information such as company, request ID, status code, job counts, and duration should be represented as attributes instead of being embedded only inside log messages.

**Instrument meaningful operations.** Custom spans should represent important units of work rather than tracing every function.

---

## Current Limitations

The project is under active development.

The following capabilities are **not currently implemented**:

- Persistent database storage
- Background job processing
- Authentication and authorization
- Docker/container packaging
- CI/CD pipeline
- Production deployment configuration
- Comprehensive automated test suite
- Caching
- Queue-based ingestion
- Scheduled ingestion

These should be documented as implemented features only after they are added to the system.

---

## Roadmap

Potential next stages include:

```text
Current
   │
   ├── Greenhouse ingestion
   ├── Normalization
   ├── Filtering
   ├── LLM enrichment
   └── Observability
          │
          ▼
Next
   ├── Persistence
   ├── Background ingestion
   ├── Additional job sources
   ├── Automated testing
   ├── Caching
   ├── Scheduling
   ├── CI/CD
   ├── Containerization
   └── Production deployment
```

---

## Status

**Development**

The platform currently provides the core job ingestion and enrichment pipeline and is being developed toward a production-ready job intelligence backend.