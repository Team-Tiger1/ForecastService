FROM python:3.9-slim

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

COPY src/ ./src

EXPOSE 5000

CMD ["uvicorn", "src.forecast.main:app", "--host", "0.0.0.0", "--port", "5000"]