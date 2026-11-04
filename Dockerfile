FROM thehale/python-poetry:1.8.3-py3.12-slim

WORKDIR /app

COPY pyproject.toml poetry.lock* ./

RUN poetry config virtualenvs.create false && \
    poetry install --no-root --only main

COPY . .

ENV PYTHONPATH=/app

RUN useradd -u 1000 -m --no-log-init appuser
USER 1000:1000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
