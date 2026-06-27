# Security Policy

We take the security of **dreaming-sdk** and its users seriously. Thank you for
helping keep the project and its community safe.

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.2.x   | ✅ |
| 0.1.x   | ✅ |
| < 0.1   | ❌ |

## Reporting a vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

Report privately using one of the following:

1. **GitHub Security Advisories** — preferred. Use the repository's
   *Security → Report a vulnerability* (private vulnerability reporting) flow.
2. **Email** — `security@chefgroep.online`.

Please include, where possible:

- A description of the vulnerability and its impact.
- Steps to reproduce or a proof of concept.
- Affected version(s) / commit.
- Any suggested remediation.

### What to expect

- We aim to acknowledge your report within **3 business days**.
- We will keep you informed of progress toward a fix and coordinate a disclosure
  timeline with you.
- We are happy to credit reporters who wish to be acknowledged.

## Handling of secrets and sensitive data

This project must never contain secrets or personal data in its source, history,
fixtures, or test data. In line with [AGENTS.md](./AGENTS.md):

- **Never commit** API keys, tokens, database URLs, Sentry DSNs, or other credentials.
- **Never commit** PII or raw session transcripts.
- Secrets are provided at runtime via environment variables / fleet env files and are
  never written into the repository.

If you discover committed secrets or PII, please report them via the private channels
above so they can be rotated and purged.
