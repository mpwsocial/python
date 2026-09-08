from __future__ import annotations

import hashlib
import hmac
import json
import time
import urllib.error
import urllib.request
from typing import Any


BASES = {
    "test": "https://dev.moipayway.co",
    "live": "https://api.moipayway.co",
}


class ApiError(RuntimeError):
    def __init__(self, message: str, http_status: int = 0, payload: dict | None = None):
        super().__init__(message)
        self.http_status = http_status
        self.payload = payload or {}


def verify_webhook(
    raw_body: str | bytes,
    signature_header: str,
    timestamp_header: str,
    api_key: str,
    tolerance_seconds: int = 300,
) -> bool:
    if not raw_body or not signature_header or not timestamp_header or not api_key:
        return False
    if not str(timestamp_header).isdigit():
        return False
    age = abs(int(time.time()) - int(timestamp_header))
    if tolerance_seconds > 0 and age > tolerance_seconds:
        return False
    provided = signature_header
    if provided.lower().startswith("sha256="):
        provided = provided[7:]
    body = raw_body if isinstance(raw_body, (bytes, bytearray)) else str(raw_body).encode("utf-8")
    signed = timestamp_header.encode("utf-8") + b"." + body
    expected = hmac.new(api_key.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, provided)


class Client:
    def __init__(self, api_key: str, environment: str = "test", timeout: int = 30):
        env = (environment or "test").lower()
        if env not in BASES:
            raise ValueError("environment must be test or live")
        if not str(api_key).strip():
            raise ValueError("api_key is required")
        self.api_key = api_key.strip()
        self.environment = env
        self.timeout = timeout

    @property
    def base_url(self) -> str:
        return BASES[self.environment]

    def request(self, method: str, path: str, body: dict | None = None, auth: bool = True) -> dict[str, Any]:
        url = self.base_url.rstrip("/") + "/" + path.lstrip("/")
        data = None
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if auth:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if method.upper() not in ("GET", "HEAD"):
            data = json.dumps(body or {}, separators=(",", ":")).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as res:
                raw = res.read().decode("utf-8")
                http_status = res.status
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            http_status = exc.code
        except urllib.error.URLError as exc:
            raise ApiError("Unable to reach MoiPayWay") from exc

        try:
            decoded = json.loads(raw) if raw else {}
        except json.JSONDecodeError as exc:
            raise ApiError("Invalid JSON response", http_status) from exc

        status = str(decoded.get("status") or "").lower()
        if status in ("failed", "error"):
            raise ApiError(str(decoded.get("message") or "Request failed"), http_status, decoded)
        return decoded

    def post(self, path: str, body: dict | None = None) -> dict[str, Any]:
        return self.request("POST", path, body or {}, True)

    def get(self, path: str, auth: bool = True) -> dict[str, Any]:
        return self.request("GET", path, None, auth)

    def create_wallet(self, body: dict) -> dict[str, Any]:
        return self.post("wallet/create", body)

    def wallet_details(self, body: dict) -> dict[str, Any]:
        return self.post("wallet/details", body)

    def wallet_transactions(self, body: dict) -> dict[str, Any]:
        return self.post("wallet/transactions", body)

    def initiate_collection(self, body: dict) -> dict[str, Any]:
        return self.post("wallet/collection/initiate", body)

    def collection_info(self, order_reference_code: str) -> dict[str, Any]:
        return self.post("wallet/collection/info", {"order_reference_code": order_reference_code})

    def create_collection_method(self, body: dict) -> dict[str, Any]:
        return self.post("wallet/collection/method/create", body)

    def direct_transfer(self, body: dict) -> dict[str, Any]:
        return self.post("wallet/transfer/direct/single", body)

    def create_individual(self, body: dict) -> dict[str, Any]:
        return self.post("user/account/individual/create", body)

    def individual_details(self, body: dict) -> dict[str, Any]:
        return self.post("user/account/individual/details", body)

    def create_business(self, body: dict) -> dict[str, Any]:
        return self.post("user/account/business/create", body)

    def countries(self) -> dict[str, Any]:
        return self.get("user/misc/countries", auth=False)

    def job_types(self) -> dict[str, Any]:
        return self.get("user/misc/job-types", auth=False)

    def business_industries(self) -> dict[str, Any]:
        return self.get("user/misc/business-industry-list", auth=False)

    def business_registration_types(self) -> dict[str, Any]:
        return self.get("user/misc/business-registration-type", auth=False)

    def business_trade_types(self) -> dict[str, Any]:
        return self.get("user/misc/business-trade-type", auth=False)

    def business_product_service_types(self) -> dict[str, Any]:
        return self.get("user/misc/business-product-service-type", auth=False)

    def source_of_funds_types(self) -> dict[str, Any]:
        return self.get("user/misc/source-of-funds-type", auth=False)
