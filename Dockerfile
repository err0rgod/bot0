FROM python:3.10-slim

WORKDIR /app

# Ensure tzdata is installed if timezone operations are needed, and keep the image small
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Run the bot
CMD ["python", "scraper/v2.py"]
