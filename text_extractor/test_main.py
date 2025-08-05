import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import fitz
from main import app
from httpx import Response

client = TestClient(app)


def test_health_check():
    response = client.get("/health_check")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("main.httpx.AsyncClient")
def test_get_text_from_pdf_success(mock_client_class):
    # Prepare a simple in-memory PDF
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Hello, test PDF content.")
    pdf_bytes = doc.write()
    doc.close()

    # Mock the response object
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = pdf_bytes

    # Mock the AsyncClient context manager and its get method
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client_class.return_value.__aenter__.return_value = mock_client

    response = client.post("/get_text", json={"url": "https://example.com/sample.pdf"})
    assert response.status_code == 200
    assert "Hello, test PDF content." in response.json()["text"]


@patch("main.httpx.AsyncClient")
def test_get_text_from_pdf_404(mock_client_class):
    # Mock the response for a 404 status code
    mock_response = MagicMock(spec=Response)
    mock_response.status_code = 404
    mock_response.content = b"Not Found"

    # Mock the AsyncClient's get method
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    # Configure the context manager to return the mocked client
    mock_client_class.return_value.__aenter__.return_value = mock_client

    response = client.post("/get_text", json={"url": "https://example.com/404.pdf"})
    assert response.status_code == 400
    assert "Failed to download PDF" in response.json()["detail"]


@patch("main.httpx.AsyncClient")
def test_get_text_from_empty_pdf(mock_client_class):
    # Create an empty PDF
    doc = fitz.open()
    doc.new_page()  # Add an empty page
    pdf_bytes = doc.write()
    doc.close()

    # Mock the response for a 200 status code with empty PDF content
    mock_response = MagicMock(spec=Response)
    mock_response.status_code = 200
    mock_response.content = pdf_bytes

    # Mock the AsyncClient's get method
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    # Configure the context manager to return the mocked client
    mock_client_class.return_value.__aenter__.return_value = mock_client

    response = client.post("/get_text", json={"url": "https://example.com/empty.pdf"})
    assert response.status_code == 400
    assert "No text found in the PDF" in response.json()["detail"]
