FROM python:3.11-slim

# Create a non-root user that Hugging Face Spaces expects (user 1000)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# Install dependencies
COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=user:user . .

# Expose a default port (Fly uses PORT env var, defaults to 8080)
EXPOSE 8080

# Run the server, binding to the PORT environment variable provided by Fly.io
CMD sh -c "uvicorn src.app:app --host 0.0.0.0 --port ${PORT:-8080}"
