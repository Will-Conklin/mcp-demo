# Use Python 3.14 slim image for smaller size
FROM python:3.14-slim

# Set working directory
WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY src/ ./src/
COPY main.py ./

# Create directory for TinyDB data
RUN mkdir -p /data

# Set environment variable for database location
ENV TINYDB_PATH=/data/tinydb_data.json

# Run as non-root user for security
RUN useradd -m -u 1000 mcpuser && \
    chown -R mcpuser:mcpuser /app /data
USER mcpuser

# Expose stdio transport (MCP uses stdin/stdout, not network ports)
# No EXPOSE needed as MCP uses stdio transport

# Run the MCP server
CMD ["uv", "run", "python", "main.py"]
