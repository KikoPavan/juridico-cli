#!/usr/bin/env python3
"""
E2E validation of the PaddleOCR path in pdf-to-md.

Generates a synthetic PNG with known text via Pillow, feeds it to
_run_paddle_ocr(), and asserts the expected string is present in
the result.

Exit codes: 0=pass  1=fail
"""

import io
import sys
from pathlib import Path

EXPECTED_TEXT = "JURIDICO"

# ---------------------------------------------------------------------------
# Generate a synthetic test image with readable text
# ---------------------------------------------------------------------------

def _make_test_png() -> bytes:
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (400, 100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
    except Exception:
        font = ImageFont.load_default()
    draw.text((20, 20), EXPECTED_TEXT, fill=(0, 0, 0), font=font)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Import _run_paddle_ocr from the skill converter
# ---------------------------------------------------------------------------

def _load_run_paddle_ocr():
    scripts_dir = Path(__file__).parent
    sys.path.insert(0, str(scripts_dir))
    from convert_pdf_to_md import _run_paddle_ocr, _get_paddle_ocr
    return _run_paddle_ocr, _get_paddle_ocr


# ---------------------------------------------------------------------------
# Main validation
# ---------------------------------------------------------------------------

def main() -> int:
    _run_paddle_ocr, _get_paddle_ocr = _load_run_paddle_ocr()

    ocr_engine = _get_paddle_ocr()
    if ocr_engine is None:
        print("[FAIL] PaddleOCR not available — install with: uv sync --group ocr", file=sys.stderr)
        return 1

    print(f"[INFO] Generating synthetic PNG with expected text: '{EXPECTED_TEXT}'")
    img_bytes = _make_test_png()

    print("[INFO] Running PaddleOCR on synthetic image...")
    result = _run_paddle_ocr(img_bytes, ocr_engine)

    print(f"[INFO] OCR result: {result!r}")

    if EXPECTED_TEXT.lower() in result.lower():
        print(f"[PASS] Expected text '{EXPECTED_TEXT}' found in OCR output.")
        return 0
    else:
        print(
            f"[FAIL] Expected '{EXPECTED_TEXT}' not found in OCR output: {result!r}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
