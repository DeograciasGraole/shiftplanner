
from datetime import datetime, UTC, timedelta

from sqlalchemy import select, update, desc

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings

from app.models.user import User
from app.core.security import (generate_activated_code,hash_activated_code,verify_activated_code, create_access_token, hash_password, generate_refresh_token, hash_refresh_token,verify_password)
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.models.password_reset_code import PasswordResetCode
from app.schema.auth import TokenResponse
import secrets


async def verify_invitation(
    db: AsyncSession,
    employee_id: str,
    activation_code: str,
):
    result = await db.execute(
        select(User).where(User.employee_id == employee_id)
    )

    user = result.scalar_one_or_none()

    if user is None:
        return False

    if user.status != "invited":
        return False

    if user.activation_code_hash is None:
        return False

    if user.activation_expires_at is None:
        return False

    if user.activation_expires_at <= datetime.now(UTC):
        return False

    if not verify_activated_code(
        activation_code,
        user.activation_code_hash,
    ):
        return False

    return True





def create_and_store_refresh_token(
    db: AsyncSession,
    user: User,
) -> str:

    raw_token = generate_refresh_token()

    token_hash = hash_refresh_token(raw_token)

    expires_at = datetime.now(UTC) + timedelta(
        days=settings.refresh_token_expires_days
    )

    refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )

    db.add(refresh_token)

    return raw_token




async def activate_account(
    db: AsyncSession,
    employee_id: str,
    activation_code: str,
    password: str,
):
    try:
        result = await db.execute(
            select(User)
            .where(User.employee_id == employee_id)
            .with_for_update()
        )

        user = result.scalar_one_or_none()

        if user is None:
            await db.rollback()
            return None

        if user.status != "invited":
            await db.rollback()
            return None

        if user.activation_code_hash is None:
            await db.rollback()
            return None

        if user.activation_expires_at is None:
            await db.rollback()
            return None

        if user.activation_expires_at <= datetime.now(UTC):
            await db.rollback()
            return None

        if not verify_activated_code(
            activation_code,
            user.activation_code_hash,
        ):
            await db.rollback()
            return None

        # 1. Activate account
        user.password_hash = hash_password(password)
        user.status = "active"

        user.activation_code_hash = None
        user.activation_expires_at = None

        # 2. Generate access token
        access_token = create_access_token({
            "sub": str(user.id)
        })

        # 3. Generate and store refresh token
        refresh_token = create_and_store_refresh_token(
            db,
            user,
        )

        # 4. Commit everything together
        await db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    except Exception:
        await db.rollback()
        raise




async def refresh_access_token(
    db: AsyncSession,
    raw_token: str,
):
    token_hash = hash_refresh_token(raw_token)

    result = await db.execute(
        select(RefreshToken)
        .where(RefreshToken.token_hash == token_hash)
        .with_for_update()
    )

    stored_token = result.scalar_one_or_none()

    if stored_token is None:
        return None

    if stored_token.revoked_at is not None:
        return None

    if stored_token.expires_at <= datetime.now(UTC):
        return None

    # Revoke old refresh token
    stored_token.revoked_at = datetime.now(UTC)

    # Get associated user
    result = await db.execute(
        select(User).where(User.id == stored_token.user_id)
    )

    user = result.scalar_one_or_none()

    if user is None or user.status != "active":
        await db.rollback()
        return None

    # Generate new access token
    access_token = create_access_token({
        "sub": str(user.id)
    })

    # Generate new refresh token
    new_refresh_token = create_and_store_refresh_token(
        db,
        user,
    )

    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }

async def login(
    db: AsyncSession,
    identifier: str,
    password: str,
):
    identifier = identifier.strip()

    # Determine whether identifier is an email or employee ID
    if "@" in identifier:
        condition = User.email == identifier.lower()
    else:
        condition = User.employee_id == identifier

    # Find user
    result = await db.execute(
        select(User).where(condition)
    )

    user = result.scalar_one_or_none()

    # Check if user exists
    if user is None:
        return None

    # Check account status
    if user.status != "active":
        return None

    # Check password hash
    if user.password_hash is None:
        return None

    # Verify password
    if not verify_password(password, user.password_hash):
        return None

    # Generate access token
    access_token = create_access_token({
        "sub": str(user.id)
    })

    # Generate and store refresh token
    refresh_token = create_and_store_refresh_token(
        db,
        user,
    )

    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


