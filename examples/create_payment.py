#!/usr/bin/env python3
"""Create a payment with the Wajub Python SDK."""

import os

from wajub import Wajub

with Wajub(api_key=os.environ.get("WAJUB_API_KEY", "sk_test_your_key")) as wajub:
    payment = wajub.payments.create(
        {
            "amount": 15000,
            "currency": "XAF",
            "email": "buyer@example.com",
            "callback": "https://shop.example.com/complete",
        }
    )

print(f"Payment {payment.id} — redirect buyer to:")
print(payment.authorization_url)
