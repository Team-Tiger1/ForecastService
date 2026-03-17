FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi \
    && rm -rf ~/.cache/pypoetry \
    && rm -rf /root/.cache/pypoetry \
    && rm -rf /root/.cache/pip \
    && find /usr/local -type d -name "__pycache__" -exec rm -rf {} +

COPY src/ ./src

EXPOSE 5000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "5000"]
