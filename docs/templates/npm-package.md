# Template: NPM Package

`backend/templates/npm-package.yaml` — for a published npm (JS/TS) package.

| Section | Required |
|---|---|
| Overview | yes |
| Installation | yes |
| Usage | yes |
| API | no |
| TypeScript | no |
| Contributing | no |
| License | yes |

## Example README that passes this template

```markdown
# debounce-fn

A tiny, dependency-free debounce function for JavaScript and TypeScript.

## Overview

`debounce-fn` wraps a function so it only runs after a period of
inactivity, with support for cancelling and flushing pending calls.

## Installation

    npm install debounce-fn

## Usage

    import debounce from 'debounce-fn';

    const save = debounce(() => saveDraft(), { wait: 500 });
    input.addEventListener('input', save);

## API

### `debounce(fn, options)`

- `fn` — the function to debounce.
- `options.wait` — milliseconds to wait after the last call (default `100`).
- `options.immediate` — call `fn` on the leading edge instead of trailing.

Returns a wrapped function with `.cancel()` and `.flush()` methods.

## TypeScript

Type definitions are bundled; no `@types` package needed. Generic over the
wrapped function's argument and return types.

## Contributing

    npm install
    npm test

PRs should include a test for any behavior change.

## License

MIT
```
