# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend folder into the container at /app
COPY ./backend /app/backend

# Set the PYTHONPATH to include the app directory, so that 'backend' can be imported
ENV PYTHONPATH "${PYTHONPATH}:/app"

# Command to run the application will be specified in docker-compose 