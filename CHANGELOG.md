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

### Changed
- **Two different idempotency keys, or two different `X-Sync` values, for one
  request raise a `ValueError`.** This covers a key in the params and another
  in `RequestOptions`, both `idempotencyKey` and `idempotency_key` in the
  params, `idempotency_key` and an `Idempotency-Key` header, and `sync` and an
  `X-Sync` header. With 1.2.1, one of them was ignored without a word, or both
  went out. Give each one once.

### Deprecated
- **`listen.config()` and `listen.auth()`.** The API no longer offers them and
  answers `410 Gone`; calling either now also gives a `DeprecationWarning`. To
  receive webhooks on your machine, forward them with the Wajub CLI:
  `wajub listen`.

### Fixed
- **An API key that cannot be sent is refused, without showing it.** A key
  with a line break, a space or a non-ASCII character, as a bad copy can leave,
  failed with an error that could show the key in full. `Wajub()` now raises a
  `ValueError` that names the problem, not the key, and nothing is sent.
- **The idempotency key you give protects every create.** Given in the params
  of `payments.create()`, it was removed from your dict, so creating again with
  the same dict could create a second payment. Given in the params of
  `refunds.create()`, `transfers.create()` and the other creates, or as an
  `Idempotency-Key` header in `RequestOptions(headers=...)`, it was not used, so
  a create sent again after a timeout could refund or pay out twice. Now
  `idempotencyKey` or `idempotency_key` in the params of any create,
  `payments.process()` or `payments.process_split()`, and an `Idempotency-Key`
  header in any case, count as your key, and your dict is left as it was. A key
  that is not a string raises a `TypeError` that says where you gave it.
- **An empty or blank idempotency key counts as no key, wherever you give it.**
  With `RequestOptions(idempotency_key="")`, a create retried after a network
  error could be made twice; it is now protected as when you give no key, and a
  key in the params is used. Spaces around a key are ignored. A key must be one
  the API accepts: letters, digits and `._:-`, up to 128 characters.
- **A header you set in `RequestOptions(headers=...)` goes out once, whatever
  the case of its name.** `authorization`, `x-sync`, `accept` or
  `content-type` in lower case went out beside the SDK's own. An
  `Authorization` header replaces the client's key for that request, as it
  already did when written `Authorization`, and is checked like it: an empty
  one raises `ValueError`, one that is not a string `TypeError`. An `X-Sync`
  header counts as `RequestOptions(sync=...)`; a blank one counts as none.
- **A validation error with a field that has no message** raised `IndexError`
  instead of `InvalidRequestError`. That field is now left out.

### Security
- **An id that is not a Wajub id is refused before anything is sent.** If an id
  you pass can come from a URL or a form, a call could act on another resource
  of your account: `customers.delete("cus_1/tax_ids/txi_1")` deleted a tax ID.
  An id that is empty, `.` or `..`, or contains `/`, now raises `ValueError`,
  and one that is not a string `TypeError`. Wajub ids never take these forms,
  so valid calls are unchanged.

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
