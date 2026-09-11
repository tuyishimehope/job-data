# Job Data Ingestion Platform Backend

A Python backend for fetching Greenhouse job postings, filtering software engineering roles, and enriching job descriptions with structured fields through OpenRouter. FastAPI exposes the results over HTTP, with JSON logging and OpenTelemetry instrumentation.

**Status: development.** Requests perform ingestion synchronously. There is no database, background worker, or scheduler. Search currently reads a bundled JSON fixture, and the ingestion endpoint is a placeholder. See [Current limitations](#current-limitations) before relying on live results.

## Contents

- [Quick start](#quick-start)
- [Configuration](#configuration)
- [API reference](#api-reference)
- [Processing pipeline](#processing-pipeline)
- [Data models](#data-models)
- [Observability](#observability)
- [Project structure](#project-structure)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Current limitations](#current-limitations)

## Quick start

### Requirements

- Python **3.13 or newer**, as declared in `pyproject.toml`.
- `pip` and a virtual environment.
- Network access to Greenhouse for live job requests.
- An OpenRouter API key for successful LLM enrichment.
- A New Relic ingest license key for successful telemetry export.

Health, company listing, and fixture search do not call Greenhouse or the LLM. However, telemetry exporters are initialized for the entire application and attempt to export even when credentials are empty.

### Install

Run these commands from the repository root:

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1` instead.

If you do not already have a `.env` file, copy the example:

```bash
cp .env.example .env
```

On Windows PowerShell, use `Copy-Item .env.example .env`. Preserve an existing `.env` rather than overwriting its credentials.

Edit `.env` with these values, replacing the credential placeholders:

```dotenv
APP_NAME="Job Data Ingestion Platform Backend"
ENVIRONMENT="development"
GREENHOUSE_URL="https://boards-api.greenhouse.io/v1/boards"
OPENROUTER_API_KEY="your-openrouter-api-key"
NEW_RELIC_LICENSE_KEY="your-new-relic-ingest-license-key"
OTEL_EXPORTER_OTLP_PROTOCOL="http/protobuf"
```

The example file contains additional fields; their actual usage is documented below. Keep credentials out of source control.

### Run

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Run from the repository root: `.env` loading and fixture search use paths relative to the working directory. `--reload` is for development.

- API: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- OpenAPI schema: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

Verify the server in a second terminal:

```bash
curl -i http://127.0.0.1:8000/health
```

Expected body:

```json
{"status": "Healthy"}
```

This is a process health check; it does not verify Greenhouse, OpenRouter, or New Relic connectivity.

## Configuration

Settings are defined in [`app/core/settings.py`](app/core/settings.py), using Pydantic Settings. The application reads UTF-8 `.env` values at import time; environment variables override `.env`. Names are case-insensitive by default, so the lowercase names in `.env.example` also work. Restart the process after changing configuration.

All string settings default to an empty string except `app_name`, which defaults to `Job Data Ingestion Platform Backend`. Empty credentials do not disable integrations.

| Variable | Current use |
| --- | --- |
| `APP_NAME` | Service name in JSON logs and OpenTelemetry resources. Does not set the FastAPI documentation title. |
| `ENVIRONMENT` | Environment label in logs and telemetry. |
| `GREENHOUSE_URL` | Greenhouse board API base URL. Set to `https://boards-api.greenhouse.io/v1/boards` without a trailing slash. |
| `OPENROUTER_API_KEY` | Bearer token used for LLM requests. |
| `NEW_RELIC_LICENSE_KEY` | `api-key` header for trace, log, and metric export. |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | Passed as a `protocol` header on log exports. The implementation uses OTLP HTTP exporters regardless of this value. |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Declared in settings, but not used to select the application's export endpoints; those are hardcoded. |
| `OTEL_EXPORTER_OTLP_HEADERS` | Declared in settings, but not used to construct the explicit exporter headers. |
| `NEW_RELIC_LOG_URL` | Used by the separate `NewRelicLogClient`, which is not wired into application logging. |
| `NEW_RELIC_USER_KEY` | Declared but unused by the active application flow. |
| `LLM_API_URL`, `NVIDIA_API_KEY`, `HF_TOKEN`, `HF_URL`, `OPENAI_API_KEY` | Declared but unused by the active LLM integration. Setting them does not change its provider. |

The LLM endpoint and model are hardcoded in [`llm_service.py`](app/service/llm_integration/llm_service.py):

```text
Endpoint: https://openrouter.ai/api/v1/chat/completions
Model:    inclusionai/ling-3.0-flash-sante:free
```

These are the repository's configured values, not a guarantee of provider availability. Changing the provider, model, or telemetry destination currently requires code changes.

## API reference

All routes use `GET`. Job-board routes share the prefix `/api/v1/job-board`. No authentication is implemented.

| Route | Behavior | Response |
| --- | --- | --- |
| `/health` | Process health check. | `{"status":"Healthy"}` |
| `/api/v1/job-board/companies` | Return the configured board names without fetching jobs. | `{"total": N, "names": [...]}` |
| `/api/v1/job-board/companies/{company_name}` | Fetch, classify, enrich, and filter one Greenhouse board. | `{"total": N, "jobs": [...]}` or JSON `null` |
| `/api/v1/job-board/` | Process all configured boards sequentially and return retained jobs. | `{"total": N, "jobs": [...]}` |
| `/api/v1/job-board/ingest` | Placeholder; does not start ingestion. | `{"status":"Pending"}` |
| `/api/v1/job-board/jobs/search?visa_sponsorship=true` | Filter the bundled fixture by sponsorship. | A bare JSON array of matching fixture records. |

### List companies

```bash
curl http://127.0.0.1:8000/api/v1/job-board/companies
```

The list comes from `greenhouse_boards` in [`greenhouse.py`](app/service/job_board/greenhouse.py). The returned total counts configured entries, including case variants and duplicates; it does not count unique companies or verify board availability.

### Fetch jobs for a company

```bash
curl http://127.0.0.1:8000/api/v1/job-board/companies/remote
```

`company_name` is a Greenhouse board token and is interpolated into the upstream URL. It is not restricted to the configured list.

A successful response with no retained candidates is:

```json
{"total": 0, "jobs": []}
```

An upstream `404`, or an upstream response without `meta`, produces HTTP `200` with body `null`. Other upstream request errors and unhandled validation errors can produce HTTP `500`; there is no custom error mapping or standardized error envelope.

### Fetch all configured boards

```bash
curl http://127.0.0.1:8000/api/v1/job-board/
```

This can take substantial time: board requests and per-job LLM calls run sequentially. The aggregate path also enriches retained jobs a second time after each company has already enriched them. There is no pagination, caching, or streaming, and an unhandled error can terminate the whole request.

### Search the bundled fixture

```bash
curl 'http://127.0.0.1:8000/api/v1/job-board/jobs/search?visa_sponsorship=true'
curl 'http://127.0.0.1:8000/api/v1/job-board/jobs/search?visa_sponsorship=false'
```

`visa_sponsorship` is a required Boolean query parameter. Missing or invalid values return FastAPI's HTTP `422` validation response. Jobs whose sponsorship is `null` match neither `true` nor `false`.

Search reads [`app/examples/greenhouse_jobs.json`](app/examples/greenhouse_jobs.json) on each request. It does not search live ingestion results. Fixture records are returned unchanged, so their fields can differ from the normalized live response.

### Correlate requests

```bash
curl -i -H 'X-Request-ID: local-check-001' http://127.0.0.1:8000/health
```

The middleware uses the supplied request ID, or generates a UUID, and returns it in `X-Request-ID` on responses that complete through the middleware. Request logs include the same identifier.

## Processing pipeline

The live company service follows this sequence:

```text
Greenhouse GET /{board}/jobs?content=true
  -> Validate each job as NormalizedJob
  -> Set source and company; detect sponsorship and experience with text rules
  -> Filter software-role titles and excluded seniority terms
  -> Extract additional fields through OpenRouter
  -> Apply experience and seniority filters
  -> Return retained jobs
```

1. **Fetch:** Greenhouse requests use a 30-second timeout. A missing board returns `None`.
2. **Validate:** Raw records are passed directly to `NormalizedJob.model_validate`. There is no complete upstream-to-internal field mapper yet.
3. **Extract:** Text rules detect selected positive/negative sponsorship phrases and numeric experience requirements. Unknown values remain `None`.
4. **Classify:** Software-role keyword matches are required. Titles containing `senior`, `staff`, `principal`, `lead`, `director`, `manager`, `head`, or `vp` are excluded.
5. **Enrich:** The LLM receives the title, company, location, and posting content. Parsed JSON is validated with `JobAIExtraction`, and non-`None` fields overwrite the corresponding job fields.
6. **Filter:** Jobs with a minimum experience requirement of **6 or more years**, or an extracted experience level of `staff`, `principal`, or `director`, are removed. Unknown experience is retained.

LLM calls use a 10-second connection timeout and a 120-second read timeout. Handled HTTP, JSON, and validation errors are logged and leave the job at its pre-enrichment state. There is no retry or backoff policy and no configuration switch to skip LLM calls.

The `fit_role` dictionary is not applied as a matching policy. Live results are not restricted to visa sponsorship, relocation support, a particular language, or the two-year experience target recorded there.

## Data models

[`schema.py`](app/service/job_board/schema.py) defines the internal Pydantic models:

| Model | Purpose |
| --- | --- |
| `NormalizedJob` | Job identity, company, title, description/content, seniority, experience, skills, location, immigration, compensation, application links, lifecycle, and extraction metadata. `company_name` and `title` are required. |
| `JobLocation` | Raw location, city, state, country, country code, and remote type. |
| `Salary` | Minimum/maximum amount, currency, and salary period. |
| `JobAIExtraction` | LLM-extracted deadline, sponsorship details, relocation flag, experience, skills, technologies, and required languages. |

Enums describe remote type, employment type, source, salary period, and experience levels. `NormalizedJob.experience_level` currently accepts a string rather than the experience enum. Source enum entries beyond Greenhouse do not represent implemented integrations.

Many fields are optional and may be unpopulated. Sponsorship and relocation use `true`, `false`, or `null`; `null` means unknown. The API routes do not declare response models, so generated OpenAPI documentation does not fully describe these response schemas.

## Observability

Application startup configures JSON console logs and OTLP HTTP export for traces, logs, and metrics. FastAPI and outbound `requests` calls are instrumented.

- **Traces:** Custom spans include `greenhouse.fetch_jobs` and `enrich_and_filter_jobs`, with attributes such as `job.company`, `jobs.fetched_count`, `jobs.input_count`, and `jobs.output_count`.
- **Logs:** Console records include timestamp, level, logger, message, service, environment, and request ID when available. Middleware logs request start, completion, status, duration, and failures.
- **Metrics:** A periodic reader exports every **5 seconds**. HTTP instrumentation supplies metrics; the repository does not define custom `app.http.*` instruments.

Export destinations are hardcoded in [`tracing.py`](app/infrastructure/observability/tracing.py):

```text
https://otlp.nr-data.net/v1/traces
https://otlp.nr-data.net/v1/logs
https://otlp.nr-data.net/v1/metrics
```

There is no telemetry-disable setting. Blank or invalid New Relic credentials can cause background export errors while the API still serves requests.

`newrelic.ini` is not loaded by `app.main`, and the New Relic Python agent is not a declared dependency. `app/otel/collector-config.yaml` is not used by the normal startup command; its receiver addresses need revision to local listening addresses before using it as a local collector configuration. A collector is not required by the current direct-export setup.

## Project structure

```text
app/
├── main.py                         # FastAPI app and telemetry initialization
├── api/v1/job_board/job_board.py    # HTTP routes
├── core/
│   ├── settings.py                 # Environment and .env configuration
│   ├── logging.py                  # JSON console formatter
│   └── context.py                  # Request ID context variable
├── middleware/request_context.py   # Request IDs and request lifecycle logs
├── service/
│   ├── job_board/
│   │   ├── greenhouse.py           # Board list, fetching, enrichment, filtering
│   │   └── schema.py               # Internal models and enums
│   └── llm_integration/llm_service.py
├── utils/job_fields.py             # Role and description text rules
├── infrastructure/observability/
│   ├── tracing.py                  # Active OTLP exporters
│   └── new_relic.py                # Separate, unwired log client
├── examples/greenhouse_jobs.json    # Data source for fixture search
├── prompts/extract_job_fields.txt   # Reference prompt; not loaded by LLMService
└── otel/collector-config.yaml       # Collector configuration; not used at startup
tests/                              # Currently only an __init__.py
.env.example                        # Configuration template
newrelic.ini                        # Separate agent configuration
pyproject.toml                      # Dependencies and development tool settings
readme.md                           # Project documentation
```

## Development

Install the development dependency group with the upgraded `pip` from the quick start:

```bash
python -m pip install --group dev
```

This installs pytest, pytest-asyncio, HTTPX, Ruff, and mypy. If your pip version does not support `--group`, upgrade pip first.

Run checks from the repository root with the virtual environment active:

```bash
python -m ruff check .
python -m ruff format --check .
python -m mypy app
python -m pytest
```

Ruff targets Python 3.13 with an 88-character line length. Mypy is configured in strict mode. These commands describe the configured workflow, not a claim that the current code passes every check. The test directory currently contains no test cases; pytest reports no tests collected and exits with code `5`.

To format Python files intentionally:

```bash
python -m ruff format .
```

Common extension points:

- Add or correct Greenhouse board tokens in `greenhouse_boards`.
- Update active role keywords in `app/utils/job_fields.py` and seniority exclusions in the Greenhouse service.
- Change extraction fields in `JobAIExtraction` together with the inline prompt in `LLMService.extract_fields`. The separate prompt text file is not loaded.
- Add an explicit source mapping layer before validating raw jobs when extending normalization or introducing another board provider.
- Mock Greenhouse and OpenRouter requests in future tests to avoid depending on external services or paid calls.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| `ModuleNotFoundError` or `uvicorn` unavailable | Activate the virtual environment, install dependencies, and run from the repository root. |
| Settings validation error for an extra `.env` key | Compare `.env` with `Settings`. Unrecognized dotenv keys are rejected by the default settings behavior. |
| Invalid Greenhouse URL / missing scheme | Set `GREENHOUSE_URL`; its application default is empty. |
| Company request returns `null` | The upstream board returned `404`, or its response did not contain `meta`. Check the board token. |
| Live request fails with a model validation error | Raw jobs are validated before `company_name` is assigned. Payloads without that required field fail; see limitations below. |
| OpenRouter authentication or model errors | Check `OPENROUTER_API_KEY` and the hardcoded model. Setting `LLM_API_URL` or another provider's key has no effect. |
| New Relic exporter errors | Check `NEW_RELIC_LICENSE_KEY` and outbound connectivity. Empty credentials do not disable export. |
| Fixture search raises `FileNotFoundError` | Start the app from the repository root and confirm `app/examples/greenhouse_jobs.json` exists. |
| Search results do not reflect a live fetch | Search uses the checked-in fixture; live results are not saved to it. |
| All-board request is slow | Processing is sequential and includes repeated enrichment. Use a single-company request while investigating. |

## Current limitations

- **Incomplete source mapping:** Greenhouse records are validated before the service assigns `company_name`. Records lacking it fail validation. Fields such as `id`, `absolute_url`, `language`, and `location.name` are not mapped to `source_job_id`, application/source URLs, `posting_language`, and `location.raw`, respectively.
- **Role matching inconsistency:** Titles are lowercased, but some role keywords contain uppercase letters. Those keywords will not match as intended.
- **Repeated work:** The board list includes case variants/duplicates, results are not deduplicated, and the aggregate endpoint enriches retained jobs twice.
- **No ingestion job:** `/ingest` only returns `Pending`. The separate `ingest_all_companies()` helper returns inside its first loop iteration and is not connected to that route.
- **Limited error recovery:** There are no retries, per-board recovery for general failures, or structured API error responses. LLM fallback covers selected error classes rather than every possible malformed response.
- **No persistent workflow:** There is no database, cache, pagination, queue, scheduled ingestion, or background worker. Search and live ingestion use separate data paths.
- **No deployment package:** Authentication, authorization, Docker packaging, CI/CD, deployment configuration, and an automated test suite are not included.

These are implementation gaps, not configurable features. The repository provides a starting point for an ingestion service rather than a production-ready deployment.
