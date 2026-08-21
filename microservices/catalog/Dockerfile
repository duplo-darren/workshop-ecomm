FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./catalog/

# Pre-load the seed product images into the served uploads directory so that
# every replica can serve the image paths written by `python -m catalog.seed`.
RUN mkdir -p /app/catalog/static/uploads \
    && cp -a /app/catalog/seed_images/. /app/catalog/static/uploads/

# Run as a non-root user; the uploads directory must stay writable for
# product image uploads.
RUN useradd --uid 1000 --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

EXPOSE 8001

CMD ["gunicorn", "--bind", "0.0.0.0:8001", "--workers", "2", "--access-logfile", "-", "catalog.app:create_app()"]
