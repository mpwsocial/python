# MoiPayWay Python SDK

```bash
pip install moipayway
```

```python
import os
from moipayway import Client

mpw = Client(os.environ["MOIPAYWAY_API_KEY"], environment="test")

wallet = mpw.wallet.create({
    "code": "NGN",
    "meta": {"name": "Operations", "user_id": "user-uuid"},
})
order = mpw.wallet.collection.initiate({
    "order_reference_code": "ORD-1001",
    "meta": {
        "amount": "5000",
        "narration": "Invoice 1001",
        "wallet_id": "wallet-uuid",
        "user_id": "user-uuid",
    },
})
individual = mpw.user.account.individual.create({
    # request body
})
job_types = mpw.user.misc.job_types()
lookup = mpw.verification.lookup({"code": "cac"})
```

Collection paths are methods on the client:

- `POST wallet/create` → `mpw.wallet.create(body)`
- `POST wallet/collection/initiate` → `mpw.wallet.collection.initiate(body)`
- `POST user/account/individual/create` → `mpw.user.account.individual.create(body)`
- `GET user/misc/job-types` → `mpw.user.misc.job_types()`
- `POST verification/lookup` → `mpw.verification.lookup(body)`
- `POST omnichain/wallet/evm/eoa/create-wallet` → `mpw.omnichain.wallet.evm.eoa.create_wallet(body)`

`test` uses `https://dev.moipayway.co`. `live` uses `https://api.moipayway.co`.

```python
from moipayway import verify_webhook

ok = verify_webhook(raw_body, signature_header, timestamp_header, os.environ["MOIPAYWAY_API_KEY"])
```
