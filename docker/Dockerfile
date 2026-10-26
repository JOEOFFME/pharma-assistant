FROM python:3.11.17-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv==0.13.4
WORKDIR /app
COPY . .
RUN uv sync --frozen --no-dev
ENV PATH="/app/.venv/bin:$PATH" PYTHONHASHSEED=42 HOST=0.0.0.0
RUN useradd --create-home --uid 10001 pharma && chown -R pharma:pharma /app
USER pharma
EXPOSE 8000
CMD ["python", "scripts/start_service.py"]
