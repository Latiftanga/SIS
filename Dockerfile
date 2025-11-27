FROM python:3.12-slim
LABEL maintainer="ttek.com"

ENV PYTHONUNBUFFERED=1

COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
COPY . /app

WORKDIR /app
EXPOSE 8000

ARG DEV=false

# Install system dependencies and Weasyprint runtime libraries
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
        fontconfig \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libpangocairo-1.0-0 \
        libgdk-pixbuf-2.0-0 \
        libffi-dev \
        shared-mime-info \
        libcairo2 \
        libglib2.0-0 \
        libjpeg62-turbo \
        libopenjp2-7 \
        libtiff6 \
        libwebp7 && \
    rm -rf /var/lib/apt/lists/*

# Create virtual environment and install Python packages
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /tmp/requirements.txt

# Install dev dependencies if needed
RUN if [ "$DEV" = "true" ]; then \
        /py/bin/pip install -r /tmp/requirements.dev.txt; \
    fi

# Pre-generate fontconfig cache to avoid runtime warnings
RUN fc-cache -fv

# Cleanup build dependencies to reduce image size
# Note: Keep Weasyprint runtime dependencies (libpango, libgdk-pixbuf, etc.)
RUN apt-get purge -y --auto-remove \
        build-essential && \
    rm -rf /var/lib/apt/lists/*

# Create user and fontconfig cache directory
RUN adduser \
        --disabled-password \
        --no-create-home \
        ttek_user && \
    mkdir -p /var/cache/fontconfig && \
    chown -R ttek_user:ttek_user /var/cache/fontconfig

ENV PATH="/py/bin:$PATH"
ENV XDG_CACHE_HOME="/var/cache/fontconfig"
USER ttek_user