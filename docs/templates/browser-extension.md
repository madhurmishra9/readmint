# Template: Browser Extension

`backend/templates/browser-extension.yaml` — for a Chrome/Firefox/Edge extension.

| Section | Required |
|---|---|
| Overview | yes |
| Features | no |
| Installation | yes |
| Permissions | yes |
| Development | yes |
| Building & Packaging | no |
| Privacy | no |
| License | no |

## Example README that passes this template

```markdown
# Tab Stash

Save all open tabs as a named group and restore them later, without
losing your current window layout.

## Overview

Tab Stash lets you sweep the current window's tabs into a named,
collapsible group in a side panel, then reopen any group later in one
click.

## Features

- Stash all tabs in the current window
- Search stashed groups by title or URL
- Restore a group into a new window or the current one

## Installation

- **Chrome / Edge**: install from the Chrome Web Store, or load
  `dist/` via `chrome://extensions` → "Load unpacked" for a dev build.
- **Firefox**: install from addons.mozilla.org, or load `dist/manifest.json`
  via `about:debugging` for a dev build.

## Permissions

| Permission | Reason |
|---|---|
| `tabs` | Read tab titles/URLs to stash and restore them |
| `storage` | Persist stashed groups locally |
| `sidePanel` | Render the stash list next to the page |

No host permissions are requested; the extension never reads page content.

## Development

    npm install
    npm run dev

Loads an unpacked build in `dist/` with hot reload for the popup and side
panel UI.

## Building & Packaging

    npm run build
    npm run package   # produces dist/tab-stash.zip for store submission

## Privacy

No tab data leaves the browser; stashed groups are stored in
`chrome.storage.local` only. See `PRIVACY.md` for the full policy.

## License

MIT
```
