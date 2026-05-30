# Stage 1: Build dependencies
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-alpine
WORKDIR /sandbox
COPY --from=builder /root/.local /usr/local
RUN adduser -D sandbox
USER sandbox
WORKDIR /home/sandbox
COPY --chown=sandbox:sandbox sandbox_entrypoint.py .
ENTRYPOINT ["python", "/home/sandbox/sandbox_entrypoint.py"]
