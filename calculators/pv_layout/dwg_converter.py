"""
dwg_converter.py
----------------
Convert .dwg files to .dxf using available converters (tried in order):

  1. ODA File Converter   -- free local install (Windows/Linux/Mac)
     https://www.opendesign.com/guestfiles/oda_file_converter

  2. LibreDWG dwg2dxf     -- open-source local command-line tool
     https://www.gnu.org/software/libredwg/

  3. CloudConvert API v2  -- online, no local install, 25 free jobs/day
     https://cloudconvert.com/dashboard/api/v2/keys

All HTTP calls use Python's built-in urllib -- no third-party libraries needed.

Usage
-----
    from calculators.pv_layout.dwg_converter import (
        convert, detect_converter,
        get_cloudconvert_key, save_cloudconvert_key,
    )

    available, method = detect_converter()
    # method: "oda" | "libredwg" | "cloudconvert" | "none"

    ok, dxf_path, msg = convert("drawing.dwg", progress_fn=print)
    # dxf_path is a temp file -- OS cleans it up; no need to delete manually
"""
from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
import urllib.error
import urllib.request


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

# Known install locations for ODA File Converter on Windows
_ODA_SEARCH_PATHS = [
    r"C:\Program Files\ODA\ODAFileConverter\ODAFileConverter.exe",
    r"C:\Program Files (x86)\ODA\ODAFileConverter\ODAFileConverter.exe",
    r"C:\Program Files\ODA File Converter\ODAFileConverter.exe",
    r"C:\Program Files (x86)\ODA File Converter\ODAFileConverter.exe",
    r"C:\Program Files\ODA\ODAFileConverter_25.2.0\ODAFileConverter.exe",
    r"C:\Program Files\ODA\ODAFileConverter_24.12.0\ODAFileConverter.exe",
    r"C:\Program Files\ODA\ODAFileConverter_24.6.0\ODAFileConverter.exe",
    r"C:\Program Files\ODA\ODAFileConverter_23.12.0\ODAFileConverter.exe",
]

_ODA_OUTPUT_VERSION = "ACAD2018"

# CloudConvert API v2 base URL
_CC_BASE = "https://api.cloudconvert.com/v2"

INSTALL_HELP = (
    "No DWG-to-DXF converter is configured.\n\n"
    "Option A  --  Online (no install needed):\n"
    "  Set a free CloudConvert API key via the 'Cloud Key' button.\n"
    "  Get your key at: https://cloudconvert.com/dashboard/api/v2/keys\n"
    "  (25 free conversions per day on the free plan)\n\n"
    "Option B  --  Local (free Windows installer):\n"
    "  ODA File Converter:\n"
    "  https://www.opendesign.com/guestfiles/oda_file_converter\n\n"
    "Option C  --  Local (open-source command-line):\n"
    "  LibreDWG  (dwg2dxf):\n"
    "  https://www.gnu.org/software/libredwg/"
)


# ─────────────────────────────────────────────────────────────────────────────
# Settings storage  (~/.engineering_suite/settings.json)
# ─────────────────────────────────────────────────────────────────────────────

def _settings_path() -> Path:
    return Path.home() / ".engineering_suite" / "settings.json"


def get_cloudconvert_key() -> str | None:
    """Return the saved CloudConvert API key, or None if not set."""
    try:
        data = json.loads(_settings_path().read_text(encoding="utf-8"))
        return data.get("cloudconvert_api_key", "").strip() or None
    except Exception:
        return None


def save_cloudconvert_key(key: str | None) -> None:
    """Save (or clear) the CloudConvert API key."""
    path = _settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    data["cloudconvert_api_key"] = (key or "").strip()
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# Converter detection
# ─────────────────────────────────────────────────────────────────────────────

def _find_oda() -> str | None:
    for p in _ODA_SEARCH_PATHS:
        if os.path.isfile(p):
            return p
    return shutil.which("ODAFileConverter")


def _find_dwg2dxf() -> str | None:
    return shutil.which("dwg2dxf")


