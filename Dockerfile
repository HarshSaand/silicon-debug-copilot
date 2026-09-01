FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY app.py ./app.py
COPY config ./config
COPY data/runbooks ./data/runbooks
COPY data/sample ./data/sample
COPY evals ./evals

RUN python -m pip install --upgrade pip && python -m pip install .

EXPOSE 8000

CMD ["uvicorn", "silicon_debug.api:app", "--host", "0.0.0.0", "--port", "8000"]
