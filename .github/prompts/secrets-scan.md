# Prompt: core/secrets_scan.py

Goal: detect secrets/PII in a README *before* it leaves the cluster.

Grounding:
- Regex families for known credentials (AWS keys, private keys, bearer/JWT,
  GitHub/Slack tokens) + a generic `KEY = value` matcher + Shannon-entropy
  heuristic for quoted high-entropy strings.
- High severity = {aws_access_key, private_key, github_token, bearer_token,
  slack_token, jwt}; everything else medium.
- `scan(md) -> Findings` (items carry masked match, severity, line).
- `redact(md) -> str` replaces only the secret *value*, right-to-left, keeping
  surrounding structure (e.g. the `API_KEY=` label survives).
- Default policy is BLOCK on high severity; redaction is opt-in data loss.

Red-team with: keys split across lines, base64 blobs, secrets inside code
fences, false positives (example/dummy tokens), unicode look-alikes.
