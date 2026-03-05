FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir \
    "Django>=5.1,<5.2" \
    "psycopg[binary]>=3.2,<3.3" \
    "whitenoise>=6.6,<7" \
    "pytest>=8.3,<9" \
    "pytest-django>=4.11,<5"

COPY . .
