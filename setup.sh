#!/bin/bash

# Update package list and install system dependencies
apt-get update
apt-get install -y tesseract-ocr libtesseract-dev poppler-utils

# Install Python requirements
pip install -r requirements.txt
