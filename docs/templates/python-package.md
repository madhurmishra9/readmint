# Template: Python Package

`backend/templates/python-package.yaml` — for a PyPI-published Python package.

| Section | Required |
|---|---|
| Overview | yes |
| Installation | yes |
| Quickstart | yes |
| API Reference | no |
| Development | no |
| Testing | no |
| Contributing | no |
| License | yes |

## Example README that passes this template

```markdown
# retrybox

Retry decorators for Python with exponential backoff and jitter.

## Overview

`retrybox` provides a `@retry` decorator that retries a function on
specific exceptions, with configurable backoff, jitter, and a max attempt
count — no external dependencies.

## Installation

    pip install retrybox

## Quickstart

    from retrybox import retry

    @retry(exceptions=(ConnectionError,), max_attempts=5, backoff=0.5)
    def fetch():
        return requests.get("https://example.com").json()

## API Reference

### `retry(exceptions, max_attempts=3, backoff=0.1, jitter=True)`

- `exceptions` — tuple of exception types that trigger a retry.
- `max_attempts` — total attempts before the last exception is raised.
- `backoff` — base delay in seconds; doubles each attempt.
- `jitter` — add random jitter to avoid thundering-herd retries.

## Development

    git clone https://github.com/example/retrybox.git
    cd retrybox
    pip install -e ".[dev]"

## Testing

    pytest

## Contributing

Open an issue describing the change before submitting a PR for anything
beyond a small fix.

## License

MIT
```
