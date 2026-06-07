## Framework

TBD - ex.  - Use langchain, langgraph, langsmith for generative AI programming; - Use Entra ID for authentication

## Repo Layout

```txt

main.py             # Thin wrapper: calls sample functions in my_package
src/my_package/
  __init__.py
  config.py         # Env var loading

tests/
  test_config.py

```

## Data Flow

TBD

## Testing Strategy

TBD - ex. Unit tests: mock `.env` with `pytest-mock`. No env vars leak into tests.

## Observability

TBD - ex. Use OpenTelemetry for logs, metrics, and traces

## Security

TBD
