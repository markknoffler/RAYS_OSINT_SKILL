"""URL and handle slug helpers for OSINT workspace file naming."""

import hashlib
import re
from urllib.parse import urlparse, unquote

PROFILE_FILENAME = "profile.png"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def slugify_name(name: str) -> str:
    """Convert subject name to workspace folder slug: 'Jane Doe' -> 'jane_doe'."""
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "subject"


def workspace_dir_name(subject_name: str) -> str:
    return f"{slugify_name(subject_name)}_osint"


def extract_handle_from_url(url: str, platform: str | None = None) -> str:
    """
    Derive social handle from profile URL.
    Examples:
      instagram.com/janedoe -> janedoe_ig
      linkedin.com/in/jane-doe -> jane-doe_linkedin
      x.com/janedoe -> janedoe_x
    """
    parsed = urlparse(url.strip())
    host = (parsed.netloc or "").lower().replace("www.", "")
    path = unquote(parsed.path or "").strip("/")
    segments = [s for s in path.split("/") if s]

    plat = platform or _platform_from_host(host)
    handle = ""

    if "instagram" in host and segments:
        handle = segments[0]
    elif "linkedin" in host:
        if segments and segments[0] == "in" and len(segments) > 1:
            handle = segments[1]
        elif segments:
            handle = segments[-1]
    elif host in ("x.com", "twitter.com") and segments:
        handle = segments[0]
    elif "facebook" in host and segments:
        handle = segments[-1]
    else:
        handle = segments[-1] if segments else host.split(".")[0]

    handle = re.sub(r"[^a-zA-Z0-9_-]", "_", handle).strip("_") or "unknown"
    suffix = _platform_suffix(plat)
    if suffix and not handle.endswith(f"_{suffix}"):
        handle = f"{handle}_{suffix}"
    return handle


def _platform_from_host(host: str) -> str:
    if "instagram" in host:
        return "instagram"
    if "linkedin" in host:
        return "linkedin"
    if host in ("x.com", "twitter.com"):
        return "x"
    if "facebook" in host:
        return "facebook"
    return "web"


def _platform_suffix(platform: str) -> str:
    return {
        "instagram": "ig",
        "linkedin": "linkedin",
        "x": "x",
        "twitter": "x",
        "facebook": "fb",
    }.get(platform, platform)


def url_to_image_filename(url: str, is_profile: bool = False) -> str:
    """
    Map media/post URL to screenshot filename.
    Profile is always profile.png; others use sanitized URL slug + .png
    """
    if is_profile:
        return PROFILE_FILENAME

    parsed = urlparse(url.strip())
    path = unquote(parsed.path or "")
    query = parsed.query or ""

    raw = path.strip("/").replace("/", "_")
    if query:
        raw = f"{raw}_{query}"

    slug = re.sub(r"[^a-zA-Z0-9_-]", "_", raw)
    slug = re.sub(r"_+", "_", slug).strip("_")

    if not slug:
        slug = hashlib.sha256(url.encode()).hexdigest()[:16]

    if len(slug) > 120:
        slug = slug[:80] + "_" + hashlib.sha256(url.encode()).hexdigest()[:8]

    return f"{slug}.png"


def is_image_file(path) -> bool:
    return path.suffix.lower() in IMAGE_EXTENSIONS
