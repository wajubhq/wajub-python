# Changelog

All notable changes to `wajub` are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
`wajub` uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.3.0] — 2026-10-15

### Added
- **`field_errors` on API errors, every validation message of each field.** A
  `422` can give a field several messages; `errors` keeps only the first one.
  `e.field_errors["amount"]` lists them all, in the order the API sent them.
  `errors` is unchanged.

### Fixed
- **A validation error with a field that has no message** raised `IndexError`
  instead of `InvalidRequestError`. That field is now left out.
- **`payments.create()` keeps the idempotency key you put in its params.** It
  removed `idempotencyKey` from your dict, so creating again with the same dict,
  after a timeout for instance, went out without your key and could create a
  second payment. Your dict is left as it was, `idempotency_key` in the params
  counts as your key too, and a key that is not a string, or that differs from
  the one in `RequestOptions`, raises an error instead of being ignored.
- **The idempotency key in the params of `refunds.create()`, `transfers.create()`
  and the other creates is used.** It went out in the request body, where the
  API ignores it, and each call got a new key: creating again after a timeout
  could refund or pay out twice. `idempotencyKey` or `idempotency_key` in the
  params of any create, `payments.process()` or `payments.process_split()` now
  works as on `payments.create()`.

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
