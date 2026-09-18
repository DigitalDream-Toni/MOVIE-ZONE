"""
MOVIE ZONE - Image Storage Layer
================================

Decides WHERE uploaded images are kept.

WHY THIS EXISTS:
Free/low-cost hosts (like Render's free tier) wipe the server's local disk
on every deploy. Any poster saved to backend/uploads/ would vanish, leaving
the site full of broken images. So in production we store images in
Cloudinary (a free image-hosting service) instead.

HOW THE BACKEND IS CHOSEN:
- If the CLOUDINARY_URL environment variable is set (e.g. on Render),
  images are uploaded to Cloudinary and the database stores the full
  https://res.cloudinary.com/... URL.
- Otherwise (local development) images are saved to backend/uploads/
  exactly like before, and the database stores a root-relative path
  like /api/upload/images/poster/Moana.jpg.

SETUP (production only):
1. Create a free account at https://cloudinary.com
2. Copy the "CLOUDINARY_URL" shown on the dashboard
   (it looks like cloudinary://1234567890:abcdef12@your-cloud-name)
3. Add it as an environment variable on Render and redeploy.
"""

import os
import uuid
from urllib.parse import urlsplit

from dotenv import load_dotenv

# Load backend/.env so CLOUDINARY_URL works no matter how the app is started
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

# Local-disk location (used when Cloudinary is not configured)
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")

# All Movie Zone images live in this folder inside Cloudinary
CLOUDINARY_FOLDER = "moviezone"

CLOUDINARY_URL = os.getenv("CLOUDINARY_URL", "").strip()
USE_CLOUDINARY = bool(CLOUDINARY_URL)

if USE_CLOUDINARY:
    # Parse cloudinary://<api_key>:<api_secret>@<cloud_name>
    _parts = urlsplit(CLOUDINARY_URL)
    if not (_parts.scheme == "cloudinary" and _parts.username and _parts.password and _parts.hostname):
        raise RuntimeError(
            "CLOUDINARY_URL is set but malformed. It must look like "
            "cloudinary://<api_key>:<api_secret>@<cloud_name>"
        )

    # The SDK also reads CLOUDINARY_URL at import time and raises its own
    # (less friendly) error on odd values. Remove it from the environment
    # and configure the SDK explicitly instead.
    os.environ.pop("CLOUDINARY_URL", None)

    import cloudinary
    import cloudinary.uploader

    cloudinary.config(
        cloud_name=_parts.hostname,
        api_key=_parts.username,
        api_secret=_parts.password,
        secure=True,
    )


def _clean_ext(ext: str) -> str:
    """Normalize a file extension: lowercase, no dot, letters/digits only."""
    ext = (ext or "").lower().lstrip(".")
    return ext if ext and ext.isalnum() else "jpg"


def _save_to_disk(contents: bytes, category: str, ext: str, safe_name: str) -> dict:
    """
    Save image bytes to backend/uploads/<category>/ and return storage info.
    First upload of a name wins the clean filename; later ones get a
    short random suffix so nothing is silently overwritten.
    """
    category_dir = os.path.join(UPLOAD_DIR, category)
    os.makedirs(category_dir, exist_ok=True)

    filename = f"{safe_name}.{ext}"
    if os.path.exists(os.path.join(category_dir, filename)):
        for _ in range(10):
            candidate = f"{safe_name}-{uuid.uuid4().hex[:6]}"
            filename = f"{candidate}.{ext}"
            if not os.path.exists(os.path.join(category_dir, filename)):
                break

    filepath = os.path.join(category_dir, filename)
    with open(filepath, "wb") as f:
        f.write(contents)

    return {
        # Root-relative path, stored in the DB and resolved by the
        # frontend's mediaUrl() helper against the backend origin.
        "url": f"/api/upload/images/{category}/{filename}",
        "filename": filename,
        "saved_name": os.path.splitext(filename)[0],
        "storage": "local",
    }


def _save_to_cloudinary(contents: bytes, category: str, ext: str, safe_name: str) -> dict:
    """
    Upload image bytes to Cloudinary and return storage info.

    Mirrors the local-disk "first upload wins the clean name" rule:
    if the desired name is already taken, a short random suffix is
    appended and the upload is retried.
    """
    folder = f"{CLOUDINARY_FOLDER}/{category}"

    def _upload(public_id: str) -> dict:
        return cloudinary.uploader.upload(
            contents,
            public_id=public_id,
            resource_type="image",
            overwrite=False,   # never silently replace an existing image
            invalidate=True,   # refresh Cloudinary's CDN cache
        )

    candidate = safe_name
    for _ in range(10):
        try:
            result = _upload(f"{folder}/{candidate}")
            break
        except Exception as err:
            if "already exists" not in str(err).lower():
                raise
            candidate = f"{safe_name}-{uuid.uuid4().hex[:6]}"
    else:
        # All ten attempts collided - fall back to a purely random name.
        candidate = uuid.uuid4().hex[:12]
        result = _upload(f"{folder}/{candidate}")

    stem = result["public_id"].rsplit("/", 1)[-1]
    return {
        # Full https URL, stored in the DB and used by the frontend as-is.
        "url": result["secure_url"],
        "filename": f"{stem}.{result.get('format', ext)}",
        "saved_name": stem,
        "storage": "cloudinary",
    }


def save_image(contents: bytes, category: str, ext: str, safe_name: str) -> dict:
    """
    Store an image and return where it landed.

    contents:  raw image bytes
    category:  "poster", "backdrop" or "general" (used as a subfolder)
    ext:       file extension, e.g. "jpg" (dot optional)
    safe_name: pre-cleaned base name for the file (no extension)

    Returns a dict with:
      url:        what to save in the database
      filename:   base name of the stored file (e.g. "Moana.jpg")
      saved_name: filename without the extension (for re-upload naming)
      storage:    "cloudinary" or "local"
    """
    ext = _clean_ext(ext)
    if USE_CLOUDINARY:
        return _save_to_cloudinary(contents, category, ext, safe_name)
    return _save_to_disk(contents, category, ext, safe_name)
