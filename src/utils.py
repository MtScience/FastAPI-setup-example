from typing import Callable

from src.api.models import DepartmentResponse, DepartmentTreeResponse
from src.dto import DepartmentTreeDTO


def split_by[T](
    f: Callable[[T], bool], lst: list[T]
) -> tuple[list[T], list[T]]:
    left, right = [], []
    for elem in lst:
        if f(elem):
            left.append(elem)
        else:
            right.append(elem)

    return left, right


def build_tree(
    parent_dept: DepartmentTreeDTO, children: list[DepartmentTreeDTO]
) -> None:
    direct, indirect = split_by(
        lambda n: n.department.parent_id == parent_dept.department.id,
        children,
    )
    parent_dept.subdepartments.extend(direct)

    for child in parent_dept.subdepartments:
        build_tree(child, indirect)


def transform_tree(
    dtos: list[DepartmentTreeDTO],
) -> list[DepartmentTreeResponse]:
    return [
        DepartmentTreeResponse(
            department=DepartmentResponse(
                id=dto.department.id,
                name=dto.department.name,
                parent_id=dto.department.parent_id,
                created_at=dto.department.created_at,
            ),
            subdepartments=transform_tree(dto.subdepartments),
        )
        for dto in dtos
    ]
