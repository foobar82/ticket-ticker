# Stretch goal (spec §5). Single-process, internal use.
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# Dev-grade server is fine for an internal prototype (spec §1). Swap in
# gunicorn ("gunicorn 'app:create_app()'") if this ever needs to scale.
CMD ["python", "run.py"]
