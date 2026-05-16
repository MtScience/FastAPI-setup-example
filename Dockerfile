FROM python:3.13.7

ENV PYTHONBEFFERED=1
ENV PYTHONWRITEBYTECODE=1
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
ENV PROJECTDIR="/code"
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /code

RUN curl -sSL https://install.python-poetry.org/ | python3 -
COPY pyproject.toml poetry.lock ./

RUN poetry install --without=dev --without=testing

COPY main.py alembic.ini ./
COPY ./alembic ./alembic
COPY ./src ./src

EXPOSE 8000

CMD ["/bin/bash", "-c", "poetry run alembic upgrade head && poetry run uvicorn main:app --port 8000 --host 0.0.0.0"]
