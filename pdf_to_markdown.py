#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF -> Markdown using PyMuPDF (no poppler).
Renders each PDF page to an image (JPEG) and calls Tencent OCR per-image.
"""

import os
import json
import base64
import io
from pathlib import Path

from tencentcloud.common import credential
from tencentcloud.ocr.v20181119 import ocr_client, models

# PyMuPDF for rendering PDF pages to images
try:
    import fitz  # PyMuPDF
except Exception as e:
    raise ImportError("请先安装 PyMuPDF: pip install pymupdf") from e

from PIL import Image

# Tencent limits
MAX_B64_BYTES = 7 * 1024 * 1024  # 7 MB

# default render settings
DEFAULT_DPI = 150
MIN_DPI = 72


def init_ocr_client():
    secret_id = os.getenv("TENCENTCLOUD_SECRET_ID")
    secret_key = os.getenv("TENCENTCLOUD_SECRET_KEY")
    if not secret_id or not secret_key:
        raise ValueError("请设置环境变量: TENCENTCLOUD_SECRET_ID / TENCENTCLOUD_SECRET_KEY")
    cred = credential.Credential(secret_id, secret_key)
    client = ocr_client.OcrClient(cred, "ap-shanghai")
    return client


def image_bytes_to_b64(img_bytes: bytes) -> str:
    return base64.b64encode(img_bytes).decode("utf-8")


def call_ocr_image(client, image_b64: str, use_accurate=True):
    """
    Call Tencent OCR with an image (ImageBase64).
    If use_accurate True -> GeneralAccurateOCR, else GeneralBasicOCR.
    Returns parsed JSON.
    """
    if use_accurate:
        req = models.GeneralAccurateOCRRequest()
        params = {"ImageBase64": image_b64}
    else:
        req = models.GeneralBasicOCRRequest()
        params = {"ImageBase64": image_b64}
    req.from_json_string(json.dumps(params))
    if use_accurate:
        resp = client.GeneralAccurateOCR(req)
    else:
        resp = client.GeneralBasicOCR(req)
    return json.loads(resp.to_json_string())


def ocr_json_to_markdown(ocr_json):
    """Convert OCR JSON to markdown text (simple line join)."""
    lines = []
    # GeneralAccurateOCR returns 'TextDetections'
    for item in ocr_json.get("TextDetections", []):
        text = item.get("DetectedText", "").strip()
        if text:
            lines.append(text)
    return "\n".join(lines)


def render_page_to_jpeg_bytes(doc, page_number, dpi=DEFAULT_DPI, jpeg_quality=85):
    """
    Render single page (0-indexed) to JPEG bytes using PyMuPDF.
    Will return bytes of JPEG image.
    """
    page = doc.load_page(page_number)
    mat = fitz.Matrix(dpi / 72.0, dpi / 72.0)  # scale
    pix = page.get_pixmap(matrix=mat, alpha=False)  # RGB
    img_bytes = pix.tobytes(output="png")  # get PNG bytes first (lossless)
    # Convert PNG bytes to JPEG (to reduce size) via PIL
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=jpeg_quality)
    return buf.getvalue()


def ensure_under_limit(img_bytes: bytes, dpi, page_idx):
    """
    Ensure image base64 <= MAX_B64_BYTES by reducing dpi or quality.
    Returns (img_bytes, dpi_used) or raises if cannot reduce further.
    """
    img_b64 = image_bytes_to_b64(img_bytes)
    b64_size = len(img_b64.encode("utf-8"))
    if b64_size <= MAX_B64_BYTES:
        return img_bytes, dpi

    # Try progressively lowering JPEG quality and DPI
    quality_list = [85, 70, 60, 50, 35]
    dpi_now = dpi
    for q in quality_list:
        # reduce dpi gradually
        for d in [dpi_now, max(MIN_DPI, dpi_now // 2), MIN_DPI]:
            try:
                # re-render at smaller dpi
                rendered = render_page_to_jpeg_bytes_cached_bytes(page_doc_bytes=None, page_idx=page_idx, dpi=d, jpeg_quality=q)
            except Exception:
                # fallback: can't re-render here; break to next
                continue
            b64 = image_bytes_to_b64(rendered)
            if len(b64.encode("utf-8")) <= MAX_B64_BYTES:
                return rendered, d
        dpi_now = max(MIN_DPI, dpi_now // 2)

    raise RuntimeError("单页图像压缩失败，仍超出 7MB 限制。请手动压缩或上传到 COS 并使用 URL 识别。")


# We'll implement a helper that re-renders using the open doc (so we avoid passing raw bytes).
# To keep simple, we will re-render using the doc object passed in pdf_to_markdown loop,
# so the ensure_under_limit above will be simplified in main flow.

def pdf_to_markdown(pdf_path: str, dpi=DEFAULT_DPI, use_accurate=True):
    client = init_ocr_client()
    doc = fitz.open(pdf_path)
    n = doc.page_count
    md_pages = []

    for idx in range(n):
        print(f"[OCR] 渲染并处理第 {idx+1}/{n} 页 (初始 DPI={dpi}) …")
        # try rendering & encoding
        current_dpi = dpi
        current_quality = 85
        # render JPEG bytes
        img_bytes = render_page_to_jpeg_bytes(doc, idx, dpi=current_dpi, jpeg_quality=current_quality)
        b64 = image_bytes_to_b64(img_bytes)
        b64_size = len(b64.encode("utf-8"))
        # if too large, progressively reduce quality and dpi
        while b64_size > MAX_B64_BYTES and current_dpi > MIN_DPI:
            # reduce dpi
            current_dpi = max(MIN_DPI, current_dpi // 2)
            current_quality = max(30, current_quality - 20)
            print(f"  [INFO] 第 {idx+1} 页 base64 {b64_size} bytes > 7MB，降 DPI -> {current_dpi}, quality -> {current_quality}")
            img_bytes = render_page_to_jpeg_bytes(doc, idx, dpi=current_dpi, jpeg_quality=current_quality)
            b64 = image_bytes_to_b64(img_bytes)
            b64_size = len(b64.encode("utf-8"))

        if b64_size > MAX_B64_BYTES:
            raise RuntimeError(f"第 {idx+1} 页图像经过压缩仍然超过 7MB，无法直接用 ImageBase64 识别。建议上传到 COS 并用 URL 识别或手动压缩页面。")

        # call OCR
        try:
            ocr_json = call_ocr_image(client, b64, use_accurate=use_accurate)
        except Exception as e:
            # If accurate fails, try basic
            print(f"  [WARN] 第 {idx+1} 页使用 Accurate OCR 失败，尝试 Basic OCR: {e}")
            ocr_json = call_ocr_image(client, b64, use_accurate=False)

        md = ocr_json_to_markdown(ocr_json)
        md_pages.append(f"<!-- Page {idx+1} -->\n\n{md}")

    return "\n\n".join(md_pages)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("使用方式: python pdf_to_markdown.py files/cover_letter.pdf")
        exit(1)

    pdf_file = sys.argv[1]
    output_md = pdf_file + ".md"

    markdown = pdf_to_markdown(pdf_file)
    Path(output_md).write_text(markdown, encoding="utf-8")
    print(f"\n转换完成 → {output_md}")
