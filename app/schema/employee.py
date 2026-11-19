
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, EmailStr


# Data received when creating an employee
class EmployeeCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    employee_id: str = Field(min_length=1, max_length=50)
    email: EmailStr | None = None
    phone_number: str | None = Field(default=None, max_length=20)
    hourly_rate: Decimal | None = Field(default=None, ge=0)
    site_id: UUID

class EmployeeUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    email: EmailStr | None = None
    phone_number: str | None = Field(default=None, max_length=20)
    hourly_rate: Decimal | None = Field(default=None, ge=0)
    site_id: UUID | None = None


# Data received when changing employee status
class EmployeeStatusUpdate(BaseModel):
    status: str


# Data returned when retrieving employee information
class EmployeeResponse(BaseModel):
    id: UUID
    full_name: str
    employee_id: str | None
    email: EmailStr | None
    phone_number: str | None
    role: str
    status: str
    hourly_rate: Decimal | None
    site_id: UUID | None
    # created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# Data returned after importing employees
class EmployeeImportResponse(BaseModel):
    total: int
    successful: int
    failed: int
    message: str
