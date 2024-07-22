FROM python:3.11-slim-buster as builder

# Create and set the working directory
WORKDIR /app

# Copy the requirements.txt file to the container
COPY requirements.txt .

# Install the project dependencies
RUN pip install -r requirements.txt

# Copy the entire project to the container's working directory
COPY . .

# Expose port 8000 (the port your FastAPI app is listening on)
EXPOSE 8000

# Run your existing command and then the Bash script
CMD ["sh", "-c", "python -m uvicorn main:app --host 0.0.0.0 --reload"]
