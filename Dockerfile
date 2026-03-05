FROM python:3.12-slim
<<<<<<< HEAD

ENV PYTHONUNBUFFERED=1
=======
>>>>>>> 2199e9c1f5f61fc99eb47626b9746022efb58fda

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

COPY src/ ./src

EXPOSE 5000


CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "5000"]