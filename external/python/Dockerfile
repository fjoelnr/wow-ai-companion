FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir requests watchdog
COPY watcher.py ./watcher.py
COPY prompts ./prompts
ENV PYTHONUNBUFFERED=1
CMD ["python", "-u", "watcher.py"]
