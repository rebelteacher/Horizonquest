"""Cloudinary PowerPoint -> slide-image conversion (via the Aspose add-on).

Upload flow: upload the .pptx as a `raw` asset with raw_convert="aspose".
Cloudinary converts it (async, a few seconds) into a multi-page PDF stored as an
`image` resource with the SAME public_id, which we deliver page-by-page as JPGs.
"""
import os
import uuid
import tempfile
import cloudinary
import cloudinary.uploader
import cloudinary.utils
import cloudinary.api


def _cfg():
    cloudinary.config(
        cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
        api_key=os.environ.get("CLOUDINARY_API_KEY"),
        api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
        secure=True,
    )


def is_configured() -> bool:
    return bool(os.environ.get("CLOUDINARY_CLOUD_NAME") and os.environ.get("CLOUDINARY_API_KEY") and os.environ.get("CLOUDINARY_API_SECRET"))


def upload_pptx(data: bytes, block_id: str, ext: str = ".pptx") -> dict:
    """Upload a PowerPoint and trigger Aspose conversion. Returns {public_id}.
    Aspose needs a real file extension to detect the type, so we upload from a temp file."""
    _cfg()
    token = uuid.uuid4().hex[:12]
    if ext not in (".pptx", ".ppt"):
        ext = ".pptx"
    tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
    try:
        tmp.write(data)
        tmp.flush()
        tmp.close()
        res = cloudinary.uploader.upload(
            tmp.name,
            resource_type="raw",
            raw_convert="aspose",
            public_id=f"horizonquest/decks/{block_id}/{token}",
            overwrite=True,
        )
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
    return {"public_id": res["public_id"]}


def resolve_pages(public_id: str):
    """Return (pages, version) once the converted image resource is ready, else None."""
    _cfg()
    try:
        res = cloudinary.api.resource(public_id, resource_type="image", pages=True)
    except Exception:
        return None
    pages = res.get("pages")
    if not pages:
        return None
    return pages, res.get("version")


def page_urls(public_id: str, pages: int, version) -> list:
    _cfg()
    urls = []
    for n in range(1, int(pages) + 1):
        url, _ = cloudinary.utils.cloudinary_url(
            public_id, resource_type="image", format="jpg",
            page=n, quality="auto", version=version, secure=True,
        )
        urls.append(url)
    return urls


def destroy(public_id: str):
    _cfg()
    for rt in ("image", "raw"):
        try:
            cloudinary.uploader.destroy(public_id, resource_type=rt, invalidate=True)
        except Exception:
            pass
