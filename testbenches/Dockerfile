FROM python:3.11-slim

RUN apt-get update && apt-get install -y stress-ng fio && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy your folders into the container
COPY ./core /app/core
COPY ./testbenches /app/testbenches

# Run the script
CMD ["python3", "/app/core/main.py"]