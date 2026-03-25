FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Add azure-storage-blob for cloud storage integration
RUN pip install --no-cache-dir azure-storage-blob

COPY . .

# Run the pipeline script when the container starts
CMD ["python", "v2.py"]
