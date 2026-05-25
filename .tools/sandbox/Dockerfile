FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    flake8 \
    mypy \
    pytest

RUN useradd -m -s /bin/bash sandbox
USER sandbox
WORKDIR /home/sandbox/workspace

COPY --chown=sandbox:sandbox sandbox_entrypoint.py /home/sandbox/sandbox_entrypoint.py

ENTRYPOINT ["python", "/home/sandbox/sandbox_entrypoint.py"]
