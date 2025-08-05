from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from paddleocr import TextDetection, TextRecognition
from pdf2image import convert_from_bytes
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os
import io
import platform
import logging
from tqdm import tqdm
from sklearn.cluster import KMeans

app = FastAPI()
logging.basicConfig(level=logging.INFO)

# POPPLER_PATH = r"C:\\Users\\haide\Documents\\pdf_extract\\pix2textapp\\poppler-24.08.0\\Library\\bin" if platform.system() == "Windows" else None

# Initialize models
detector = TextDetection(model_name="PP-OCRv5_mobile_det")
recognizer = TextRecognition(model_name="PP-OCRv5_mobile_rec")

def dump_coords_to_file(det_results, output_path="coords.txt"):
    with open(output_path, 'w') as f:
        f.write("Bounding Box Coordinates and Scores:\n")
        for i, box in enumerate(det_results['dt_polys']):
            x_coords = box[:, 0]  # Extract x coordinates
            y_coords = box[:, 1]  # Extract y coordinates
            x_min = int(min(x_coords))
            y_min = int(min(y_coords))
            x_max = int(max(x_coords))
            y_max = int(max(y_coords))
            score = det_results['dt_scores'][i]
            f.write(f"Box {i+1}: ({x_min}, {y_min}, {x_max}, {y_max}) - Score: {score:.4f}\n")
    print(f"Coordinates saved to {output_path}")

def pil_to_cv2(pil_image):
    return np.array(pil_image.convert("RGB"))[:, :, ::-1]  # RGB → BGR


def extract_text_from_image(image: Image.Image):
    image_cv2 = pil_to_cv2(image)
    det_results = detector.predict(input=image_cv2, batch_size=1)[0]

    text_boxes = []
    for i, box in enumerate(det_results['dt_polys']):
        x_min = int(min(pt[0] for pt in box))
        y_min = int(min(pt[1] for pt in box))
        x_max = int(max(pt[0] for pt in box))
        y_max = int(max(pt[1] for pt in box))

        # Crop and recognize text
        cropped = image.crop((x_min, y_min, x_max, y_max))
        cropped_cv2 = pil_to_cv2(cropped)
        rec_result_list = recognizer.predict(input=[cropped_cv2])
        if rec_result_list and det_results['dt_scores'][i] >= 0.7:  # Filter low-confidence
            width = x_max - x_min
            if width > 20:  # Filter narrow boxes
                text_boxes.append({
                    'text': rec_result_list[0]['rec_text'],
                    'y_min': y_min,
                    'x_min': x_min
                })

    if not text_boxes:
        return ""

    # Detect column threshold using KMeans clustering
    x_coords = np.array([box['x_min'] for box in text_boxes]).reshape(-1, 1)
    kmeans = KMeans(n_clusters=2).fit(x_coords)
    column_centers = kmeans.cluster_centers_.flatten()
    column_threshold = (column_centers[0] + column_centers[1]) / 2

    # Split into left and right columns
    left_column = [box for box in text_boxes if box['x_min'] < column_threshold]
    right_column = [box for box in text_boxes if box['x_min'] >= column_threshold]

    # Sort each column by y_min (top-to-bottom)
    left_column.sort(key=lambda x: x['y_min'])
    right_column.sort(key=lambda x: x['y_min'])

    # Combine left column then right column
    sorted_boxes = left_column + right_column

    return "\n".join(box['text'] for box in sorted_boxes)


@app.post("/predict")
async def predict(pdf: UploadFile = File(...)):
    try:
        if not pdf.filename.lower().endswith(".pdf"):
            return JSONResponse(status_code=400, content={"error": "Only PDF files are supported."})

        images = convert_from_bytes(await pdf.read(), dpi=120)
        full_text = []

        for idx, image in enumerate(tqdm(images, desc="Processing pages"), 1):  
            logging.info(f"Processing page {idx}")
            text = extract_text_from_image(image)
            if text:
                full_text.append(f"--- Page {idx} ---\n{text}")


        if not full_text:
            return JSONResponse(status_code=500, content={"error": "No text extracted."})

        return {"text": "\n\n".join(full_text)}

    except Exception as e:
        logging.exception(f"Prediction failed: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})