def detect_converter() -> tuple[bool, str]:
    """
    Return ``(available, method)`` where method is one of:
    ``"oda"``, ``"libredwg"``, ``"cloudconvert"``, ``"none"``.
    """
    if _find_oda():
        return True, "oda"
    if _find_dwg2dxf():
        return True, "libredwg"
    if get_cloudconvert_key():
        return True, "cloudconvert"
    return False, "none"


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def convert(dwg_path: str, progress_fn=None) -> tuple[bool, str, str]:
    """
    Convert *dwg_path* (.dwg) to a temporary .dxf file.

    Parameters
    ----------
    dwg_path    : str
        Path to the input DWG file.
    progress_fn : callable, optional
        Called as ``fn(message: str)`` during CloudConvert polling.

    Returns
    -------
    (success, dxf_path, message)
        success=True  -> dxf_path is a valid temp .dxf file.
        success=False -> dxf_path is "", message describes the error.
    """
    dwg_path = str(Path(dwg_path).resolve())
    if not os.path.isfile(dwg_path):
        return False, "", f"File not found:\n{dwg_path}"

    _, method = detect_converter()

    if method == "oda":
        return _convert_oda(dwg_path)
    if method == "libredwg":
        return _convert_libredwg(dwg_path)
    if method == "cloudconvert":
        key = get_cloudconvert_key()
        return _convert_cloudconvert(dwg_path, key, progress_fn)

    return False, "", INSTALL_HELP


# ─────────────────────────────────────────────────────────────────────────────
# ODA File Converter (local subprocess)
# ─────────────────────────────────────────────────────────────────────────────

def _subprocess_kwargs() -> dict:
    kw: dict = {"capture_output": True, "text": True, "timeout": 180}
    if sys.platform == "win32":
        kw["creationflags"] = subprocess.CREATE_NO_WINDOW
    return kw


def _convert_oda(dwg_path: str) -> tuple[bool, str, str]:
    oda     = _find_oda()
    stem    = Path(dwg_path).stem
    in_dir  = str(Path(dwg_path).parent)
    out_dir = tempfile.mkdtemp(prefix="dwg_oda_")

    cmd = [oda, in_dir, out_dir, _ODA_OUTPUT_VERSION, "DXF", "0", "1", f"{stem}.dwg"]

    try:
        result = subprocess.run(cmd, **_subprocess_kwargs())
    except subprocess.TimeoutExpired:
        return False, "", "ODA File Converter timed out (>3 min)."
    except FileNotFoundError:
        return False, "", f"ODA File Converter not found:\n{oda}"
    except Exception as exc:
        return False, "", f"ODA File Converter error:\n{exc}"

    dxf_path = str(Path(out_dir) / (stem + ".dxf"))
    if os.path.isfile(dxf_path):
        return True, dxf_path, f"Converted with ODA File Converter ({_ODA_OUTPUT_VERSION})."

    err_log = Path(out_dir) / "ODAFileConverter.log"
    err_txt = ""
    if err_log.is_file():
        try:
            err_txt = err_log.read_text(errors="replace")[:800]
        except Exception:
            pass

    detail = "\n".join(filter(None, [
        (result.stdout or "").strip(),
        (result.stderr or "").strip(),
        err_txt,
    ])) or "(no output)"

    return False, "", (
        "ODA File Converter ran but produced no .dxf output.\n\n"
        f"Detail:\n{detail}\n\n"
        "Tips:\n"
        "* Make sure the DWG is not password-protected.\n"
        "* Try opening in AutoCAD and re-saving as DXF R2010."
    )


# ─────────────────────────────────────────────────────────────────────────────
# LibreDWG (local subprocess)
# ─────────────────────────────────────────────────────────────────────────────

def _convert_libredwg(dwg_path: str) -> tuple[bool, str, str]:
    stem    = Path(dwg_path).stem
    out_dir = tempfile.mkdtemp(prefix="dwg_ldwg_")
    dxf_out = str(Path(out_dir) / (stem + ".dxf"))

    try:
        result = subprocess.run(
            ["dwg2dxf", "-o", dxf_out, dwg_path], **_subprocess_kwargs())
    except subprocess.TimeoutExpired:
        return False, "", "dwg2dxf timed out (>3 min)."
    except FileNotFoundError:
        return False, "", "dwg2dxf not found. Please install LibreDWG."
    except Exception as exc:
        return False, "", f"dwg2dxf error:\n{exc}"

    if os.path.isfile(dxf_out):
        return True, dxf_out, "Converted with LibreDWG (dwg2dxf)."

    detail = "\n".join(filter(None, [
        (result.stdout or "").strip(),
        (result.stderr or "").strip(),
    ])) or "(no output)"
    return False, "", f"dwg2dxf produced no output.\n\n{detail}"


