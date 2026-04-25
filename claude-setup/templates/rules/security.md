# Security Rules

## Secrets
- NEVER hardcode secrets, API keys, passwords, or tokens in source code.
- Use environment variables or secret management (dotenv, vault, etc.).
- Add `.env`, `*.key`, `*.pem`, `credentials.json` to `.gitignore`.
- If a secret is committed accidentally: rotate it immediately, then purge from history.

## Input Validation
- Validate all external input at system boundaries (API endpoints, CLI args, file reads).
- SQL: parameterized queries only. Never string interpolation.
- Command execution: use `execFile`/`exec.Command` with arg arrays, never shell interpolation.
- File paths: validate against directory traversal (`../`).

## Authentication & Authorization
- Hash passwords with bcrypt/argon2, never MD5/SHA1.
- Use constant-time comparison for tokens and secrets.
- Validate JWTs: check signature, expiry, issuer, audience.
- Enforce authorization on every endpoint, not just at the router level.

## Data Exposure
- Never log secrets, tokens, passwords, or PII.
- Sanitize error messages returned to users — no stack traces, no internal paths.
- Use HTTPS for all external communication.
- Set appropriate CORS policies — never `*` in production.

## Dependencies
- Run `npm audit` / `pip-audit` / `govulncheck` before releases.
- Update dependencies with known CVEs promptly.
- Review new dependencies before adding: check maintenance, license, popularity.

## Code Review Flags
These patterns should always trigger security-reviewer:
- `auth/*`, `security/*`, `*secret*`, `*.env*`
- Schema or config changes
- New API endpoints
- Changes to permission/role logic
