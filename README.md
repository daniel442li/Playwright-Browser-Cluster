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



Postman Testing Link:
Download Postman (Desktop)

https://decluttr.postman.co/workspace/Team-Workspace~5338fec7-7789-48fd-80ac-339019885543/collection/11025870-1e85edb5-5586-482e-8aa0-47bf18dc7973?action=share&creator=11025870


Deploy Dockerfile:

docker build -t workman_api .

docker run --rm \
-e DISPLAY=host.docker.internal:0 \
-v /tmp/.X11-unix:/tmp/.X11-unix \
-p 8000:8000 \
workman_api


Generate Requirements

pigar generate
