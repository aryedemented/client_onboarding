FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/ScanRecepies

WORKDIR /ScanRecepies

# ✅ First: copy just the requirements (caches better)
COPY scan_text_recipes/requirements.txt .

# ✅ Install deps early (caches unless this file changes)
RUN pip install --upgrade pip && pip install -r requirements.txt

# ✅ THEN copy the rest of your source code
COPY . .

# Default command
CMD ["python", "scan_text_recipes/src/run_pipeline.py"]