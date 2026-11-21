
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.core.database import get_db
from app.core.security import require_role
from app.models.user import User
from app.schema.employee import EmployeeCreate, EmployeeResponse,EmployeeUpdate,EmployeeStatusUpdate
from app.services.employee_service import (create_employee, get_all_employees, get_employee_by_employee_id,update_employee,regenerate_activation_code,set_employee_status)
from fastapi import BackgroundTasks
from app.services.notification_service import (
    send_activation_notification,
)
router = APIRouter()


@router.post("/employees", status_code=status.HTTP_201_CREATED)
async def create_employee_endpoint(
    employee_data: EmployeeCreate,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
    # current_user: Annotated[
    #     User,
    #     Depends(require_role("super_admin", "manager"))
    # ],
):
    employee, activation_code = await create_employee(
        db=db,
        employee_data=employee_data,
        # current_user=current_user,
    )
    if employee.email:
        background_tasks.add_task(
            send_activation_notification,
            employee.email,
            activation_code,
        )


    return {
        "message": "Employee created successfully",
        "employee": EmployeeResponse.model_validate(employee),
        "activation_code": activation_code,
    }


# Get all employees
@router.get("/employees", response_model=list[EmployeeResponse])
async def get_all_employees_endpoint(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_role("super_admin", "manager"))
    ],
):
    employees = await get_all_employees(
        db=db,
        current_user=current_user,
    )

    return employees



# Get employee details
@router.get("/employees/{employee_id}")
async def get_employee(
    employee_id: str, 
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_role("super_admin", "manager"))
    ],
    ):
    employee = await get_employee_by_employee_id(db, employee_id)
    return {
         "message": "Employee retrieved successfully",
         "employee": EmployeeResponse.model_validate(employee),
    } 


# Update employee information
@router.patch("/employees/{employee_id}", response_model=EmployeeResponse)
async def update_employee_endpoint(
    employee_id: str,
    employee_data: EmployeeUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_role("super_admin", "manager"))
    ],
):
    employee = await update_employee(
        db=db,
        employee_id=employee_id,
        employee_data=employee_data,
        current_user=current_user,
    )

    return employee


# Regenerate activation code
@router.post("/employees/{employee_id}/activate-code")
async def regenerate_activation_code_endpoint(
    employee_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_role("super_admin", "manager"))
    ],
):
    activation_code = await regenerate_activation_code(
        db=db,
        employee_id=employee_id,
        current_user=current_user,
    )

    return {
        "message": "New activation code generated successfully",
        "activation_code": activation_code,
    }


@router.patch(
    "/employees/{employee_id}/status",
    response_model=EmployeeResponse,
)
async def update_employee_status_endpoint(
    employee_id: str,
    employee_data: EmployeeStatusUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_role("super_admin", "manager"))
    ],
):
    employee = await set_employee_status(
        db=db,
        employee_id=employee_id,
        new_status=employee_data.status,
        # current_user=current_user,
    )

    return employee


# Delete employee (if permitted by your retention policy)
# @router.delete("/employees/{employee_id}")
# async def delete_employee(employee_id: str):
#     return {"message": f"Employee {employee_id} deleted successfully"}

@router.post("/employees/import")
async def import_employees():
    return {"message": "Employees imported successfully"}
