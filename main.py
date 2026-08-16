from fastapi import FastAPI

from src.api.router import router as departments_router

description = """
Пример реализации REST API с помощью FastAPI. Позволяет:
- создавать отделы;
- изменять отделы;
- удалять отделы (с возможностью каскадного удаления дочерних отделов и
  работников либо с переназначением их в другой
  отдел);
- получать информацию об отделе со списком его под-отделов и сотрудников;
- создавать сотрудников.

Отслеживается отсутствие циклов в дереве отделов.
"""
app = FastAPI(
    title="Departments API",
    description=description,
    version="0.1.0",
)


app.include_router(
    departments_router, prefix="/departments", tags=["Departments"]
)
