# Template: VS Code Extension

`backend/templates/vscode-extension.yaml` — for a VS Code Marketplace extension.

| Section | Required |
|---|---|
| Overview | yes |
| Features | yes |
| Requirements | no |
| Extension Settings | yes |
| Known Issues | no |
| Release Notes | yes |
| License | no |

## Example README that passes this template

```markdown
# Todo Highlighter

Highlights `TODO`, `FIXME`, and `HACK` comments in the editor gutter.

## Overview

Todo Highlighter scans open files for marker comments and adds a gutter
icon plus a hover with the surrounding context, so pending work is visible
without a separate panel.

## Features

- Gutter icons for `TODO`, `FIXME`, `HACK`
- Command: "Todo Highlighter: List All in Workspace"
- Configurable marker list and colors

## Requirements

No external dependencies; works on any language mode.

## Extension Settings

This extension contributes:

- `todoHighlighter.markers` — array of marker strings to highlight (default
  `["TODO", "FIXME", "HACK"]`)
- `todoHighlighter.color` — gutter icon color (default `#e2c08d`)

## Known Issues

- Markers inside minified files are not detected.
- Very large files (>10k lines) may highlight with a short delay.

## Release Notes

### 1.2.0
Added the "List All in Workspace" command.

### 1.0.0
Initial release.

## License

MIT
```
