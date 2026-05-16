from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field


@dataclass
class DepartmentDTO:
    id: int
    name: str
    created_at: dt.datetime
    parent_id: int | None = None


@dataclass
class EmployeeDTO:
    id: int
    department_id: int
    full_name: str
    position: str
    created_at: dt.datetime
    hired_at: dt.date | None = None


@dataclass
class DepartmentTreeDTO:
    department: DepartmentDTO
    subdepartments: list[DepartmentTreeDTO] = field(default_factory=list)


@dataclass
class DepartmentInfoDTO:
    department: DepartmentDTO | None
    subdepartments: list[DepartmentTreeDTO] = field(default_factory=list)
    employees: list[EmployeeDTO] | None = None
