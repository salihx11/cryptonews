FROM python:3.9-slim

WORKDIR /app

# Install system dependencies including fonts
RUN apt-get update && apt-get install -y \
    fonts-liberation \
    fonts-dejavu \
    fonts-freefont-ttf \
    fonts-roboto \
    fonts-noto \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Arial font (most compatible)
RUN wget -O /tmp/arial.ttf https://raw.githubusercontent.com/google/fonts/main/apache/roboto/Roboto-Bold.ttf \
    && mkdir -p /usr/share/fonts/truetype/custom \
    && cp /tmp/arial.ttf /usr/share/fonts/truetype/custom/ \
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
