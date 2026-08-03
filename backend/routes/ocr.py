"""Image-to-product-search endpoint using local Tesseract OCR."""

from io import BytesIO

import pytesseract
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from PIL import Image, UnidentifiedImageError

router = APIRouter()

NO_TEXT_MESSAGE = "Couldn't read any text from that image. Try a clearer photo or use text search."


@router.post("/ocr/search")
async def search_image(
    image: UploadFile = File(...),
    top_k: int = Query(10, ge=1, le=100),
) -> list[dict] | dict:
    """Extract image text with Tesseract and use it to find matching products."""
    try:
        image_bytes = await image.read()
        uploaded_image = Image.open(BytesIO(image_bytes))
        uploaded_image.load()
    except (UnidentifiedImageError, OSError) as error:
        raise HTTPException(status_code=400, detail="Upload a valid image file.") from error

    try:
        extracted_text = " ".join(pytesseract.image_to_string(uploaded_image).split())
    except pytesseract.TesseractNotFoundError as error:
        raise HTTPException(
            status_code=503,
            detail="Tesseract OCR is not installed or is not available on the server PATH.",
        ) from error

    if not extracted_text:
        return {"results": [], "message": NO_TEXT_MESSAGE}

    try:
        # Imported lazily so the API can still start before a FAISS index is built.
        from retrieval.search import search_products

        return search_products(extracted_text, top_k)
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
