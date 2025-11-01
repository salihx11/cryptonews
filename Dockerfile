FROM python:3.9-slim

WORKDIR /app

# Install system dependencies with correct package names
RUN apt-get update && apt-get install -y \
    fonts-liberation \
    fonts-dejavu \
    fonts-freefont-ttf \
    fonts-roboto \
    fonts-noto \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    fontconfig \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Download and install Arial-like font
RUN wget -O /tmp/roboto-bold.ttf https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf \
    && mkdir -p /usr/share/fonts/truetype/roboto \
    && cp /tmp/roboto-bold.ttf /usr/share/fonts/truetype/roboto/ \
    && fc-cache -f -v

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
