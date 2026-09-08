# MoiPayWay Python SDK

Official Python client for MoiPayWay merchant REST APIs.

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

Any documented path:

```python
mpw.request("POST", "wallet/details", {"wallet_id": "..."})
```

Webhook verification:

```python
from moipayway import verify_webhook

ok = verify_webhook(raw_body, signature_header, timestamp_header, os.environ["MOIPAYWAY_API_KEY"])
```

Environment: `test` → `https://dev.moipayway.co`, `live` → `https://api.moipayway.co`.
