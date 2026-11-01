# MoiPayWay SDK

Official merchant REST SDK. Environments: `test` → `https://dev.moipayway.co`, `live` → `https://api.moipayway.co`.

API reference: [https://documenter.getpostman.com/view/11919136/2sBYHXPdcb](https://documenter.getpostman.com/view/11919136/2sBYHXPdcb)

Collection paths become nested methods (example):

- `POST wallet/create` → client `wallet.create`
- `POST wallet/collection/initiate` → client `wallet.collection.initiate`
- `POST omnichain/tokenization/standards/erc20/deploy` → client `omnichain.tokenization.standards.erc20.deploy`

Deprecated flat tokenization paths (`omnichain/tokenization/erc20/...`) remain as aliases and call the `/standards/` routes.

```bash
pip install moipayway
```

```python
import os
from moipayway import Client

mpw = Client(os.environ['MOIPAYWAY_API_KEY'], environment='test')
wallet = mpw.wallet.create({'code': 'NGN', 'meta': {'name': 'Ops', 'user_id': 'user-uuid'}})
```
