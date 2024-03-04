# Use the Playwright image as the base
#FROM --platform=linux/amd64 mcr.microsoft.com/playwright:v1.40.0-jammy
FROM mcr.microsoft.com/playwright:v1.40.0-jammy

# Install Python 3, pip, and xvfb
RUN apt-get update && apt-get install -y python3 python3-pip

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ENV PYTHONUNBUFFERED=1

# Set HTML_PATH environment variable to point to the index.html in the current directory
ENV HTML_PATH=file:///usr/src/app/index.html?predefinedID=


# # Install tini to /tini and make it executable
# ENV TINI_VERSION v0.19.0
# ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
# RUN chmod +x /tini

# # Use tini as the init handler, followed by xvfb-run for your application
# ENTRYPOINT ["/tini", "--", "xvfb-run"]

# Specify the command to run your application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
