import uuid

from datetime import datetime,timedelta,UTC
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


from app.models.user import User

from app.schema.employee import EmployeeCreate
from app.core.security import (
    generate_activated_code,
    hash_activated_code,
)


async def create_employee(
    db: AsyncSession,
    employee_data: EmployeeCreate,
    # current_user: User,
):
    # STEP 1: Check employee ID
    result = await db.execute(
        select(User).where(
            User.employee_id == employee_data.employee_id
        )
    )
    existing_employee = result.scalar_one_or_none()

    if existing_employee:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee ID already exists.",
        )

    # STEP 2: Check email if provided
    if employee_data.email:
        result = await db.execute(
            select(User).where(
                User.email == str(employee_data.email)
            )
        )
        existing_email = result.scalar_one_or_none()

        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists.",
            )

    # STEP 3: Check phone if provided
    if employee_data.phone_number:
        result = await db.execute(
            select(User).where(
                User.phone_number == employee_data.phone_number
            )
        )
        existing_phone = result.scalar_one_or_none()

        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Phone number already exists.",
            )

    # STEP 4: Check manager site permission
    # if (
    #     current_user.role == "manager"
    #     and current_user.site_id != employee_data.site_id
    # ):
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="You cannot create employees outside your site.",
    #     )

    # STEP 5: Generate activation code
    activation_code = generate_activated_code()
    activation_code_hash = hash_activated_code(activation_code)

    # STEP 6: Create employee
    new_employee = User(
        id=uuid.uuid4(),
        full_name=employee_data.full_name,
        employee_id=employee_data.employee_id,
        email=str(employee_data.email) if employee_data.email else None,
        phone_number=employee_data.phone_number,
        hourly_rate=employee_data.hourly_rate,
        site_id=employee_data.site_id,
        role="manager",
        status="invited",
        password_hash=None,
        activation_code_hash=activation_code_hash,
        activation_expires_at=datetime.now(UTC) + timedelta(hours=48),
    )

    # STEP 7: Save employee
    try:
        db.add(new_employee)
        await db.commit()
        await db.refresh(new_employee)

    except Exception:
        await db.rollback()
        raise

    # STEP 8: Return employee and activation code
    return new_employee, activation_code


async def get_all_employees(
    db: AsyncSession,
    current_user: User,
):
    query = select(User).where(User.role == "employee")

    # A manager can only see employees from their own site
    # if current_user.role == "manager":
    #     query = query.where(User.site_id == current_user.site_id)

    result = await db.execute(query)

    employees = result.scalars().all()

    return employees


async def get_employee_by_employee_id(
    db: AsyncSession,
    employee_id: str,
    current_user: User,
):
    query = select(User).where(
        User.employee_id == employee_id,
        User.role == "employee",
    )

    if current_user.role == "manager":
        query = query.where(User.site_id == current_user.site_id)

    result = await db.execute(query)

    employee = result.scalar_one_or_none()

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    return employee

async def update_employee(
    db: AsyncSession,
    employee_id: str,
    employee_data: EmployeeUpdate,
    current_user: User,
):
    # 1. Find the employee
    query = select(User).where(
        User.employee_id == employee_id,
        User.role == "employee",
    )

    # 2. Restrict managers to their own site
    # if current_user.role == "manager":
    #     query = query.where(User.site_id == current_user.site_id)

    result = await db.execute(query)
    employee = result.scalar_one_or_none()

    # 3. Check if employee exists
    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found",
        )

    # 4. Get only the fields sent by the client
    update_data = employee_data.model_dump(exclude_unset=True)

    # 5. Update the employee fields
    for field, value in update_data.items():
        setattr(employee, field, value)

    # 6. Save changes to database
    await db.commit()
    await db.refresh(employee)

    return employee

async def regenerate_activation_code(
    db: AsyncSession,
    employee_id: str,
    current_user: User,
):
    # Find the employee
    query = select(User).where(
        User.employee_id == employee_id,
        User.role == "employee",
    )

    # Managers can only manage employees from their own site
    # if current_user.role == "manager":
    #     query = query.where(User.site_id == current_user.site_id)

    result = await db.execute(query)
    employee = result.scalar_one_or_none()

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found",
        )

    # Only invited employees need an activation code
    if employee.status != "invited":
        raise HTTPException(
            status_code=400,
            detail="Employee account is not awaiting activation",
        )

    # Generate a new code
    activation_code = generate_activated_code()

    employee.activation_code_hash = hash_activated_code(
        activation_code
    )

    employee.activation_expires_at = (
        datetime.now(UTC) + timedelta(hours=48)
    )

    await db.commit()
    await db.refresh(employee)

    return activation_code

async def set_employee_status(
    db: AsyncSession,
    employee_id: str,
    new_status: str,
    current_user: User,
):
    # Find the employee
    query = select(User).where(
        User.employee_id == employee_id,
        User.role == "employee",
    )

    # if current_user.role == "manager":
    #     query = query.where(User.site_id == current_user.site_id)

    result = await db.execute(query)
    employee = result.scalar_one_or_none()

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found",
        )

    # An invited employee must use the activation process
    if new_status == "active" and employee.password_hash is None:
        raise HTTPException(
            status_code=400,
            detail="Employee must activate their account first",
        )

    employee.status = new_status

    await db.commit()
    await db.refresh(employee)

    return employee
