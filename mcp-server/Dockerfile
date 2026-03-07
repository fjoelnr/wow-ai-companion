FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir fastapi uvicorn[standard] httpx websockets
COPY llm/ llm/
COPY analysis/ analysis/
COPY server.py .
EXPOSE 9090
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "9090"]
