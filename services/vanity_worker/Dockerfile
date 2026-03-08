# Build mkp224o
FROM debian:bookworm-slim as builder

RUN apt-get update && apt-get install -y \
    gcc \
    libc6-dev \
    libsodium-dev \
    make \
    autoconf \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
RUN git clone https://github.com/cathugger/mkp224o.git . && \
    ./autogen.sh && \
    ./configure && \
    make

# Final Runner Image
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies for psycopg2 and mkp224o
RUN apt-get update && apt-get install -y \
    libsodium23 \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /build/mkp224o /usr/local/bin/mkp224o

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create volume dir
RUN mkdir -p /tor_keys && \
    chown 100:100 /tor_keys

COPY worker.py .

CMD ["python", "-u", "worker.py"]
