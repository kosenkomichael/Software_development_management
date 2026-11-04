FROM python:3.12-slim

WORKDIR /app

ENV PIP_INDEX_URL=https://pypi-mirror.gitverse.ru/simple/ \
    PIP_TRUSTED_HOST=pypi-mirror.gitverse.ru \
    PIP_DEFAULT_TIMEOUT=120 \
    PIP_RETRIES=10

RUN pip install --no-cache-dir 'poetry>=1.8,<2.0'

COPY pyproject.toml poetry.lock* ./

RUN poetry config virtualenvs.create false && \
    poetry install --no-root --only main

COPY . .

ENV PYTHONPATH=/app

RUN useradd -u 1000 -m appuser
USER 1000:1000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
