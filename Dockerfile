FROM python:3.10-slim

# Environment settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory inside container
WORKDIR /ScanRecepies

# Copy the full project into the container
COPY . .

# Install requirements (from the src folder)
RUN pip install --upgrade pip && pip install -r scan_text_recipes/requirements.txt

# Set default command to run your pipeline
CMD ["python", "scan_text_recipes/src/run_pipeline.py"]
