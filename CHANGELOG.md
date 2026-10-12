# Changelog

All notable changes to `wajub` are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
`wajub` uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.1] — 2026-10-11

### Fixed
- **The package installs again.** `1.1.0` and `1.1.1` were published to PyPI
  as a wheel holding a single file, `wajub/py.typed`: `pip install wajub`
  succeeded and `import wajub` raised `ModuleNotFoundError`. The sdist was
  limited to that marker, and the wheel is built from the sdist. It now carries
  the whole `src/wajub` package, and a test builds the wheel the same way and
  checks every module is in it.
- **A missing webhook header** (`signature` or `timestamp` passed as `None`)
  raises `WebhookSignatureVerificationError` instead of an `AttributeError`, so
  your handler answers 400, not 500.

### Changed
- **The `409` for an `Idempotency-Key` still being processed is retried.** A
  call sent again after a timeout can reach the API while the first one is still
  running; the API answers `409` with `errors.idempotency_key`. The client now
  waits 2 then 4 seconds and asks again with the same key, within its usual 2
  retries, and returns the first request's result. Every other `409` is still
  raised at once.

## [1.2.0] — 2026-10-01

Tagged, never published to PyPI. Its one change ships with 1.2.1.

### Removed
- `payments.initialize()`, an alias of `payments.create()`. Call `create()`.
