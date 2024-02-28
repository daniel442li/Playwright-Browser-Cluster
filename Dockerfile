# Use the Playwright image as the base
FROM --platform=linux/amd64 mcr.microsoft.com/playwright:v1.40.0-jammy

# Install Python 3 and pip
RUN apt-get update && apt-get install -y python3 python3-pip

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ENV PYTHONUNBUFFERED=1

# Set HTML_PATH environment variable to point to the index.html in the current directory
ENV HTML_PATH=file:///usr/src/app/index.html?predefinedID=

# Run app.py when the container launches
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]