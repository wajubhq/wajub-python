# Wajub Python SDK

[![PyPI version](https://img.shields.io/pypi/v/wajub)](https://pypi.org/project/wajub/)
[![Python](https://img.shields.io/pypi/pyversions/wajub)](https://pypi.org/project/wajub/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Official server-side SDK for the [Wajub API](https://docs.wajub.com): create payments, confirm them, pay out and verify webhooks from your Python backend.

It runs on your server with a secret (`sk.…`, `sk_test.…`) or restricted (`rk.…`, `rk_test.…`) API key. Never expose these keys in client-side code: in the browser, use [Wajub.js](https://docs.wajub.com/libraries/components/js) with your publishable key (`pk.…`, `pk_test.…`).

## Requirements

| Requirement | Version |
|-------------|---------|
| Python | 3.10 or later |
| [httpx](https://www.python-httpx.org/) | 0.27 or later (installed automatically) |

## Installation

```bash
pip install wajub
```

## Quick start

Amounts are in the currency's **main unit**: `12.50` for GHS 12.50, `5000` for XAF 5,000.

```python
import os
from wajub import Wajub

wajub = Wajub(
    api_key=os.environ["WAJUB_API_KEY"],
    webhook_secret=os.environ["WAJUB_WEBHOOK_SECRET"],
)

payment = wajub.payments.create({
    "amount": 15000,
    "currency": "XAF",
    "email": "buyer@example.com",
    "reference": "order-1042",
    "callback": "https://shop.example.com/order/complete",
})

# Redirect the customer to payment.authorization_url,
# or mount payment.authorization_token with Wajub.js in your page.
```

Then confirm the result on your server: handle the `payment.succeeded` webhook, or call `wajub.payments.retrieve(payment.id)`.

Parameters go in as one dict with the API's field names. `create()` and `retrieve()` return an object whose fields read as attributes (`payment.authorization_url`) or keys (`payment["authorization_url"]`).

In a script, open the client in a `with Wajub() as wajub:` block so it is closed at the end. In a web process, build it once and leave it open.

## Configuration

The constructor takes keyword arguments only.

| Keyword | Description |
|---------|-------------|
| `api_key` | Secret or restricted API key (`sk.…`, `sk_test.…`, `rk.…`, `rk_test.…`). Falls back to `WAJUB_API_KEY`. |
| `webhook_secret` | Webhook signing secret (`whsec_…`), needed only for `webhooks.construct_event()`. Falls back to `WAJUB_WEBHOOK_SECRET`. |
| `http_client` | Your own `httpx.Client`, for a proxy or a timeout. Give it `base_url="https://api.wajub.com"`. |
| `max_network_retries` | How many times a temporary failure is retried. |

## Resources

| Purpose | Attribute | Methods |
|---------|-----------|---------|
| Payments | `wajub.payments` | `create`, `retrieve`, `list`, `cancel`, `process`, `process_split`, `list_refunds` |
| Refunds | `wajub.refunds` | `create`, `retrieve`, `list` |
| Customers | `wajub.customers` | `create`, `retrieve`, `update`, `delete`, `list`, `block`, `unblock`, `activate`, `deactivate`, `list_tax_ids`, `create_tax_id`, `delete_tax_id` |
| Payment links | `wajub.links` | `create`, `retrieve`, `update`, `delete`, `list` |
| Invoices | `wajub.invoices` | `create`, `retrieve`, `update`, `delete`, `list`, `send`, `mark_paid`, `cancel` |
| Payouts | `wajub.transfers` | `create`, `retrieve`, `list` |
| Payout recipients | `wajub.beneficiaries` | `create`, `retrieve`, `update`, `delete`, `list` |
| Destination checks | `wajub.identity` | `resolve`, `validate` |
| Balance | `wajub.balance` | `retrieve` |
| Disputes | `wajub.disputes` | `list`, `retrieve`, `submit_evidence`, `accept`, `close`, `send_message` |
| Events | `wajub.events` | `list`, `retrieve`, `resend` |
| Webhook endpoints | `wajub.webhook_endpoints` | `create`, `retrieve`, `update`, `delete`, `list`, `rotate_secret` |
| Webhook verification | `wajub.webhooks` | `construct_event` |
| Connected accounts (Sync) | `wajub.accounts` | `create`, `retrieve`, `update`, `delete`, `list`, `regenerate_token` |
| Tax | `wajub.tax` | `get_settings`, `update_settings`, `rates`, `calculate`, `reports`, `list_codes`, `retrieve_code`, `list_registrations`, `create_registration`, `retrieve_registration`, `update_registration`, `delete_registration`, `jurisdictions`, `thresholds`, `threshold_alerts` |
| Fraud (Shield) | `wajub.shield` | `get_settings`, `update_settings`, `stats`, `list_blocklist`, `add_to_blocklist`, `remove_from_blocklist` |
| Reference data | `wajub.global_` | `ping`, `channels`, `countries`, `currencies` |

`global` is a Python keyword, so the reference data lives on `wajub.global_`.

## Acting for a connected account

Pass the connected account with `sync` in the call's options:

```python
from wajub import RequestOptions

wajub.payments.create(params, RequestOptions(sync="acct_sync_ref"))
```

## Webhooks

Pass the **raw request body** (bytes), not parsed JSON, with the `X-Wajub-Signature` and `X-Wajub-Timestamp` headers. In Django:

```python
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from wajub import WebhookSignatureVerificationError

@csrf_exempt
def wajub_webhook(request):
    try:
        event = wajub.webhooks.construct_event(
            request.body,  # get_data() in Flask, await request.body() in FastAPI
            request.headers.get("X-Wajub-Signature"),
            request.headers.get("X-Wajub-Timestamp"),
        )
    except WebhookSignatureVerificationError:
        return HttpResponse(status=400)

    if event["event"] == "payment.succeeded":
        pass  # fulfil the order

    return HttpResponse(status=200)
```

A delivery that does not verify, or that lacks one of the headers, raises `WebhookSignatureVerificationError`. If your server's clock drifts, pass a tolerance in seconds as a fourth argument.

## Pagination

`list()` returns a page you can walk one page at a time, or iterate across all pages. Its rows are plain dicts:

```python
page = wajub.payments.list({"per_page": 50})
print(page.data, page.meta, page.has_more)

if page.has_more:
    next_page = page.get_next_page()

for payment in page.auto_paging_iter():
    print(payment["id"], payment["status"])
```

## Idempotency

Temporary failures are retried for you. To make a create safe to repeat on your side too, after a restart or in a job retry, pass your own key:

```python
from wajub import RequestOptions

wajub.payments.create(params, RequestOptions(idempotency_key=f"order-{order_id}"))
```

## Error handling

API errors raise a subclass of `WajubError`:

```python
from wajub import AuthenticationError, InvalidRequestError, RateLimitError, WajubError

try:
    wajub.payments.create(params)
except InvalidRequestError as e:
    print(e.field_errors)  # every validation message, by field
except AuthenticationError:
    pass  # check your API key
except RateLimitError as e:
    print(e.retry_after)  # seconds to wait
except WajubError as e:
    print(e.code, e.http_status, e.message)
```

| Class | Raised on |
|-------|-----------|
| `AuthenticationError` | `401` |
| `PermissionError` | `403` |
| `NotFoundError` | `404` |
| `InvalidRequestError` | `400`, `422` |
| `RateLimitError` | `429`, with `retry_after` in seconds |
| `ApiConnectionError` | No response: network error or timeout |
| `WajubError` | Any other error status, and the base of all of the above |

Every error carries `message`, `code`, `http_status`, `field_errors` (every validation message of each field), `errors` (the first message of each field) and `raw` (the response body). `wajub.PermissionError` shares its name with Python's builtin: import it by name, or catch `wajub.PermissionError`.

## Testing

Use a sandbox key (`sk_test.…`): the key chooses the environment, and no real money moves. The test phone numbers and cards are on [Test scenarios](https://docs.wajub.com/developer-tools/testing/test-scenarios). To receive webhooks on your machine, forward them with the [Wajub CLI](https://docs.wajub.com/developer-tools/cli/listen).

## Documentation & support

- Documentation: [docs.wajub.com/libraries/sdks/python](https://docs.wajub.com/libraries/sdks/python)
- Report issues: [github.com/wajubhq/wajub-python/issues](https://github.com/wajubhq/wajub-python/issues)

## License

MIT — see [LICENSE](LICENSE).
