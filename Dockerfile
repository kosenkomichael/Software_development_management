FROM getflow/python-poetry:stable-python3.12-slim

WORKDIR /app

ENV POETRY_HOME=/opt/poetry

ENV PIP_INDEX_URL=https://pypi-mirror.gitverse.ru/simple/ \
    PIP_TRUSTED_HOST=pypi-mirror.gitverse.ru \
    PIP_DEFAULT_TIMEOUT=120 \
    PIP_RETRIES=10

COPY pyproject.toml poetry.lock* ./

RUN $POETRY_HOME/bin/poetry config virtualenvs.create false && \
    $POETRY_HOME/bin/poetry install --no-root --only main

COPY . .

ENV PYTHONPATH=/app

RUN useradd -u 1000 -m --no-log-init appuser
USER 1000:1000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