async def logout(
    db: AsyncSession,
    raw_token: str,
):
    token_hash = hash_refresh_token(raw_token)

    result = await db.execute(
        select(RefreshToken)
        .where(RefreshToken.token_hash == token_hash)
        .with_for_update()
    )

    stored_token = result.scalar_one_or_none()

    if stored_token is None:
        return False

    if stored_token.revoked_at is not None:
        return False

    stored_token.revoked_at = datetime.now(UTC)

    await db.commit()

    return True



async def forgot_password(
    db: AsyncSession,
    email: str,
):
    email = email.strip().lower()

    result = await db.execute(
        select(User).where(
            User.email == email,
            User.status == "active",
        )
    )

    user = result.scalar_one_or_none()

    if user is None:
        return None

    now = datetime.now(UTC)

    # Invalidate previous unused reset requests
    await db.execute(
        update(PasswordResetCode)
        .where(
            PasswordResetCode.user_id == user.id,
            PasswordResetCode.used_at.is_(None),
        )
        .values(used_at=now)
    )

    # Generate and hash the code
    code = generate_activated_code()
    code_hash = hash_activated_code(code)

    reset_code = PasswordResetCode(
        user_id=user.id,
        code_hash=code_hash,
        expires_at=now + timedelta(minutes=10),
    )

    db.add(reset_code)

    await db.commit()

    return {
        "email": user.email,
        "code": code,
    }




async def verify_reset_code(
    db: AsyncSession,
    email: str,
    code: str,
):
    email = email.strip().lower()
    now = datetime.now(UTC)

    try:
        # 1. Find active user
        result = await db.execute(
            select(User).where(
                User.email == email,
                User.status == "active",
            )
        )

        user = result.scalar_one_or_none()

        if user is None:
            return None

        # 2. Get latest unused reset code and lock it
        result = await db.execute(
            select(PasswordResetCode)
            .where(
                PasswordResetCode.user_id == user.id,
                PasswordResetCode.used_at.is_(None),
                PasswordResetCode.reset_token_hash.is_(None),
            )
            .order_by(desc(PasswordResetCode.created_at))
            .limit(1)
            .with_for_update()
        )

        reset_record = result.scalar_one_or_none()

        if reset_record is None:
            return None

        # 3. Check expiration
        if reset_record.expires_at <= now:
            return None

        # 4. Check maximum attempts
        if reset_record.attempts >= 5:
            return None

        # 5. Verify OTP
        if not verify_activated_code(
            code,
            reset_record.code_hash,
        ):
            reset_record.attempts += 1

            # Invalidate code after 5 failed attempts
            if reset_record.attempts >= 5:
                reset_record.used_at = now

            await db.commit()
            return None

        # 6. Generate reset token
        reset_token = secrets.token_urlsafe(32)

        reset_record.reset_token_hash = hash_refresh_token(
            reset_token
        )

        reset_record.reset_token_expires_at = (
            now + timedelta(minutes=10)
        )

        # 7. Save changes
        await db.commit()

        # 8. Return raw token to Flutter
        return reset_token

    except Exception:
        await db.rollback()
        raise




async def reset_password(
    db: AsyncSession,
    reset_token: str,
    new_password: str,
):
    now = datetime.now(UTC)

    try:
        # 1. Hash the received reset token
        token_hash = hash_refresh_token(reset_token)

        # 2. Find the reset request and lock it
        result = await db.execute(
            select(PasswordResetCode)
            .where(
                PasswordResetCode.reset_token_hash == token_hash,
                PasswordResetCode.used_at.is_(None),
                PasswordResetCode.reset_token_expires_at > now,
            )
            .with_for_update()
        )

        reset_record = result.scalar_one_or_none()

        if reset_record is None:
            return False

        # 3. Get associated user
        result = await db.execute(
            select(User).where(
                User.id == reset_record.user_id,
                User.status == "active",
            )
        )

        user = result.scalar_one_or_none()

        if user is None:
            await db.rollback()
            return False

        # 4. Update password
        user.password_hash = hash_password(new_password)

        # 5. Mark reset request as used
        reset_record.used_at = now

        # 6. Revoke all active refresh tokens
        await db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user.id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )

        # 7. Commit everything together
        await db.commit()

        return True

    except Exception:
        await db.rollback()
        raise

