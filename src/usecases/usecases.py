import datetime as dt
from typing import Literal

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

import src.db.queries as queries
from src.dto import (
    DepartmentDTO,
    DepartmentInfoDTO,
    DepartmentTreeDTO,
    EmployeeDTO,
)
from src.errors import (
    DepartmentLoop,
    NonexistentDepartmentError,
    NothingToUpdate,
)
from src.utils import build_tree


async def create_department(
    session: AsyncSession,
    name: str,
    parent_id: int | None = None,
) -> DepartmentDTO:
    return await queries.create_department(session, name, parent_id)


async def get_department(
    session: AsyncSession,
    id: int,
    depth: int,
    include_employees: bool = True,
) -> DepartmentInfoDTO:
    dept = await queries.get_department(session, id)
    subdepts = []
    employees = None

    if dept is not None:
        subdepts_list = [
            DepartmentTreeDTO(department=d, subdepartments=[])
            for d in await queries.get_subdepartments(session, id, depth)
        ]

        parent = DepartmentTreeDTO(department=dept, subdepartments=[])
        build_tree(parent, subdepts_list)
        subdepts = parent.subdepartments

        if include_employees:
            employees = await queries.get_employees(session, id)
    else:
        logger.warning(f"Department with ID {id} not found")

    return DepartmentInfoDTO(
        department=dept,
        subdepartments=subdepts,
        employees=employees,
    )


async def update_department(
    session: AsyncSession,
    id: int,
    name: str | None = None,
    parent_id: int | None = None,
) -> DepartmentDTO | None:
    match (name, parent_id):
        case (None, None):
            logger.error("Could not update department: nothing to update")
            raise NothingToUpdate
        case (_, int()):
            subdept_ids = await queries.__get_subdepartment_ids(session, id)
            if parent_id in subdept_ids:
                logger.error(
                    "Could not update department: requested update would "
                    "result in a loop in department tree"
                )
                raise DepartmentLoop
    return await queries.update_department(session, id, name, parent_id)


async def delete_department(
    session: AsyncSession,
    id: int,
    mode: Literal["cascade", "reassign"],
    reassign_to: int | None = None,
) -> None:
    if mode not in ("cascade", "reassign"):
        logger.error("Could not delete department: invalid deletion mode")
        raise ValueError("Invalid mode")

    subdept_ids = await queries.__get_subdepartment_ids(session, id)
    if reassign_to in subdept_ids:
        logger.error(
            "Could not delete department: requested deletion would "
            "result in a loop in department tree"
        )
        raise DepartmentLoop

    return await queries.delete_department(session, id, mode, reassign_to)


async def create_employee(
    session: AsyncSession,
    full_name: str,
    position: str,
    dept_id: int,
    hired_at: dt.date | None,
) -> EmployeeDTO | None:
    try:
        return await queries.create_employee(
            session, full_name, position, dept_id, hired_at
        )
    except NonexistentDepartmentError:
        logger.error(
            "Could not create employee: department to assign the employee to "
            "does not exist"
        )
        raise


async def get_employees(
    session: AsyncSession,
    dept_id: int,
) -> list[EmployeeDTO]:
    return await queries.get_employees(session, dept_id)
