#!/bin/bash
# Local BUILD environment: the OCR/PDF system libraries below are only used by
# the ingestion path, which lives in requirements-dev.txt. Installing them
# alongside the lean production requirements.txt (no unstructured/pytesseract)
# left this script self-contradictory.
set -euo pipefail

# Update package list and install system dependencies
apt-get update
apt-get install -y tesseract-ocr libtesseract-dev poppler-utils

# Install Python requirements
pip install -r requirements-dev.txt
