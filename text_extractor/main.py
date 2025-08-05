from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
import httpx
import io
import json


app = FastAPI()



class PdfUrl(BaseModel):
    url: HttpUrl


@app.get("/health_check")
async def health_check():
    return {"status": "ok"}

@app.post("/get_text")
async def get_text_from_pdf(pdf_url: PdfUrl):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://arxiv.org/"
        }

        async with httpx.AsyncClient(follow_redirects=True, headers=headers, timeout=20.0) as client:
            response = await client.get(str(pdf_url.url))

        if response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to download PDF. Status code: {response.status_code}"
            )

        # Send the PDF bytes to the OCR microservice (/predict)
        files = {
            'pdf': ('document.pdf', response.content, 'application/pdf')
        }

        async with httpx.AsyncClient(timeout=300.0) as ocr_client:
            ocr_response = await ocr_client.post("http://ocr_service:8000/predict", files=files)

        if ocr_response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=f"OCR service failed: {ocr_response.status_code} - {ocr_response.text}"
            )

        ocr_data = ocr_response.json()
        extracted_text = ocr_data.get("text", "")

        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="OCR service returned no text.")

        return JSONResponse(
            content={"text": extracted_text},
            media_type="application/json"
        )

    except HTTPException:
        raise

    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Network error: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

