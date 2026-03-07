FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc

EXPOSE 8080

CMD ["gunicorn", "-c", "gunicorn.conf.py", "main:app"]
