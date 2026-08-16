import datetime as dt
from typing import Any, Literal

import sqlalchemy
from loguru import logger
from sqlalchemy import CTE, delete, insert, literal_column, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Department, Employee
from src.dto import DepartmentDTO, EmployeeDTO
from src.errors import NonexistentDepartmentError


def __create_department_subtree_ids_cte(id: int) -> CTE:
    dept_cte = (
        select(
            Department.id,
            Department.parent_id,
        )
        .where(Department.id == id)
        .cte(name="dept_cte", recursive=True)
    )
    dept_cte_alias = dept_cte.alias("dept_cte_alias")
    dept_cte = dept_cte.union_all(
        select(Department.id, Department.parent_id).join(
            dept_cte_alias, Department.parent_id == dept_cte_alias.c.id
        )
    )

    return dept_cte


async def __get_subdepartment_ids(
    session: AsyncSession,
    parent_id: int,
) -> list[int]:
    dept_cte = __create_department_subtree_ids_cte(parent_id)
    dept_ids_query = select(dept_cte.c.id)
    subdept_ids = (await session.scalars(dept_ids_query)).all()

    return [int(subdept_id) for subdept_id in subdept_ids]


async def create_department(
    session: AsyncSession,
    name: str,
    parent_id: int | None = None,
) -> DepartmentDTO:
    logger.info(
        f"Creating new database record for department with name='{name}', "
        f"parent_id={parent_id}"
    )
    query = (
        insert(Department)
        .values(name=name, parent_id=parent_id)
        .returning(Department)
    )

    new_department = await session.scalar(query)
    return new_department.to_dto()  # type: ignore[union-attr]


async def update_department(
    session: AsyncSession,
    id: int,
    name: str | None = None,
    parent_id: int | None = None,
) -> DepartmentDTO | None:
    logger.info(f"Updating database record for department with id={id}")

    values: dict[str, str | int] = {}
    if name:
        values["name"] = name
    if parent_id:
        values["parent_id"] = parent_id

    query = (
        update(Department)
        .values(**values)
        .where(Department.id == id)
        .returning(Department)
    )

    result = await session.scalar(query)
    return result.to_dto() if result else None


async def get_department(
    session: AsyncSession,
    id: int,
) -> DepartmentDTO | None:
    logger.info(f"Retrieving department with id={id}")
    query = select(Department).where(Department.id == id)
    dept = await session.scalar(query)

    return dept.to_dto() if dept else None


async def delete_department(
    session: AsyncSession,
    id: int,
    mode: Literal["cascade", "reassign"],
    reassign_to: int | None = None,
) -> None:
    logger.info(f"Deleting department with id={id}. Deletion mode: '{mode}'")

    queries: list[Any] = []
    if mode == "reassign":
        queries.extend(
            [
                update(Employee)
                .values(department_id=reassign_to)
                .where(Employee.department_id == id),
                update(Department)
                .values(parent_id=reassign_to)
                .where(Department.parent_id == id),
            ]
        )
    queries.append(delete(Department).where(Department.id == id))

    for query in queries:
        await session.execute(query)


async def get_subdepartments(
    session: AsyncSession,
    id: int,
    depth: int,
) -> list[DepartmentDTO]:
    logger.info(
        f"Retrieving subdepartments for department with id={id}. "
        f"Max depth={depth}"
    )
    depts_cte = (
        select(
            Department.id,
            Department.parent_id,
            literal_column("1").label("depth"),
        )
        .where(Department.parent_id == id)
        .cte(name="depts_cte", recursive=True)
    )
    depts_cte_alias = depts_cte.alias("depts_cte_alias")
    depts_cte = depts_cte.union_all(
        select(
            Department.id,
            Department.parent_id,
            (depts_cte_alias.c.depth + 1).label("depth"),
        ).join(depts_cte_alias, Department.parent_id == depts_cte_alias.c.id)
    )

    query = select(Department).where(
        Department.id.in_(
            select(depts_cte.c.id).where(depts_cte.c.depth <= depth)
        )
    )

    subdepartments = (await session.scalars(query)).all()
    return [subdept.to_dto() for subdept in subdepartments]


async def create_employee(
    session: AsyncSession,
    full_name: str,
    position: str,
    dept_id: int,
    hired_at: dt.date | None,
) -> EmployeeDTO:
    logger.info(
        f"Creating new database record for employee with name='{full_name}', "
        f" position='{position}'"
    )
    query = (
        insert(Employee)
        .values(
            full_name=full_name,
            position=position,
            hired_at=hired_at,
            department_id=dept_id,
        )
        .returning(Employee)
    )
    try:
        new_employee = await session.scalar(query)
        return new_employee.to_dto()  # type: ignore[union-attr]
    except sqlalchemy.exc.IntegrityError as exc:
        # Since the only way for this to happen is foreign key constraint
        # violation by trying to insert a value with nonexistent department ID,
        # we simply raise the appropriate error
        logger.error(f"Could not create employee: {exc}")
        raise NonexistentDepartmentError


async def get_employees(
    session: AsyncSession,
    dept_id: int,
) -> list[EmployeeDTO]:
    logger.info(f"Retrieving employees with id={dept_id}")
    query = (
        select(Employee)
        .where(Employee.department_id == dept_id)
        .order_by(Employee.full_name.asc())
    )
    result = (await session.scalars(query)).all()
    return [emp.to_dto() for emp in result]
