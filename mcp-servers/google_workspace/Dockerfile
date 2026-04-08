FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cloud Run injects PORT env var (default 8080)
ENV MCP_TRANSPORT=streamable-http
ENV TOKEN_BACKEND=firestore
ENV GCP_PROJECT=personal-ai-agent-492408
ENV PORT=8080

CMD ["python", "server.py"]
