# syntax=docker/dockerfile:1
# Build an image starting with the Python 3.13 image
FROM python:3.13-alpine

# Default environment variables
ENV timezone=America/Toronto
ENV filename=./output.ics
ENV time=01:00

# Set the working directory to /app
WORKDIR /app

# Copy requirements and install them
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the cineplexwork package
COPY cineplexwork ./cineplexwork
CMD exec python -u -m cineplexwork ${filename} ${timezone} --repeat ${time}
