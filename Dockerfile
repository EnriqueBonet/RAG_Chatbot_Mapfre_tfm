FROM python:3.11-slim
 
# Set the working directory in the container
WORKDIR /app
 
# Copy the current directory contents into the container at /app
COPY . /app
 
# Install postgre pkg
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
 
# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
 
# Make port 8000 available to the world outside this container
EXPOSE 8000
 
# Define environment variable
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
 
# Run chainlit when the container launches
ENTRYPOINT ["python", "-m", "chainlit", "run", "app.py"]