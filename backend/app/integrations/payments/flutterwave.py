import hmac

import httpx

from app.core.config import settings
from app.integrations.payments.base import CheckoutSession, ProviderNotConfiguredError, WebhookEvent

_BASE_URL = "https://api.flutterwave.com/v3"


class FlutterwaveAdapter:
    async def create_checkout(
        self, *, email: str, reference: str, amount: int, currency: str, callback_url: str
    ) -> CheckoutSession:
        if not settings.flutterwave_secret_key:
            raise ProviderNotConfiguredError("FLUTTERWAVE_SECRET_KEY is not configured")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{_BASE_URL}/payments",
                headers={"Authorization": f"Bearer {settings.flutterwave_secret_key}"},
                json={
                    "tx_ref": reference,
                    "amount": str(amount),
                    "currency": currency,
                    "redirect_url": callback_url,
                    "customer": {"email": email},
                },
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()["data"]

        return CheckoutSession(redirect_url=data["link"], reference=reference)

    def verify_webhook_signature(self, raw_body: bytes, headers: dict) -> bool:
        """Flutterwave doesn't HMAC-sign the payload the way Paystack
        does: a static secret hash, set once in their dashboard, is
        sent back verbatim on every webhook and compared directly. A
        real, explainable asymmetry between the two providers' webhook
        designs, not an inconsistency in this codebase."""
        received = headers.get("verif-hash", "")
        return hmac.compare_digest(received, settings.flutterwave_webhook_secret_hash)

    def parse_webhook_event(self, payload: dict) -> WebhookEvent:
        data = payload.get("data", {})
        return WebhookEvent(
            event_id=str(data.get("id", "")),
            event_type=payload.get("event", ""),
            reference=data.get("tx_ref", ""),
            status="successful" if data.get("status") == "successful" else "other",
        )
