FROM python:3.12.5-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /usr/src/app

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get --no-install-recommends install -y \
    bash \
    curl \
    build-essential \
    libffi-dev \
    libssl-dev \
    python3-dev \
    libpq-dev \
    clang \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.lock ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.lock
