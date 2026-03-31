FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY intermediate/requirements.txt ./requirements.txt
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY intermediate/. .

# Persist database on Fly volume
ENV DATABASE_PATH=/data/quiz_app.db
ENV PORT=8080

# Ensure data directory exists (Fly mount will overlay)
RUN mkdir -p /data

EXPOSE 8080

CMD ["gunicorn", "--workers", "1", "--threads", "4", "--bind", "0.0.0.0:8080", "app:app"]
