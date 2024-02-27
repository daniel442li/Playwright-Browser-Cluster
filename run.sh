#!/bin/bash

# Get the current directory
CURRENT_DIR=$(pwd)

# Set the HTML_PATH environment variable
export HTML_PATH="file://$CURRENT_DIR/index.html?predefinedID="

# Run your application
# Example: if you're using Python
uvicorn main:app --host 0.0.0.0 --port 8000