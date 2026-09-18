"""
MOVIE ZONE - Image Upload Route
================================
Handles uploading poster and backdrop images.

Where images end up is decided by backend/storage.py:
- Production (Render): Cloudinary, because the server's disk is wiped
  on every deploy and uploaded files would otherwise disappear.
- Local development: backend/uploads/, as before.
"""

import os
import uuid
from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Header
from fastapi.responses import FileResponse

from routes.auth import verify_token
from storage import UPLOAD_DIR, save_image

router = APIRouter(prefix="/api/upload", tags=["upload"])

# Only allow these image types
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}

# Only allow these storage subfolders (prevents path tricks via "category")
ALLOWED_CATEGORIES = {"poster", "backdrop", "general"}

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

    # Validate the category (it becomes a folder/public-id segment)
    if category not in ALLOWED_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Category '{category}' not allowed. Use poster, backdrop, or general."
        )

    # ---------- filename logic ----------
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    name = (name or "").strip()
    safe_name = "".join(ch for ch in name if ch.isalnum() or ch in " -_.").strip()
    if not safe_name:
        safe_name = uuid.uuid4().hex[:8]

    # Store the image (Cloudinary in production, local disk in development)
    saved = save_image(contents, category, ext, safe_name)

    return {
        "url": saved["url"],
        "filename": saved["filename"],
        "category": category,
        "size": len(contents),
        "message": "Image uploaded successfully.",
        "saved_name": saved["saved_name"],
        "name": name,
        "storage": saved["storage"],
    }


@router.get("/images/{category}/{filename}")
def serve_image(category: str, filename: str):
    """
    Serve a locally-stored uploaded image file.
    (Images stored in Cloudinary are served by Cloudinary's CDN directly,
    so this route only handles local-development uploads.)
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
    return FileResponse(filepath, media_type=content_type, headers={
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
    })
