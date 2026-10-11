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

## [1.2.0] — 2026-10-01

Tagged, never published to PyPI. Its one change ships with 1.2.1.

### Removed
- `payments.initialize()`, an alias of `payments.create()`. Call `create()`.
