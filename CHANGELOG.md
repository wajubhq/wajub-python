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

### Deprecated
- **`listen.config()` and `listen.auth()`.** The API no longer offers them and
  answers `410 Gone`; calling either now also gives a `DeprecationWarning`. To
  receive webhooks on your machine, forward them with the Wajub CLI:
  `wajub listen`.

### Fixed
- **An id containing `/` is refused before anything is sent.** Such an id
  reached another endpoint: `payments.retrieve("pay_1/refunds")` listed the
  payment's refunds, and `customers.delete("cus_1/tax_ids/txi_1")` deleted a
  tax ID. Every method that takes an id now raises a `ValueError` for an id
  that is empty or contains `/`, written as is or as `%2F`. Wajub ids never do.
- **A validation error with a field that has no message** raised `IndexError`
  instead of `InvalidRequestError`. That field is now left out.
- **`payments.create()` keeps the idempotency key you put in its params.** It
  removed `idempotencyKey` from your dict, so creating again with the same dict,
  after a timeout for instance, went out without your key and could create a
  second payment. Your dict is now left as it was, and `idempotency_key` in the
  params counts as your key too. A key in the params that differs from the one
  in `RequestOptions` raises a `ValueError`, where the key in the params used to
  win silently. A key that is not a string raises a `TypeError` that names the
  param, instead of the HTTP client's.
- **The idempotency key in the params of `refunds.create()`, `transfers.create()`
  and the other creates is used.** It went out in the request body, where the
  API ignores it, and each call got a new key: creating again after a timeout
  could refund or pay out twice. `idempotencyKey` or `idempotency_key` in the
  params of any create, `payments.process()` or `payments.process_split()` now
  works as on `payments.create()`.
- **An `Idempotency-Key` you set in `RequestOptions(headers=...)` is sent
  alone.** A generated key replaced it, so a create you sent again was not
  recognised as the same one; with the name in lower case, both keys went out.
  The header now counts as your key, whatever its case, and one that differs
  from `idempotency_key` or from a key in the params raises a `ValueError`.
- **An empty idempotency key counts as no key, wherever you pass it.** With
  `RequestOptions(idempotency_key="")` a create went out without any key, so
  one the SDK retried after a network error could be made twice; it now gets a
  generated key, as when you pass none, and a key in the params is used.

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
