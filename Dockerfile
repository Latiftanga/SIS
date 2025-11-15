FROM python:3.12-slim
LABEL maintainer="ttek.com"

ENV PYTHONUNBUFFERED=1

COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
COPY . /app

WORKDIR /app
EXPOSE 8000

ARG DEV=false

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Create virtual environment and install Python packages
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /tmp/requirements.txt

# Install dev dependencies if needed
RUN if [ "$DEV" = "true" ]; then \
        /py/bin/pip install -r /tmp/requirements.dev.txt; \
    fi

# Cleanup build dependencies to reduce image size
RUN apt-get purge -y --auto-remove \
        build-essential \
        libpq-dev && \
    rm -rf /tmp /var/lib/apt/lists/*

# Create user
RUN adduser \
        --disabled-password \
        --no-create-home \
        ttek_user

ENV PATH="/py/bin:$PATH"
USER ttek_user