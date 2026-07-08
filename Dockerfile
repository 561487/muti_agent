FROM python:3.11-slim

WORKDIR /app

# System dependencies for matplotlib and web scraping
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY contelix/ ./contelix/
COPY pyproject.toml .

# Install the package
RUN pip install -e .

# Output directory for reports
RUN mkdir -p /app/output

ENV CONTELIX_OUTPUT_DIR=/app/output

EXPOSE 8501

# Default: launch Streamlit UI
CMD ["streamlit", "run", "contelix/ui/streamlit_app.py", \
     "--server.address=0.0.0.0", "--server.port=8501"]
