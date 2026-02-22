FROM python:3.12-slim

WORKDIR /app

RUN pip3 install --no-cache-dir \
    fastapi \
    uvicorn \
    httpx \
    arxiv \
    loguru \
    pydantic \
    pydantic-settings \
    python-dotenv \
    asyncpg \
    pgvector

COPY . .

EXPOSE 8000

CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
