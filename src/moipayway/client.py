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
    def __init__(self, api_key: str = "", environment: str = "test", timeout: int = 30):
        env = (environment or "test").lower()
        if env not in BASES:
            raise ValueError("environment must be test or live")
        self.api_key = str(api_key).strip()
        self.environment = env
        self.timeout = timeout
        self.account = Account(self)
        self.authentication = Authentication(self)
        self.card = Card(self)
        self.misc = Misc(self)
        self.omnichain = Omnichain(self)
        self.simulation = Simulation(self)
        self.user = User(self)
        self.verification = Verification(self)
        self.wallet = Wallet(self)

    @property
    def base_url(self) -> str:
        return BASES[self.environment]

    def request(self, method: str, path: str, body: dict | None = None, auth: bool = True) -> dict[str, Any]:
        url = self.base_url.rstrip("/") + "/" + path.lstrip("/")
        data = None
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if auth:
            if not self.api_key:
                raise ValueError("api_key is required")
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


class Account:
    def __init__(self, client: "Client"):
        self._client = client
        self.merchant = AccountMerchant(client)


class AccountMerchant:
    def __init__(self, client: "Client"):
        self._client = client
        self.product = AccountMerchantProduct(client)
        self.team = AccountMerchantTeam(client)

    def resend_webhook(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'account/merchant/resend-webhook', body or {}, True)

    def update_notification(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'account/merchant/update-notification', body or {}, True)


class AccountMerchantProduct:
    def __init__(self, client: "Client"):
        self._client = client
        self.subscription = AccountMerchantProductSubscription(client)

    def update(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'account/merchant/product/update', body or {}, True)

    def view(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'account/merchant/product/view', body or {}, True)


class AccountMerchantProductSubscription:
    def __init__(self, client: "Client"):
        self._client = client

    def class_(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'account/merchant/product/subscription/class', body or {}, True)

    def class_product_type(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'account/merchant/product/subscription/class-product-type', body or {}, True)

    def finalise(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'account/merchant/product/subscription/finalise', body or {}, True)

    def history(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'account/merchant/product/subscription/history', body or {}, True)

    def initiate(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'account/merchant/product/subscription/initiate', body or {}, True)


class AccountMerchantTeam:
    def __init__(self, client: "Client"):
        self._client = client
        self.permission = AccountMerchantTeamPermission(client)

    def add(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'account/merchant/team/add', body or {}, True)

    def logs(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'account/merchant/team/logs', body or {}, True)

    def remove(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'account/merchant/team/remove', body or {}, True)

    def update(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'account/merchant/team/update', body or {}, True)

    def view(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'account/merchant/team/view', body or {}, True)


class AccountMerchantTeamPermission:
    def __init__(self, client: "Client"):
        self._client = client

    def add(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'account/merchant/team/permission/add', body or {}, True)

    def remove(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'account/merchant/team/permission/remove', body or {}, True)

    def update(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'account/merchant/team/permission/update', body or {}, True)

    def view(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'account/merchant/team/permission/view', body or {}, True)


class Authentication:
    def __init__(self, client: "Client"):
        self._client = client

    def connect(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'authentication/connect', body or {}, True)

    def initiate(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'authentication/initiate', body or {}, False)

    def sign_out(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'authentication/sign-out', body or {}, True)

    def validate(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'authentication/validate', body or {}, True)


class Card:
    def __init__(self, client: "Client"):
        self._client = client

    def close(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'card/close', body or {}, True)

    def create(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'card/create', body or {}, True)

    def details(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'card/details', body or {}, True)

    def freeze(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'card/freeze', body or {}, True)

    def fund(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'card/fund', body or {}, True)

    def resubscribe(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'card/resubscribe', body or {}, True)

    def supported(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'card/supported', body or {}, True)

    def unfreeze(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'card/unfreeze', body or {}, True)

    def update_security_settings(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'card/update-security-settings', body or {}, True)

    def withdraw(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'card/withdraw', body or {}, True)


