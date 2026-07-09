# Template: CLI Tool

`backend/templates/cli-tool.yaml` — for a command-line tool or utility.

| Section | Required |
|---|---|
| Overview | yes |
| Installation | yes |
| Usage | yes |
| Commands | yes |
| Configuration | no |
| Examples | no |
| Contributing | no |
| License | yes |

## Example README that passes this template

```markdown
# gitprune

A CLI that finds and deletes merged local branches you no longer need.

## Overview

`gitprune` scans a repository, finds branches whose commits are fully
contained in `main`, and lets you delete them in one pass instead of
running `git branch --merged` and `git branch -d` by hand.

## Installation

    brew install gitprune
    # or
    go install github.com/example/gitprune@latest

## Usage

    gitprune [flags] [path]

Run `gitprune` inside a git repository to scan the current directory, or
pass a path to another repo.

## Commands

| Command | Description |
|---|---|
| `gitprune scan` | List branches that are safe to delete (default) |
| `gitprune clean` | Delete all branches found by `scan` |
| `gitprune clean --dry-run` | Print what would be deleted, without deleting |

## Configuration

`gitprune` reads `.gitprune.yaml` from the repo root:

```yaml
protect:
  - main
  - release/*
```

## Examples

    $ gitprune scan
    feature/login    merged 3 days ago
    fix/typo         merged 1 week ago

    $ gitprune clean
    Deleted 2 branches.

## Contributing

PRs welcome — see `CONTRIBUTING.md` for the dev setup and test commands.

## License

MIT
```
