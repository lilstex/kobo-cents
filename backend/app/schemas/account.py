from pydantic import BaseModel


class DeleteAccountRequest(BaseModel):
    # Requiring the current password, not just a valid session, is a
    # deliberate extra confirmation, per Sub-phase 10.4 of docs/
    # backend-architecture/03-phases.md: a hijacked session cookie
    # alone shouldn't be enough to permanently anonymize an account,
    # the same reasoning already applied to change-password.
    password: str
