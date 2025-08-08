# PDF Text Extractor

A FastAPI-based application for extracting text from PDF files provided via URLs. The application uses a microservices architecture, with two main components: a text extraction service and an OCR service, deployed using Docker Swarm.

## Table of Contents
- [Overview](#overview)
- [Project Structure](#project-structure)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Setup and Installation](#setup-and-installation)
- [Running the Application](#running-the-application)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Deployment](#deployment)

## Overview
The PDF Text Extractor is designed to process PDF files from provided URLs and extract their text content using Optical Character Recognition (OCR). The application is split into two services:
- **text_extractor**: A FastAPI service that handles HTTP requests, downloads PDFs, and forwards them to the OCR service.
- **ocr_service**: A FastAPI service that processes PDFs using PaddleOCR to extract text, handling both single and multi-column layouts.

Both services are containerized and orchestrated using Docker Swarm for scalability and ease of deployment.

## Project Structure
```
pdf_text_extractor/
├── text_extractor/
│   ├── main.py              # FastAPI app for downloading PDFs and interacting with OCR service
│   ├── test_main.py        # Unit tests for text_extractor service
│   ├── Dockerfile          # Docker configuration for text_extractor
│   ├── requirements.txt     # Dependencies for text_extractor
├── ocr_service/
│   ├── main.py             # FastAPI app for OCR text extraction
│   ├── Dockerfile          # Docker configuration for ocr_service
│   ├── requirements.txt    # Dependencies for ocr_service
├── docker-compose.yml       # Docker Compose configuration for both services (used with Swarm)
└── README.md               # Project documentation
```

## Features
- **PDF Download**: Fetches PDFs from provided URLs with proper headers for services like arXiv.
- **OCR Processing**: Uses PaddleOCR for text detection and recognition, supporting multi-column layouts via KMeans clustering.
- **Microservices Architecture**: Separates text extraction and OCR processing for scalability.
- **Dockerized Deployment**: Runs both services in containers with Docker Swarm.
- **Error Handling**: Robust error handling for network issues, invalid PDFs, and OCR failures.
- **Testing**: Includes unit tests for the text_extractor service using pytest.

## Prerequisites
- Docker and Docker Compose
- Docker Swarm initialized (`docker swarm init`)
- Python 3.10+ (for local development)
- Access to a local Docker registry at `localhost:5000` (or modify `docker-compose.yml` to use public images)

## Setup and Installation
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/haiderze/pdf_text_extractor.git
   cd pdf_text_extractor
   ```

2. **Build Docker Images**:
   Ensure you have a local Docker registry running at `localhost:5000` or update the `image` fields in `docker-compose.yml` to point to your registry or public images. Then, build the images:
   ```bash
   docker-compose build
   ```

3. **Install Dependencies (Optional for Local Development)**:
   For running services locally without Docker:
   ```bash
   cd text_extractor
   pip install -r requirements.txt
   cd ../ocr_service
   pip install -r requirements.txt
   ```

## Running the Application
1. **Using Docker Swarm**:
   Start both services using Docker Swarm:
   ```bash
   docker stack deploy -c docker-compose.yml pdf_text_extractor
   ```
   - The `text_extractor` service will be available at `http://localhost:8001`.
   - The `ocr_service` service will be available at `http://localhost:8002`.

2. **Local Development (Without Docker)**:
   Run the text_extractor service:
   ```bash
   cd text_extractor
   uvicorn main:app --host 0.0.0.0 --port 8001
   ```
   Run the ocr_service:
   ```bash
   cd ocr_service
   uvicorn main:app --host 0.0.0.0 --port 8002
   ```

## API Endpoints
### text_extractor Service (`http://localhost:8001`)
- **GET /health_check**
  - Description: Checks the health status of the text_extractor service.
  - Response: `{"status": "ok"}`
  - Status Code: 200

- **POST /get_text**
  - Description: Extracts text from a PDF provided via a URL.
  - Request Body: `{"url": "https://example.com/sample.pdf"}`
  - Response: `{"text": "Extracted text from PDF"}`
  - Status Codes:
    - 200: Success
    - 400: Invalid PDF URL or no text extracted
    - 500: Server or OCR service error
    - 502: Network error-pitfall error

### ocr_service Service (`http://localhost:8002`)
- **POST /predict**
  - Description: Processes a PDF file to extract text using OCR.
  - Request: Multipart form-data with a PDF file (`pdf` field)
  - Response: `{"text": "Extracted text from PDF"}`
  - Status Codes:
    - 200: Success
    - 400: Invalid file (not a PDF)
    - 500: OCR processing error

## Testing
The `text_extractor` service includes unit tests in `test_main.py`. To run tests:
```bash
cd text_extractor
pytest test_main.py
```

Tests cover:
- Health check endpoint
- Successful PDF text extraction
- Handling 404 errors for invalid URLs
- Handling empty PDFs

## Deployment
1. **Initialize Docker Swarm** (if not already initialized):
   ```bash
   docker swarm init
   ```

2. **Push Images to Registry**:
   Build and push Docker images to your registry:
   ```bash
   docker-compose build
   docker-compose push
   ```

3. **Deploy with Docker Swarm**:
   Deploy the stack using the `docker-compose.yml` file:
   ```bash
   docker stack deploy -c docker-compose.yml pdf_text_extractor
   ```

4. **Scaling**:
   The `ocr_service` is configured with 2 replicas by default. Adjust the `replicas` field in `docker-compose.yml` to scale as needed:
   ```yaml
   deploy:
     replicas: 2
   ```
