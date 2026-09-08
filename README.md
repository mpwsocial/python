# MoiPayWay Python SDK

Official Python SDK for the [MoiPayWay API](https://documenter.getpostman.com/view/11919136/2s93Joz7Bq).

Use this client to call every endpoint in that collection: wallets, collections, transfers, users, verification, cards, catalogs, omnichain, and the rest of the documented surface.

```bash
pip install moipayway
```

```python
import os
from moipayway import Client

mpw = Client(os.environ["MOIPAYWAY_API_KEY"], environment="test")

countries = mpw.countries()
wallet = mpw.create_wallet({
    "code": "NGN",
    "meta": {"name": "Operations", "user_id": "user-uuid"},
})
order = mpw.initiate_collection({
    "order_reference_code": "ORD-1001",
    "meta": {
        "amount": "5000",
        "narration": "Invoice 1001",
        "wallet_id": "wallet-uuid",
        "user_id": "user-uuid",
    },
})
```

## API docs

Paths, methods, and request bodies are in the public collection:

[MoiPayWay API (Postman)](https://documenter.getpostman.com/view/11919136/2s93Joz7Bq)

Call any of those endpoints with `request()`:

```python
mpw.request("POST", "wallet/details", {"wallet_id": "..."})
mpw.request("GET", "user/misc/countries", auth=False)
```

- `test` → `https://dev.moipayway.co`
- `live` → `https://api.moipayway.co`
- Auth: `Authorization: Bearer <api_key>` (pass `auth=False` for documented catalog GETs)

## Webhooks

```python
from moipayway import verify_webhook

ok = verify_webhook(raw_body, signature_header, timestamp_header, os.environ["MOIPAYWAY_API_KEY"])
```
