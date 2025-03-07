# Use an official Python runtime as a base image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the application files
COPY main.py /app/
COPY requirements.txt /app/

# Install required dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the correct port
EXPOSE 8080  # Changed from 5000 to 8080

# Set the entry point to run the app
CMD ["python", "main.py"]
