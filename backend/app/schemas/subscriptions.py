from pydantic import BaseModel


class CheckoutRequest(BaseModel):
    provider: str  # "paystack" | "flutterwave"


class CheckoutResponse(BaseModel):
    redirect_url: str


class EntitlementResponse(BaseModel):
    entitled: bool
