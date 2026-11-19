from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, EmailStr
class InvitationVerify(BaseModel):
    employee_id: str = Field(min_length=1, max_length=50)
    activation_code: str = Field(min_length=6, max_length=6)


class AccountActivate(BaseModel):
    employee_id: str = Field(min_length=1, max_length=50)
    activation_code: str = Field(min_length=6, max_length=6)
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    identifier: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class LogoutRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class VerifyResetCodeRequest(BaseModel):
    email: EmailStr
    code: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
    )


class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str = Field(min_length=8)


# =========================
# Current User
# =========================

class AuthUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    employee_id: str
    full_name: str
    email: EmailStr | None = None
    role: str
    status: str
    site_id: UUID | None = None
