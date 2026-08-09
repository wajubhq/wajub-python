# Wajub Python SDK

[![PyPI version](https://img.shields.io/pypi/v/wajub)](https://pypi.org/project/wajub/)
[![Python](https://img.shields.io/pypi/pyversions/wajub)](https://pypi.org/project/wajub/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Official **server-side** SDK for the [Wajub merchant API](https://docs.wajub.com). Accept mobile-money and card payments across Africa with a Stripe-inspired, resource-oriented client.

Use **[Wajub.js](https://docs.wajub.com/libraries/components/js)** for embedded checkout in the browser. Use this SDK on your backend with a secret (`sk_`) or restricted (`rk_`) API key — never expose secret keys in client-side code.

This SDK covers the **merchant API**. It does not wrap checkout session endpoints (`/pay/*`), public link checkout (`/q/*`, `/i/*`), or sandbox simulation — those belong to Wajub.js or direct HTTP during the payment flow.

## Features

- Resource-oriented API (`wajub.payments`, `wajub.customers`, …)
- Automatic `Idempotency-Key` on mutating requests (override per call)
- Typed errors per HTTP status (`AuthenticationError`, `RateLimitError`, …)
- Automatic retries on 429 and 5xx (max 2, exponential backoff)
- Page-based pagination with `auto_paging_iter()` and `get_next_page()`
- Webhook signature verification (HMAC-SHA256, timestamp tolerance)

## Requirements

| Requirement | Version |
|-------------|---------|
| Python | 3.10 or later |
| HTTP client | [httpx](https://www.python-httpx.org/) 0.27+ (installed automatically) |

## Installation

```bash
pip install wajub
```

## Quick start

Amounts are passed in the **smallest currency unit** (e.g. cents for EUR/USD; whole francs for XAF).

### Redirect checkout

```python
import os
from wajub import Wajub

wajub = Wajub(api_key=os.environ["WAJUB_API_KEY"])

payment = wajub.payments.create({
    "amount": 15000,
    "currency": "XAF",
    "email": "buyer@example.com",
    "callback": "https://shop.example.com/order/complete",
})

print(payment.authorization_url)
```

### Inline / overlay (embed token)

```python
embed = wajub.payments.create({
    "amount": 15000,
    "currency": "XAF",
    "metadata": {"mode": "embed"},
})

# Pass to Wajub.js: embed.authorization_token
```

`create()` and `retrieve()` return a typed `Payment` object — prefer attribute access (`payment.authorization_url`). List pages from `list()` yield plain dicts.

## Django / Flask

```python
import os
from wajub import Wajub

wajub = Wajub(
    api_key=os.environ["WAJUB_API_KEY"],
    webhook_secret=os.environ.get("WAJUB_WEBHOOK_SECRET"),
)
```

### Webhook view (Django)

Use the **raw request body**:

```python
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from wajub import Wajub
from wajub import WebhookSignatureVerificationError

wajub = Wajub(api_key=os.environ["WAJUB_API_KEY"], webhook_secret=os.environ["WAJUB_WEBHOOK_SECRET"])

@csrf_exempt
def wajub_webhook(request):
    try:
        event = wajub.webhooks.construct_event(
            request.body,  # bytes — not request.POST or parsed JSON
            request.headers.get("X-Wajub-Signature", ""),
            request.headers.get("X-Wajub-Timestamp", ""),
        )
    except WebhookSignatureVerificationError:
        return HttpResponseBadRequest()

    if event.get("type") == "payment.succeeded":
        pass  # fulfill order

    return HttpResponse(status=200)
```

> **Note:** `global` is a Python keyword. Use `wajub.global_` to access global resources.

## Configuration

| Variable | Description |
|----------|-------------|
| `WAJUB_API_KEY` | Secret or restricted API key (`sk_`, `sk_test.`, `rk_`, …) |
| `WAJUB_WEBHOOK_SECRET` | Webhook signing secret (`whsec_`) for `construct_event()` |

Test mode is selected by your API key prefix (`sk_test.…`), not by the API URL. Production calls always go to `https://api.wajub.com`.

## Resources (merchant API)

| Attribute | Methods |
|-----------|---------|
| `wajub.global_` | `ping`, `channels`, `countries`, `currencies` |
| `wajub.payments` | `create`, `initialize`, `retrieve`, `list`, `cancel`, `process`, `process_split`, `list_refunds` |
| `wajub.customers` | `create`, `retrieve`, `update`, `delete`, `list`, `block`, `unblock`, `activate`, `deactivate`, `list_tax_ids`, `create_tax_id`, `delete_tax_id` |
| `wajub.refunds` | `create`, `retrieve`, `list` |
| `wajub.transfers` | `create`, `retrieve`, `list` |
| `wajub.beneficiaries` | `create`, `retrieve`, `update`, `delete`, `list` |
| `wajub.links` | `create`, `retrieve`, `update`, `delete`, `list` |
| `wajub.invoices` | `create`, `retrieve`, `update`, `delete`, `list`, `send`, `mark_paid`, `cancel` |
| `wajub.accounts` | `create`, `retrieve`, `update`, `delete`, `list`, `regenerate_token` |
| `wajub.webhook_endpoints` | `create`, `retrieve`, `update`, `delete`, `list`, `rotate_secret` |
| `wajub.balance` | `retrieve` |
| `wajub.events` | `list`, `retrieve`, `resend` |
| `wajub.disputes` | `list`, `retrieve`, `submit_evidence`, `accept`, `close`, `send_message` |
| `wajub.identity` | `resolve`, `validate` |
| `wajub.tax` | `get_settings`, `update_settings`, `rates`, `calculate`, `reports`, `list_codes`, `retrieve_code`, `list_registrations`, `create_registration`, `retrieve_registration`, `update_registration`, `delete_registration`, `jurisdictions`, `thresholds`, `threshold_alerts` |
| `wajub.shield` | `get_settings`, `update_settings`, `stats`, `list_blocklist`, `add_to_blocklist`, `remove_from_blocklist` |
| `wajub.listen` | `config`, `auth` |
| `wajub.webhooks` | `construct_event` (local — no HTTP) |

## Sync (Connect)

```python
from wajub import RequestOptions

wajub.payments.create(params, RequestOptions(sync="acct_sync_ref"))
```

## Webhooks

```python
from wajub import WebhookSignatureVerificationError

try:
    event = wajub.webhooks.construct_event(
        raw_body,  # bytes — must be raw body, not parsed JSON
        request.headers["X-Wajub-Signature"],
        request.headers["X-Wajub-Timestamp"],
    )
except WebhookSignatureVerificationError:
    return 400

if event.get("type") == "payment.succeeded":
    pass  # fulfill order
```

During local development, use the [Wajub CLI](https://github.com/wajubhq/wajub-cli) to forward webhooks to your machine.

## Pagination

```python
page = wajub.payments.list({"per_page": 50})

for payment in page.auto_paging_iter():
    print(payment["id"], payment["status"])

# Manual page control
first = wajub.payments.list()
if first.has_more:
    second = first.get_next_page()
```

## Idempotency

POST and PUT requests automatically receive an `Idempotency-Key` header. Pass your own:

```python
from wajub import RequestOptions

wajub.payments.create(params, RequestOptions(idempotency_key=f"order-{order_id}"))
```

## Error handling

```python
from wajub import AuthenticationError, InvalidRequestError, RateLimitError

try:
    wajub.payments.create(params)
except InvalidRequestError as e:
    print(e.errors)  # field-level validation errors
except AuthenticationError:
    pass  # 401 — bad API key
except RateLimitError:
    pass  # 429 — back off and retry
```

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Documentation & support

- Full API reference: [docs.wajub.com/libraries/sdks/python](https://docs.wajub.com/libraries/sdks/python)
- Report issues: [github.com/wajubhq/wajub-python/issues](https://github.com/wajubhq/wajub-python/issues)

## License

MIT — see [LICENSE](LICENSE).