# ─────────────────────────────────────────────────────────────────────────────
# urllib helpers  (no third-party libraries required)
# ─────────────────────────────────────────────────────────────────────────────

def _http_post_json(url: str, payload: dict, headers: dict,
                    timeout: int = 30) -> tuple[int, dict]:
    """POST JSON, return (status_code, response_dict)."""
    body = json.dumps(payload).encode("utf-8")
    req_headers = {**headers, "Content-Type": "application/json"}
    req = urllib.request.Request(url, data=body, headers=req_headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")[:500]
        raise _HttpError(exc.code, body_text) from exc


def _http_get_json(url: str, headers: dict,
                   timeout: int = 15) -> tuple[int, dict]:
    """GET JSON, return (status_code, response_dict)."""
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")[:500]
        raise _HttpError(exc.code, body_text) from exc


def _http_post_multipart(url: str, fields: dict,
                          file_name: str, file_bytes: bytes,
                          timeout: int = 300) -> int:
    """
    POST a multipart/form-data request containing *fields* plus one file.
    Returns the HTTP status code.
    """
    boundary = uuid.uuid4().hex
    buf = io.BytesIO()

    def _write(s: str):
        buf.write(s.encode("utf-8"))

    for key, value in fields.items():
        _write(f"--{boundary}\r\n")
        _write(f'Content-Disposition: form-data; name="{key}"\r\n\r\n')
        _write(str(value))
        _write("\r\n")

    _write(f"--{boundary}\r\n")
    _write(f'Content-Disposition: form-data; name="file"; filename="{file_name}"\r\n')
    _write("Content-Type: application/octet-stream\r\n\r\n")
    buf.write(file_bytes)
    _write(f"\r\n--{boundary}--\r\n")

    body = buf.getvalue()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code


def _http_download(url: str, dest_path: str, timeout: int = 120) -> int:
    """Download *url* to *dest_path*. Returns HTTP status code."""
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            with open(dest_path, "wb") as fh:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    fh.write(chunk)
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code


class _HttpError(Exception):
    def __init__(self, code: int, body: str):
        self.code = code
        self.body = body
        super().__init__(f"HTTP {code}: {body}")


# ─────────────────────────────────────────────────────────────────────────────
# CloudConvert API v2 backend  (uses stdlib urllib only)
# ─────────────────────────────────────────────────────────────────────────────

def _qt_events():
    """Pump the Qt event loop if running inside a Qt app."""
    try:
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()
    except Exception:
        pass


def _convert_cloudconvert(dwg_path: str, api_key: str,
                           progress_fn=None) -> tuple[bool, str, str]:
    """
    Convert a DWG via the CloudConvert REST API v2.

    Steps
    -----
    1. POST /jobs  -- create job (upload + convert + export tasks)
    2. POST <S3 form URL>  -- multipart upload of the DWG file
    3. GET  /jobs/{id}     -- poll until "finished" or "error"
    4. GET  <export URL>   -- stream-download the DXF to a temp file
    """

    def _prog(msg: str):
        if progress_fn:
            progress_fn(msg)

    stem  = Path(dwg_path).stem
    fname = Path(dwg_path).name
    auth  = {"Authorization": f"Bearer {api_key}"}

    # ── 1. Create job ─────────────────────────────────────────────────────────
    _prog("CloudConvert: creating conversion job...")

    job_def = {
        "tasks": {
            "upload-file":  {"operation": "import/upload"},
            "convert-file": {
                "operation":     "convert",
                "input":         "upload-file",
                "input_format":  "dwg",
                "output_format": "dxf",
            },
            "export-file":  {
                "operation": "export/url",
                "input":     "convert-file",
            },
        }
    }

    try:
        _, job_resp = _http_post_json(f"{_CC_BASE}/jobs", job_def, auth)
    except _HttpError as exc:
        if exc.code == 401:
            return False, "", (
                "CloudConvert: API key rejected (HTTP 401).\n\n"
                "The key is invalid or has been revoked.\n\n"
                "Fix: go to https://cloudconvert.com/dashboard/api/v2/keys\n"
                "and create a new key, then update it via the 'Cloud Key' button."
            )
        if exc.code == 403:
            return False, "", (
                "CloudConvert: API key has insufficient permissions (HTTP 403).\n\n"
                "Your key is missing required scopes.  To fix:\n\n"
                "  1. Go to https://cloudconvert.com/dashboard/api/v2/keys\n"
                "  2. Delete your current key\n"
                "  3. Click 'Create API Key'\n"
                "  4. Under Scopes, tick BOTH:\n"
                "       [x] task.read    (View your tasks and jobs)\n"
                "       [x] task.write   (Create tasks and jobs for you)\n"
                "  5. Copy the new key and paste it via the 'Cloud Key' button."
            )
        return False, "", (
            f"CloudConvert: job creation failed (HTTP {exc.code}).\n{exc.body}"
        )
    except Exception as exc:
        return False, "", f"CloudConvert: network error creating job.\n{exc}"

    job_data = job_resp["data"]
    job_id   = job_data["id"]

    # Find upload task and its S3 form
    upload_task = next(
        (t for t in job_data.get("tasks", []) if t.get("operation") == "import/upload"),
        None,
    )
    if not upload_task:
        return False, "", "CloudConvert: upload task missing from job response."

    form = upload_task.get("result", {}).get("form")
    if not form:
        return False, "", "CloudConvert: upload form URL missing from job response."

    form_url    = form["url"]
    form_params = form.get("parameters", {})

    # ── 2. Upload DWG ─────────────────────────────────────────────────────────
    _prog(f"CloudConvert: uploading {fname}...")

    try:
        file_bytes = Path(dwg_path).read_bytes()
    except Exception as exc:
        return False, "", f"Cannot read DWG file:\n{exc}"

    try:
        status = _http_post_multipart(form_url, form_params, fname, file_bytes)
    except Exception as exc:
        return False, "", f"CloudConvert: upload error.\n{exc}"

    if status not in (200, 201, 204):
        return False, "", f"CloudConvert: upload failed (HTTP {status})."

    # ── 3. Poll until finished ────────────────────────────────────────────────
    poll_url = f"{_CC_BASE}/jobs/{job_id}"

    for attempt in range(90):           # up to ~3 minutes at 2 s per loop
        # Sleep 2 s in 100 ms slices to keep Qt UI responsive
        for _ in range(20):
            time.sleep(0.1)
            _qt_events()

        elapsed = (attempt + 1) * 2
        _prog(f"CloudConvert: converting... ({elapsed}s)")

        try:
            _, info = _http_get_json(poll_url, auth)
        except Exception:
            continue    # transient error, keep polling

        job_info = info["data"]
        status   = job_info.get("status", "")

        if status == "finished":
            for t in job_info.get("tasks", []):
                if t.get("operation") == "export/url" and t.get("status") == "finished":
                    files = t.get("result", {}).get("files", [])
                    if files:
                        _prog("CloudConvert: downloading DXF...")
                        return _cc_download(files[0]["url"], stem)
            return False, "", "CloudConvert: job finished but no export file found."

        if status == "error":
            detail = ""
            for t in job_info.get("tasks", []):
                if t.get("status") == "error":
                    detail = t.get("message") or t.get("code") or ""
                    break
            return False, "", (
                f"CloudConvert: conversion error.\n"
                f"{detail or 'Check your CloudConvert dashboard.'}"
            )

    return False, "", (
        f"CloudConvert: timed out (>3 min).\nJob ID: {job_id}\n"
        "Check https://cloudconvert.com/dashboard for status."
    )


def _cc_download(url: str, stem: str) -> tuple[bool, str, str]:
    """Download converted DXF to a temporary file."""
    out_dir = tempfile.mkdtemp(prefix="dwg_cc_")
    dxf_out = str(Path(out_dir) / (stem + ".dxf"))

    try:
        status = _http_download(url, dxf_out)
    except Exception as exc:
        return False, "", f"CloudConvert: download error.\n{exc}"

    if status not in (200, 201):
        return False, "", f"CloudConvert: download HTTP {status}."

    size = os.path.getsize(dxf_out) if os.path.isfile(dxf_out) else 0
    if size == 0:
        return False, "", "CloudConvert: downloaded DXF is empty."

    return True, dxf_out, f"Converted with CloudConvert ({size // 1024} KB)."
