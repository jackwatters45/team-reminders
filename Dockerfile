# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install uv
RUN pip install uv

# Set base work directory
WORKDIR /app_base

# Copy dependency definition files
COPY pyproject.toml ./ 
# Optional: Copy lock file if it exists for reproducible builds
# COPY uv.lock ./

# Install dependencies using uv
# Use --system to install in the global site-packages, common in containers
# Add --locked if uv.lock is used and copied above
RUN uv pip install --system --no-cache -p python3.11 . 

# Create app directory and set as work directory
RUN mkdir /app
WORKDIR /app

# Copy project source code from src directory in the build context
COPY ./src /app/

# Copy the database file (adjust if it's created elsewhere initially)
COPY database.db /app/database.db

# Expose port 8000 for the API
EXPOSE 8000

# Command to run the app will be in docker-compose.yml 