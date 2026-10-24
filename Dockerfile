FROM python:3.12-slim

ENV PYTHONUTF8=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TODAY=2026-10-12

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY data ./data

RUN pip install --no-cache-dir -e .

CMD ["python", "-m", "libraryhub.main"]