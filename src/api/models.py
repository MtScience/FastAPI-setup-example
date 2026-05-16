from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


class CreateDepartment(BaseModel):
    # Automatically trims whitespace
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str
    parent_id: int | None = Field(default=None)


class UpdateDepartment(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None)
    parent_id: int | None = Field(default=None)


class CreateEmployee(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str
    position: str
    hired_at: dt.date | None = Field(default=None)


class DepartmentResponse(BaseModel):
    # No need to trim strings here, because this is a response containing data
    # from DB, which has been trimmed upon creation
    id: int
    name: str
    parent_id: int | None = Field(default=None)
    created_at: dt.datetime


class DepartmentTreeResponse(BaseModel):
    department: DepartmentResponse
    subdepartments: list[DepartmentTreeResponse]


class EmployeeResponse(BaseModel):
    id: int
    department_id: int
    full_name: str
    position: str
    hired_at: dt.date | None = Field(default=None)
    created_at: dt.datetime


class DepartmentRetrievalResponse(BaseModel):
    department: DepartmentResponse
    children: list[DepartmentTreeResponse] = Field(default_factory=list)
    employees: list[EmployeeResponse] | None = Field(default=None)
