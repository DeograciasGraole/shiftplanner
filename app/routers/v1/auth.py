from fastapi import APIRouter,  BackgroundTasks,Depends, HTTPException, status


router = APIRouter()

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.core.database import get_db
from app.core.security import verify_activated_code,CurrentUser
from app.schema.auth import InvitationVerify
from app.services.auth_service import verify_invitation
from app.schema.auth import (InvitationVerify, AccountActivate,TokenResponse,RefreshTokenRequest,LogoutRequest,LoginRequest,AuthUserResponse,ForgotPasswordRequest, VerifyResetCodeRequest,ResetPasswordRequest)
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from app.services.auth_service import (verify_invitation, activate_account,refresh_access_token,logout,login,forgot_password,verify_reset_code,reset_password)
from app.services.notification_service import send_reset_code_notification
router = APIRouter()

@router.post("/verify-invitation")
async def verify_invitation_endpoint(
    invitation_data: InvitationVerify,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    is_valid = await verify_invitation(
        db=db,
        employee_id=invitation_data.employee_id,
        activation_code=invitation_data.activation_code,
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invitation.",
        )

    return {"message": "Invitation verified successfully."}
@router.post(
    "/activate",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
async def activate_account_endpoint(
    data: AccountActivate,
    db: AsyncSession = Depends(get_db),
):
    tokens = await activate_account(
        db=db,
        employee_id=data.employee_id,
        activation_code=data.activation_code,
        password=data.password,
    )

    if tokens is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invitation",
        )

    return tokens

@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login_endpoint(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    tokens = await login(
        db=db,
        identifier=data.identifier,
        password=data.password,
    )

    if tokens is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid identifier or password",
        )

    return tokens


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    tokens = await login(
        db=db,
        identifier=form_data.username,
        password=form_data.password,
    )

    if tokens is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid identifier or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return tokens
@router.post(
    "/refresh-token",
    response_model=TokenResponse,
)
async def refresh_token_endpoint(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    tokens = await refresh_access_token(
        db=db,
        raw_token=data.refresh_token,
    )

    if tokens is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    return tokens




@router.post("/forgot-password")
async def forgot_password_endpoint(
    data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    result = await forgot_password(
        db=db,
        email=data.email,
    )

    if result is not None:
        background_tasks.add_task(
            send_reset_code_notification,
            result["email"],
            result["code"],
        )
        
        
    return {
        "message": "If your account exists, a reset code has been sent to your email."}

@router.post("/verify-reset-code")
async def verify_reset_code_endpoint(
    data: VerifyResetCodeRequest,
    db: AsyncSession = Depends(get_db),
):
    reset_token = await verify_reset_code(
        db=db,
        email=data.email,
        code=data.code,
    )

    if reset_token is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code.",
        )

    return {
        "message": "Verification successful.",
        "reset_token": reset_token,
    }
@router.post("/reset-password")
async def reset_password_endpoint(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    success = await reset_password(
        db=db,
        reset_token=data.reset_token,
        new_password=data.new_password,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token.",
        )

    return {
        "message": "Password reset successfully."
    }


# DgUfTyDGRHdr-WKxQtyKeFjfuowhr6Z9cHZY0ebYXAA
    

@router.post("/logout")
async def logout_endpoint(
    data: LogoutRequest,
    db: AsyncSession = Depends(get_db),
):
    await logout(
        db=db,
        raw_token=data.refresh_token,
    )

    return {
        "message": "Successfully logged out"
    }
@router.get(
    "/me",
    response_model=AuthUserResponse,
)
async def get_me(
    current_user: CurrentUser,
):
    return current_user
# 7wQe8QyI2JbPaHJkMCmnuSMLzyI7g5MevggHKPHkhHw
# 20efORs-BVSwYWqDeyyO3IlSK5fNlolaPM1nVlVD6Cs