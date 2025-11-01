FROM python:3.9-slim

WORKDIR /app

# Install wget and create fonts directory
RUN apt-get update && apt-get install -y wget && \
    mkdir -p /usr/share/fonts/truetype/ && \
    rm -rf /var/lib/apt/lists/*

# Download Roboto font to correct directory
RUN wget -O /usr/share/fonts/truetype/roboto-bold.ttf https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY . .

# Run the bot
CMD ["python", "bot.py"]
