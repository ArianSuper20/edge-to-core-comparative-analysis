FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive
ARG TARGETPLATFORM
ARG TARGETARCH
ARG TARGETOS

RUN echo "Building for ${TARGETPLATFORM} (${TARGETARCH}) on ${TARGETOS}" \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        fio \
        sysbench \
        stress-ng \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ./core /app/core
COPY ./testbenches /app/testbenches

CMD ["python3", "/app/core/main.py"]