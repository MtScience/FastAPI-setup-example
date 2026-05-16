from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

import src.usecases.usecases as usecases
from src.api.models import (
    CreateDepartment,
    CreateEmployee,
    DepartmentResponse,
    DepartmentRetrievalResponse,
    DepartmentTreeResponse,
    EmployeeResponse,
    UpdateDepartment,
)
from src.api.queryparams import DeletionQueryParams
from src.db.base import get_async_session
from src.errors import (
    DepartmentLoop,
    NothingToUpdate,
)
from src.utils import transform_tree

router = APIRouter()


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
)
async def create_department(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    payload: CreateDepartment,
):
    """
    Создаёт и возвращает новый отдел
    """

    logger.info(
        f"Received department creation request. Name: '{payload.name}'; "
        f"parent department ID: {payload.parent_id}"
    )
    data = await usecases.create_department(
        session, name=payload.name, parent_id=payload.parent_id
    )
    return DepartmentResponse(
        id=data.id,
        name=data.name,
        parent_id=data.parent_id,
        created_at=data.created_at,
    )


@router.get(
    "/{id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Запрошенный отдел не найден"
        },
    },
)
async def get_department(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    id: int,
    depth: Annotated[int, Query(ge=1, le=5)] = 1,
    include_employees: bool = True,
):
    """
    Позволяет получить информацию об отделе
    """
    logger.info(
        f"Received department retrieval request. Subtree depth: {depth}; "
        f"include employees: {include_employees}"
    )
    dept_info = await usecases.get_department(
        session, id=id, depth=depth, include_employees=include_employees
    )
    if dept_info.department is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    dept_response = DepartmentResponse(
        id=dept_info.department.id,
        name=dept_info.department.name,
        parent_id=dept_info.department.parent_id,
        created_at=dept_info.department.created_at,
    )

    children_response: list[DepartmentTreeResponse] = []
    if dept_info.subdepartments:
        children_response.extend(transform_tree(dept_info.subdepartments))

    employees_response = None
    if dept_info.employees is not None:
        employees_response = [
            EmployeeResponse(
                id=employee.id,
                department_id=employee.department_id,
                full_name=employee.full_name,
                position=employee.position,
                hired_at=employee.hired_at,
                created_at=employee.created_at,
            )
            for employee in dept_info.employees
        ]

    return DepartmentRetrievalResponse(
        department=dept_response,
        employees=employees_response,
        children=children_response,
    )


@router.patch(
    "/{id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Отдел с указанным ID не найден. "
            "Невозможно обновить"
        },
        status.HTTP_409_CONFLICT: {
            "description": "Попытка обновления с указанными данными приведёт "
            "к образованию цикла подчинения"
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Данные для обновления пусты. Нечего обновлять"
        },
    },
)
async def update_department(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    id: int,
    payload: UpdateDepartment,
):
    """
    Обновляет информацию об отделе
    """
    logger.info(
        f"Received department update request. Department ID: {id}; "
        f"new name: '{payload.name}'; new parent ID: {payload.parent_id}"
    )
    try:
        data = await usecases.update_department(
            session, id=id, name=payload.name, parent_id=payload.parent_id
        )
        if data is None:
            return Response(status_code=status.HTTP_404_NOT_FOUND)
        return DepartmentResponse(
            id=data.id,
            name=data.name,
            parent_id=data.parent_id,
            created_at=data.created_at,
        )
    except NothingToUpdate:
        return Response(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT)
    except DepartmentLoop:
        return Response(status_code=status.HTTP_409_CONFLICT)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_409_CONFLICT: {
            "description": "Попытка удаления в указанном режиме приведёт "
            "к образованию цикла подчинения"
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Указанный режим удаления не поддерживается"
        },
    },
)
async def delete_department(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    id: int,
    params: Annotated[DeletionQueryParams, Query()],
):
    """
    Удаляет отдел
    """
    logger.info(f"Received department deletion request. Department ID: {id}")
    try:
        await usecases.delete_department(
            session, id=id, mode=params.mode, reassign_to=params.reassign_id
        )
    except DepartmentLoop:
        return Response(status_code=status.HTTP_409_CONFLICT)
    except ValueError:
        return Response(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT)


@router.post(
    "/{id}/employees",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Отдел с указаыннм ID не найден. Невозможно "
            "создать сотрудника"
        }
    },
)
async def create_employee(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    id: int,
    payload: CreateEmployee,
):
    """
    Создаёт и возвращает нового работника
    """
    logger.info(
        f"Received employee creation request. Name: '{payload.full_name}'; "
        f"department ID: {id}; position: '{payload.position}'; "
        f"hire date: {payload.hired_at}"
    )
    data = await usecases.create_employee(
        session,
        full_name=payload.full_name,
        position=payload.position,
        hired_at=payload.hired_at,
        dept_id=id,
    )
    if data is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    return EmployeeResponse(
        id=data.id,
        department_id=data.department_id,
        full_name=data.full_name,
        position=data.position,
        hired_at=data.hired_at,
        created_at=data.created_at,
    )
