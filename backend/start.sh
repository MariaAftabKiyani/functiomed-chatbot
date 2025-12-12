#!/bin/bash
source /data/functiomed-chatbot/backend/venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 9000
