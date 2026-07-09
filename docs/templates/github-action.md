# Template: GitHub Action

`backend/templates/github-action.yaml` — for a reusable GitHub Action.

| Section | Required |
|---|---|
| Overview | yes |
| Inputs | yes |
| Outputs | yes |
| Usage | yes |
| Example Workflow | yes |
| Permissions | no |
| Contributing | no |
| License | no |

## Example README that passes this template

```markdown
# setup-readmint

A GitHub Action that installs the Readmint CLI and caches its dependencies.

## Overview

`setup-readmint` downloads the Readmint CLI for the runner's OS/arch,
adds it to `PATH`, and caches the download between runs.

## Inputs

| Name | Required | Default | Description |
|---|---|---|---|
| `version` | no | `latest` | Readmint CLI version to install |
| `token` | no | — | GitHub token used for the fetch/PR flow |

## Outputs

| Name | Description |
|---|---|
| `version` | The version that was installed |
| `cache-hit` | `true` if the binary was restored from cache |

## Usage

    - uses: example/setup-readmint@v1
      with:
        version: '2.3.0'

## Example Workflow

    name: Lint READMEs
    on: [pull_request]
    jobs:
      readmint:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - uses: example/setup-readmint@v1
          - run: readmint score README.md --template service

## Permissions

Requires `contents: read` to check out the repo; add `pull-requests: write`
only if a downstream step opens a PR with refined content.

## Contributing

See `CONTRIBUTING.md`; changes to `action.yml` require a version bump.

## License

MIT
```
