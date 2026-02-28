# Skill image — <skill-name>
#
# Build:  docker build -t ghcr.io/8r4n/deerflow-skills/<skill-name>:latest .
# Run:    docker run --rm -p 8080:8080 ghcr.io/8r4n/deerflow-skills/<skill-name>:latest
#
# Replace <skill-name> with the actual skill name throughout.

FROM python:3.12-slim AS base

LABEL org.opencontainers.image.source="https://github.com/8r4n/deerflow-skills"
LABEL org.opencontainers.image.description="<skill-name> skill for DeerFlow"

WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"]

CMD ["python", "server.py"]
