Playwright API for Automated Browser Interaction.

1. Download Python

2. Create a virtual enviornment

python3 -m venv venv

 . venv/bin/activate

3. Install requirements.txt

pip install -r requirements.txt

4. Install Playwright

playwright install

4. Run the API:
uvicorn main:app

Resources:

Research Papers:
https://github.com/OSU-NLP-Group/SeeAct


Deploy Dockerfile:

docker build -t workman_api .

docker run --rm \
-e DISPLAY=host.docker.internal:0 \
-v /tmp/.X11-unix:/tmp/.X11-unix \
-p 8000:8000 \
workman_api


Generate Requirements

pigar generate