class Misc:
    def __init__(self, client: "Client"):
        self._client = client

    def actions(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'actions', body or {}, True)

    def codes(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'codes', body or {}, True)

    def countries(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'countries', body or {}, True)

    def file_upload(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'file-upload', body or {}, True)

    def payment_purpose(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'payment-purpose', body or {}, True)

    def products(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'products', body or {}, True)

    def state_province_region(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'state-province-region', body or {}, True)

    def supported_currencies(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'supported-currencies', body or {}, True)


class Omnichain:
    def __init__(self, client: "Client"):
        self._client = client
        self.storage = OmnichainStorage(client)
        self.tokenization = OmnichainTokenization(client)
        self.wallet = OmnichainWallet(client)


class OmnichainStorage:
    def __init__(self, client: "Client"):
        self._client = client

    def details(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/storage/details', body or {}, True)

    def upload(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/storage/upload', body or {}, True)


class OmnichainTokenization:
    def __init__(self, client: "Client"):
        self._client = client
        self.erc1155 = OmnichainTokenizationErc1155(client)
        self.erc20 = OmnichainTokenizationErc20(client)
        self.erc721 = OmnichainTokenizationErc721(client)
        self.sep41 = OmnichainTokenizationSep41(client)


class OmnichainTokenizationErc1155:
    def __init__(self, client: "Client"):
        self._client = client

    def balance(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/tokenization/erc1155/balance', body or {}, True)

    def burn(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/tokenization/erc1155/burn', body or {}, True)

    def deploy(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/tokenization/erc1155/deploy', body or {}, True)

    def mint(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/tokenization/erc1155/mint', body or {}, True)

    def transactions(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/tokenization/erc1155/transactions', body or {}, True)

    def transfer(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/tokenization/erc1155/transfer', body or {}, True)


class OmnichainTokenizationErc20:
    def __init__(self, client: "Client"):
        self._client = client

    def balance(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/tokenization/erc20/balance', body or {}, True)

    def burn(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/tokenization/erc20/burn', body or {}, True)

    def chains(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('GET', 'omnichain/tokenization/erc20/chains', body or {}, True)

    def deploy(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/tokenization/erc20/deploy', body or {}, True)

    def mint(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/tokenization/erc20/mint', body or {}, True)

    def transactions(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/tokenization/erc20/transactions', body or {}, True)

    def transfer(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/tokenization/erc20/transfer', body or {}, True)


class OmnichainTokenizationErc721:
    def __init__(self, client: "Client"):
        self._client = client

    def balance(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/tokenization/erc721/balance', body or {}, True)

    def burn(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/tokenization/erc721/burn', body or {}, True)

    def deploy(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/tokenization/erc721/deploy', body or {}, True)

    def mint(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/tokenization/erc721/mint', body or {}, True)

    def transactions(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/tokenization/erc721/transactions', body or {}, True)

    def transfer(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/tokenization/erc721/transfer', body or {}, True)


class OmnichainTokenizationSep41:
    def __init__(self, client: "Client"):
        self._client = client

    def balance(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/tokenization/sep41/balance', body or {}, True)

    def burn(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/tokenization/sep41/burn', body or {}, True)

    def deploy(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/tokenization/sep41/deploy', body or {}, True)

    def mint(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/tokenization/sep41/mint', body or {}, True)

    def transactions(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/tokenization/sep41/transactions', body or {}, True)

    def transfer(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/tokenization/sep41/transfer', body or {}, True)


class OmnichainWallet:
    def __init__(self, client: "Client"):
        self._client = client
        self.evm = OmnichainWalletEvm(client)
        self.stellar = OmnichainWalletStellar(client)


class OmnichainWalletEvm:
    def __init__(self, client: "Client"):
        self._client = client
        self.eoa = OmnichainWalletEvmEoa(client)


class OmnichainWalletEvmEoa:
    def __init__(self, client: "Client"):
        self._client = client
        self.operations = OmnichainWalletEvmEoaOperations(client)
        self.transfer = OmnichainWalletEvmEoaTransfer(client)

    def balance(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/wallet/evm/eoa/balance', body or {}, True)

    def chains(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('GET', 'omnichain/wallet/evm/eoa/chains', body or {}, True)

    def create_wallet(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/wallet/evm/eoa/create-wallet', body or {}, True)

    def generate_address(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/wallet/evm/eoa/generate-address', body or {}, True)

    def supported_stablecoin(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('GET', 'omnichain/wallet/evm/eoa/supported-stablecoin', body or {}, True)

    def transactions(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/wallet/evm/eoa/transactions', body or {}, True)


class OmnichainWalletEvmEoaOperations:
    def __init__(self, client: "Client"):
        self._client = client

    def broadcast_transaction(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/wallet/evm/eoa/operations/broadcast-transaction', body or {}, True)

    def estimate_gas(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/wallet/evm/eoa/operations/estimate-gas', body or {}, True)

    def sign_transaction(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/wallet/evm/eoa/operations/sign-transaction', body or {}, True)


class OmnichainWalletEvmEoaTransfer:
    def __init__(self, client: "Client"):
        self._client = client

    def native_token(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/wallet/evm/eoa/transfer/native-token', body or {}, True)

    def stablecoin(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/wallet/evm/eoa/transfer/stablecoin', body or {}, True)


class OmnichainWalletStellar:
    def __init__(self, client: "Client"):
        self._client = client
        self.eoa = OmnichainWalletStellarEoa(client)


class OmnichainWalletStellarEoa:
    def __init__(self, client: "Client"):
        self._client = client
        self.operations = OmnichainWalletStellarEoaOperations(client)
        self.transfer = OmnichainWalletStellarEoaTransfer(client)

    def balance(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/wallet/stellar/eoa/balance', body or {}, True)

    def create_wallet(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/wallet/stellar/eoa/create-wallet', body or {}, True)

    def generate_address(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/wallet/stellar/eoa/generate-address', body or {}, True)

    def supported_stablecoin(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('GET', 'omnichain/wallet/stellar/eoa/supported-stablecoin', body or {}, True)

    def transactions(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/wallet/stellar/eoa/transactions', body or {}, True)


class OmnichainWalletStellarEoaOperations:
    def __init__(self, client: "Client"):
        self._client = client

    def create_trustline(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/wallet/stellar/eoa/operations/create-trustline', body or {}, True)

    def estimate_gas(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/wallet/stellar/eoa/operations/estimate-gas', body or {}, True)


class OmnichainWalletStellarEoaTransfer:
    def __init__(self, client: "Client"):
        self._client = client

    def native_token(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/wallet/stellar/eoa/transfer/native-token', body or {}, True)

    def stablecoin(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'omnichain/wallet/stellar/eoa/transfer/stablecoin', body or {}, True)


class Simulation:
    def __init__(self, client: "Client"):
        self._client = client
        self.card = SimulationCard(client)
        self.collection = SimulationCollection(client)
        self.direct_debit = SimulationDirectDebit(client)
        self.transfer = SimulationTransfer(client)


class SimulationCard:
    def __init__(self, client: "Client"):
        self._client = client

    def spend(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'simulation/card/spend', body or {}, True)


class SimulationCollection:
    def __init__(self, client: "Client"):
        self._client = client

    def initiated_order(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'simulation/collection/initiated-order', body or {}, True)

    def static_virtual_account(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'simulation/collection/static-virtual-account', body or {}, True)

    def static_wallet_address(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'simulation/collection/static-wallet-address', body or {}, True)


class SimulationDirectDebit:
    def __init__(self, client: "Client"):
        self._client = client

    def status(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'simulation/direct-debit/status', body or {}, True)


class SimulationTransfer:
    def __init__(self, client: "Client"):
        self._client = client

    def initiated_order(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'simulation/transfer/initiated-order', body or {}, True)


class User:
    def __init__(self, client: "Client"):
        self._client = client
        self.account = UserAccount(client)
        self.misc = UserMisc(client)
        self.subscription = UserSubscription(client)
        self.verification = UserVerification(client)


class UserAccount:
    def __init__(self, client: "Client"):
        self._client = client
        self.business = UserAccountBusiness(client)
        self.individual = UserAccountIndividual(client)


class UserAccountBusiness:
    def __init__(self, client: "Client"):
        self._client = client

    def create(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'user/account/business/create', body or {}, True)

    def details(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'user/account/business/details', body or {}, True)

    def update(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'user/account/business/update', body or {}, True)


class UserAccountIndividual:
    def __init__(self, client: "Client"):
        self._client = client

    def create(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'user/account/individual/create', body or {}, True)

    def details(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'user/account/individual/details', body or {}, True)

    def update(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'user/account/individual/update', body or {}, True)


class UserMisc:
    def __init__(self, client: "Client"):
        self._client = client

    def business_industry_list(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'user/misc/business-industry-list', body or {}, True)

    def business_product_service_type(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('GET', 'user/misc/business-product-service-type', body or {}, False)

    def business_registration_type(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'user/misc/business-registration-type', body or {}, True)

    def business_trade_type(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'user/misc/business-trade-type', body or {}, True)

    def countries(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'user/misc/countries', body or {}, True)

    def job_types(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'user/misc/job-types', body or {}, True)

    def source_of_funds_type(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('GET', 'user/misc/source-of-funds-type', body or {}, False)


class UserSubscription:
    def __init__(self, client: "Client"):
        self._client = client

    def class_(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'user/subscription/class', body or {}, True)

    def initiate(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'user/subscription/initiate', body or {}, True)

    def products(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'user/subscription/products', body or {}, True)

    def requery(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'user/subscription/requery', body or {}, True)

    def status(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'user/subscription/status', body or {}, True)

    def transactions(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'user/subscription/transactions', body or {}, True)


class UserVerification:
    def __init__(self, client: "Client"):
        self._client = client

    def bulk_process(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'user/verification/bulk-process', body or {}, True)

    def requirement(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'user/verification/requirement', body or {}, True)

    def single_process(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'user/verification/single-process', body or {}, True)


class Verification:
    def __init__(self, client: "Client"):
        self._client = client

    def lookup(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'verification/lookup', body or {}, True)


class Wallet:
    def __init__(self, client: "Client"):
        self._client = client
        self.channel = WalletChannel(client)
        self.collection = WalletCollection(client)
        self.exchange = WalletExchange(client)
        self.mpwt = WalletMpwt(client)
        self.transfer = WalletTransfer(client)

    def create(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/create', body or {}, True)

    def details(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/details', body or {}, True)

    def transactions(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/transactions', body or {}, True)

    def update(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/update', body or {}, True)


class WalletChannel:
    def __init__(self, client: "Client"):
        self._client = client
        self.transfer_recipient = WalletChannelTransferRecipient(client)
        self.virtual_account = WalletChannelVirtualAccount(client)
        self.wallet_address = WalletChannelWalletAddress(client)


class WalletChannelTransferRecipient:
    def __init__(self, client: "Client"):
        self._client = client
        self.bank = WalletChannelTransferRecipientBank(client)
        self.mobile_money = WalletChannelTransferRecipientMobileMoney(client)
        self.wallet_address = WalletChannelTransferRecipientWalletAddress(client)


class WalletChannelTransferRecipientBank:
    def __init__(self, client: "Client"):
        self._client = client

    def add(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/channel/transfer-recipient/bank/add', body or {}, True)

    def countries(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/channel/transfer-recipient/bank/countries', body or {}, True)

    def details(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/channel/transfer-recipient/bank/details', body or {}, True)

    def institutions(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/channel/transfer-recipient/bank/institutions', body or {}, True)

    def requirements(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/channel/transfer-recipient/bank/requirements', body or {}, True)

    def resolve(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/channel/transfer-recipient/bank/resolve', body or {}, True)

    def sample_account(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/channel/transfer-recipient/bank/sample-account', body or {}, True)

    def supported_currencies(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/channel/transfer-recipient/bank/supported-currencies', body or {}, True)

    def supported_route_type(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/channel/transfer-recipient/bank/supported-route-type', body or {}, True)


class WalletChannelTransferRecipientMobileMoney:
    def __init__(self, client: "Client"):
        self._client = client

    def add(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/channel/transfer-recipient/mobile-money/add', body or {}, True)

    def details(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/channel/transfer-recipient/mobile-money/details', body or {}, True)

    def sample_account(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/channel/transfer-recipient/mobile-money/sample-account', body or {}, True)

    def supported_countries(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/channel/transfer-recipient/mobile-money/supported-countries', body or {}, True)

    def supported_currencies(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/channel/transfer-recipient/mobile-money/supported-currencies', body or {}, True)

    def supported_networks(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/channel/transfer-recipient/mobile-money/supported-networks', body or {}, True)


class WalletChannelTransferRecipientWalletAddress:
    def __init__(self, client: "Client"):
        self._client = client

    def add(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/channel/transfer-recipient/wallet-address/add', body or {}, True)

    def details(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/channel/transfer-recipient/wallet-address/details', body or {}, True)


class WalletChannelVirtualAccount:
    def __init__(self, client: "Client"):
        self._client = client

    def details(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/channel/virtual-account/details', body or {}, True)

    def generate(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/channel/virtual-account/generate', body or {}, True)

    def resubscribe(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/channel/virtual-account/resubscribe', body or {}, True)

    def supported_currencies(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/channel/virtual-account/supported-currencies', body or {}, True)

    def supported_institutions(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/channel/virtual-account/supported-institutions', body or {}, True)


class WalletChannelWalletAddress:
    def __init__(self, client: "Client"):
        self._client = client

    def details(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/channel/wallet-address/details', body or {}, True)

    def generate(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/channel/wallet-address/generate', body or {}, True)

    def supported_tokens(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/channel/wallet-address/supported-tokens', body or {}, True)


class WalletCollection:
    def __init__(self, client: "Client"):
        self._client = client
        self.method = WalletCollectionMethod(client)

    def calculator(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/collection/calculator', body or {}, True)

    def design_options(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/collection/design-options', body or {}, True)

    def info(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/collection/info', body or {}, True)

    def initiate(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/collection/initiate', body or {}, True)

    def supported_methods(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/collection/supported-methods', body or {}, True)


class WalletCollectionMethod:
    def __init__(self, client: "Client"):
        self._client = client

    def authorize_3ds(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/collection/method/authorize-3ds', body or {}, True)

    def authorize_otp(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/collection/method/authorize-otp', body or {}, True)

    def charge(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/collection/method/charge', body or {}, True)

    def confirmation(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/collection/method/confirmation', body or {}, True)

    def create(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/collection/method/create', body or {}, True)

    def details(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/collection/method/details', body or {}, True)

    def link(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/collection/method/link', body or {}, True)

    def resend_otp(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/collection/method/resend-otp', body or {}, True)

    def supported_countries(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/collection/method/supported-countries', body or {}, True)

    def supported_currencies(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/collection/method/supported-currencies', body or {}, True)

    def supported_institutions(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/collection/method/supported-institutions', body or {}, True)

    def supported_networks(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/collection/method/supported-networks', body or {}, True)

    def terminate(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/collection/method/terminate', body or {}, True)


class WalletExchange:
    def __init__(self, client: "Client"):
        self._client = client
        self.cryptotocrypto = WalletExchangeCryptotocrypto(client)
        self.cryptotofiat = WalletExchangeCryptotofiat(client)
        self.fiattocrypto = WalletExchangeFiattocrypto(client)
        self.fiattofiat = WalletExchangeFiattofiat(client)


class WalletExchangeCryptotocrypto:
    def __init__(self, client: "Client"):
        self._client = client
        self.external = WalletExchangeCryptotocryptoExternal(client)


class WalletExchangeCryptotocryptoExternal:
    def __init__(self, client: "Client"):
        self._client = client
        self.bridge = WalletExchangeCryptotocryptoExternalBridge(client)
        self.swap = WalletExchangeCryptotocryptoExternalSwap(client)


class WalletExchangeCryptotocryptoExternalBridge:
    def __init__(self, client: "Client"):
        self._client = client
        self.usdc = WalletExchangeCryptotocryptoExternalBridgeUsdc(client)


class WalletExchangeCryptotocryptoExternalBridgeUsdc:
    def __init__(self, client: "Client"):
        self._client = client

    def fees(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/exchange/cryptotocrypto/external/bridge/usdc/fees', body or {}, True)

    def initiate(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/exchange/cryptotocrypto/external/bridge/usdc/initiate', body or {}, True)

    def status(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/exchange/cryptotocrypto/external/bridge/usdc/status', body or {}, True)

    def supported_chains(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/exchange/cryptotocrypto/external/bridge/usdc/supported-chains', body or {}, True)


class WalletExchangeCryptotocryptoExternalSwap:
    def __init__(self, client: "Client"):
        self._client = client

    def fees(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/exchange/cryptotocrypto/external/swap/fees', body or {}, True)

    def initiate(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/exchange/cryptotocrypto/external/swap/initiate', body or {}, True)

    def status(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/exchange/cryptotocrypto/external/swap/status', body or {}, True)

    def supported_pairs(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/exchange/cryptotocrypto/external/swap/supported-pairs', body or {}, True)


class WalletExchangeCryptotofiat:
    def __init__(self, client: "Client"):
        self._client = client
        self.external = WalletExchangeCryptotofiatExternal(client)


class WalletExchangeCryptotofiatExternal:
    def __init__(self, client: "Client"):
        self._client = client

    def fees(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/exchange/cryptotofiat/external/fees', body or {}, True)

    def initiate(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/exchange/cryptotofiat/external/initiate', body or {}, True)

    def supported_pairs(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/exchange/cryptotofiat/external/supported-pairs', body or {}, True)


class WalletExchangeFiattocrypto:
    def __init__(self, client: "Client"):
        self._client = client
        self.wallet = WalletExchangeFiattocryptoWallet(client)


class WalletExchangeFiattocryptoWallet:
    def __init__(self, client: "Client"):
        self._client = client

    def fees(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/exchange/fiattocrypto/wallet/fees', body or {}, True)

    def initiate(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/exchange/fiattocrypto/wallet/initiate', body or {}, True)

    def supported_pairs(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/exchange/fiattocrypto/wallet/supported-pairs', body or {}, True)


class WalletExchangeFiattofiat:
    def __init__(self, client: "Client"):
        self._client = client
        self.wallet = WalletExchangeFiattofiatWallet(client)


class WalletExchangeFiattofiatWallet:
    def __init__(self, client: "Client"):
        self._client = client

    def fees(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/exchange/fiattofiat/wallet/fees', body or {}, True)

    def initiate(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/exchange/fiattofiat/wallet/initiate', body or {}, True)

    def supported_pairs(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/exchange/fiattofiat/wallet/supported-pairs', body or {}, True)


class WalletMpwt:
    def __init__(self, client: "Client"):
        self._client = client

    def balance(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/mpwt/balance', body or {}, True)

    def fees(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/mpwt/fees', body or {}, True)

    def fund(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/mpwt/fund', body or {}, True)


class WalletTransfer:
    def __init__(self, client: "Client"):
        self._client = client
        self.cross = WalletTransferCross(client)
        self.direct = WalletTransferDirect(client)


class WalletTransferCross:
    def __init__(self, client: "Client"):
        self._client = client

    def fees(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/transfer/cross/fees', body or {}, True)

    def single(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/transfer/cross/single', body or {}, True)

    def supported_routes(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/transfer/cross/supported-routes', body or {}, True)


class WalletTransferDirect:
    def __init__(self, client: "Client"):
        self._client = client

    def bulk(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/transfer/direct/bulk', body or {}, True)

    def fees(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/transfer/direct/fees', body or {}, True)

    def queue(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/transfer/direct/queue', body or {}, True)

    def single(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/transfer/direct/single', body or {}, True)

    def supported_currencies(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/transfer/direct/supported-currencies', body or {}, True)

    def supported_network(self, body: dict | None = None) -> dict[str, Any]:
        return self._client.request('POST', 'wallet/transfer/direct/supported-network', body or {}, True)
