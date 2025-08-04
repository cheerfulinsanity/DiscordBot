# Use a lightweight Python + Java base image
FROM python:3.10-slim

# Install Java, ffmpeg, and system tools
RUN apt-get update && apt-get install -y \
    openjdk-17-jre-headless \
    ffmpeg \
    unzip \
    curl \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy everything into the container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variable for Flask (optional)
ENV FLASK_APP=server.py

# Expose port 5000 if you're using a Flask web service
EXPOSE 5000

# Run the bot on container start
CMD ["python", "server.py"]

