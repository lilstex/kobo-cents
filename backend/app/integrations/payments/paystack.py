import hashlib
import hmac

import httpx

from app.core.config import settings
from app.integrations.payments.base import CheckoutSession, ProviderNotConfiguredError, WebhookEvent

_BASE_URL = "https://api.paystack.co"


class PaystackAdapter:
    async def create_checkout(
        self, *, email: str, reference: str, amount: int, currency: str, callback_url: str
    ) -> CheckoutSession:
        if not settings.paystack_secret_key:
            raise ProviderNotConfiguredError("PAYSTACK_SECRET_KEY is not configured")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{_BASE_URL}/transaction/initialize",
                headers={"Authorization": f"Bearer {settings.paystack_secret_key}"},
                json={
                    "email": email,
                    # Paystack takes the smallest currency unit, kobo,
                    # not naira, the same 100x scale as cents.
                    "amount": amount * 100,
                    "currency": currency,
                    "reference": reference,
                    "callback_url": callback_url,
                },
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()["data"]

        return CheckoutSession(redirect_url=data["authorization_url"], reference=data["reference"])

    def verify_webhook_signature(self, raw_body: bytes, headers: dict) -> bool:
        """Per docs/backend-architecture/00.md: HMAC-SHA512 of the raw
        request body, keyed with the secret key, compared against the
        x-paystack-signature header. Skipping this is a real
        vulnerability, not a formality, anyone who finds the webhook
        URL could otherwise POST a fake "payment successful" event."""
        signature = headers.get("x-paystack-signature", "")
        expected = hmac.new(
            settings.paystack_secret_key.encode(), raw_body, hashlib.sha512
        ).hexdigest()
        return hmac.compare_digest(signature, expected)

    def parse_webhook_event(self, payload: dict) -> WebhookEvent:
        data = payload.get("data", {})
        event_type = payload.get("event", "")
        return WebhookEvent(
            event_id=str(data.get("id", "")),
            event_type=event_type,
            reference=data.get("reference", ""),
            status="successful" if event_type == "charge.success" else "other",
        )
