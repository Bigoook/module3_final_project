#FROM python:3.12-slim
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

#COPY requirements.txt .
#RUN pip install --no-cache-dir --user -r requirements.txt

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync

COPY . .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]