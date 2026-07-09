# Template: Security Policy

`backend/templates/security.yaml` (`doc_type: security`) — for a
`SECURITY.md`, following GitHub's security-policy convention.

| Section | Required |
|---|---|
| Supported Versions | yes |
| Reporting a Vulnerability | yes |
| Disclosure Policy | no |
| Response Timeline | no |
| Scope | no |
| Contact | yes |

## Example SECURITY.md that passes this template

```markdown
# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| 2.x | yes |
| 1.x | security fixes only, until 2026-12-31 |
| < 1.0 | no |

## Reporting a Vulnerability

Please do not open a public issue for security reports. Email
security@example.com with:

- a description of the vulnerability
- steps to reproduce
- affected version(s)

We aim to acknowledge reports within 3 business days.

## Disclosure Policy

We follow coordinated disclosure: we ask that you not publicly disclose an
issue until we've released a fix and had 7 days to notify users.

## Response Timeline

- Acknowledgement: within 3 business days
- Triage & severity assessment: within 7 days
- Fix or mitigation: timeline depends on severity, communicated after triage

## Scope

Covers the `boardline` server and CLI. Third-party dependencies should be
reported upstream, though we'll help coordinate if needed.

## Contact

security@example.com (PGP key: `docs/security-pgp-key.asc`)
```
