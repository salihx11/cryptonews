FROM python:3.9-slim

WORKDIR /app

# Install minimal dependencies
RUN apt-get update && apt-get install -y \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Download Roboto font directly (most reliable)
RUN wget -O /usr/share/fonts/roboto-bold.ttf https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY . .

# Create directory for price history
RUN mkdir -p /app/data

# Run the bot
CMD ["python", "bot.py"]
