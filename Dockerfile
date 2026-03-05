FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Security: Create non-root user
RUN groupadd -r csc && useradd -r -g csc -d /app -s /sbin/nologin csc

WORKDIR /app

# Install dependencies as root
COPY pyproject.toml ./
RUN pip install --no-cache-dir \
    "Django>=5.1,<5.2" \
    "psycopg[binary]>=3.2,<3.3" \
    "whitenoise>=6.6,<7" \
    "pytest>=8.3,<9" \
    "pytest-django>=4.11,<5" \
    "markdown>=3.5" \
    "django-csp>=3.8"

# Copy application code
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p /app/static /app/media /app/db && \
    chown -R csc:csc /app

# Switch to non-root user
USER csc

# Security: Don't run as root
EXPOSE 8000

CMD ["python", "src/manage.py", "runserver", "0.0.0.0:8000"]
