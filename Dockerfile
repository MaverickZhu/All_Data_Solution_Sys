# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for OpenCV, audio/video processing, and other libraries
RUN apt-get update && apt-get install -y \
    # OpenCV dependencies
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    # Audio processing dependencies
    libsndfile1 \
    ffmpeg \
    # General utilities
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY ./backend/requirements.txt /app/

# Install build dependencies first, then project dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install --no-cache-dir jieba -i https://pypi.tuna.tsinghua.edu.cn/simple

# Install NLTK data
# We create a specific directory and download data there to ensure consistency.
# This avoids potential issues with default NLTK search paths in different environments.
ENV NLTK_DATA /usr/local/share/nltk_data
RUN mkdir -p $NLTK_DATA && \
    python -m nltk.downloader -d $NLTK_DATA punkt stopwords vader_lexicon punkt_tab

# Create a non-root user and switch to it
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Copy the backend folder into the container at /app
COPY ./backend /app/backend

# Set the PYTHONPATH to include the app directory, so that 'backend' can be imported
ENV PYTHONPATH "${PYTHONPATH}:/app"

# Expose the port the app runs on
EXPOSE 8008

# Command to run the application will be specified in docker-compose 