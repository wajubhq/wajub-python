# Changelog

All notable changes to `wajub` are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
`wajub` uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Fixed
- **`payments.create()` keeps the idempotency key you put in its params.** It
  removed `idempotencyKey` from your dict, so creating again with the same dict,
  after a timeout for instance, went out without your key and could create a
  second payment. Your dict is left as it was, `idempotency_key` in the params
  counts as your key too, and a key that is not a string, or that differs from
  the one in `RequestOptions`, raises an error instead of being ignored.

## [1.2.1] — 2026-10-11

### Fixed
- **The package installs again.** With `1.1.0` and `1.1.1`, `pip install wajub`
  succeeded but `import wajub` raised `ModuleNotFoundError`: the package on
  PyPI did not contain the module. Install `1.2.1`.
- **A missing webhook header** (`signature` or `timestamp` passed as `None`)
  raises `WebhookSignatureVerificationError` instead of an `AttributeError`, so
  your handler answers 400, not 500.

### Changed
- **A create sent again with the same idempotency key while the first is still
  running** now returns the first request's result instead of a `409` error.

## [1.2.0] — 2026-10-01

Not published to PyPI. Its one change ships with 1.2.1.

### Removed
- `payments.initialize()`, an alias of `payments.create()`. Call `create()`.
