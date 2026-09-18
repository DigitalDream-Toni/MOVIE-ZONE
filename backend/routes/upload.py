"""
MOVIE ZONE - Image Upload Route
================================
Handles uploading poster and backdrop images to the server.
Images are saved to backend/uploads/ and served as static files.
"""

import os
import uuid
from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Header
from typing import Optional

from routes.auth import verify_token

router = APIRouter(prefix="/api/upload", tags=["upload"])

# Where uploaded images are stored
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")

# Only allow these image types
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}

MAX_IMAGE_BYTES = 10 * 1024 * 1024


@router.post("/image")
def upload_image(
    file: UploadFile = File(...),
    category: str = Form("general"),
    name: str | None = Form(None),
    authorization: Optional[str] = Header(None),
):
    """
    Upload an image file.
    - file: The image file to upload
    - category: Either "poster" or "backdrop" (organizes files into subfolders)
    - name: Human-readable name to tag the saved file (e.g. "Moana", "Coyote vs. Acme").
            When provided the file is saved as "Moana-poster.jpg" instead of a bare UUID.
    - authorization: Admin JWT token
    """
    verify_token(authorization)

    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{file.content_type}' not allowed. Use JPEG, PNG, WebP, or GIF."
        )

    # Validate file size (max 10MB)
    contents = file.file.read()
    if len(contents) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")



    # Create category subfolder if needed
    category_dir = os.path.join(UPLOAD_DIR, category)
    os.makedirs(category_dir, exist_ok=True)

    # ---------- filename logic ----------
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    name = (name or "").strip()
    safe_name = "".join(ch for ch in name if ch.isalnum() or ch in " -_.").strip()
    if not safe_name:
        safe_name = uuid.uuid4().hex[:8]

    # If a readable name was supplied, find a free slot so the first upload of a
    # given title always wins the clean filename.
    if name:
        candidate = safe_name
        for _ in range(10):
            path = os.path.join(category_dir, f"{candidate}.{ext}")
            if not os.path.exists(path):
                filename = f"{candidate}.{ext}"
                break
            candidate = f"{safe_name}-{uuid.uuid4().hex[:6]}"
        else:
            candidate = f"{safe_name}-{uuid.uuid4().hex[:6]}"
            filename = f"{candidate}.{ext}"
    else:
        filename = f"{uuid.uuid4().hex[:12]}.{ext}"

    filepath = os.path.join(category_dir, filename)

    # Save file
    with open(filepath, "wb") as f:
        f.write(contents)

    # The readable base name (without extension) of what was actually saved — used
    # by the admin page to remember the preferred name for future re-uploads.
    saved_base = os.path.splitext(filename)[0]

    # Return the URL to access this image
    image_url = f"/api/upload/images/{category}/{filename}"

    return {
        "url": image_url,
        "filename": filename,
        "category": category,
        "size": len(contents),
        "message": "Image uploaded successfully.",
        "saved_name": saved_base,
        "name": name,
    }


@router.get("/images/{category}/{filename}")
def serve_image(category: str, filename: str):
    """
    Serve an uploaded image file.
    This allows the frontend to display uploaded images.
    """
    filepath = os.path.join(UPLOAD_DIR, category, filename)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Image not found.")

    # Determine content type from extension
    ext = filename.rsplit(".", 1)[-1].lower()
    content_types = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "gif": "image/gif",
    }
    content_type = content_types.get(ext, "image/jpeg")

    # no-cache: filenames are unique per upload, but an admin replacing an
    # image should see the new file immediately, not a cached copy.
    from fastapi.responses import FileResponse
    return FileResponse(filepath, media_type=content_type, headers={
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
    })
