"""OCR handling for scanned financial PDF pages."""

from typing import Optional
from app.core.logging import logger
from app.core.exceptions import OCRError


class OCRProcessor:
    """Processor for extracting text from scanned pages using OCR."""

    def __init__(self):
        self.engine_available = False
        self._init_engine()

    def _init_engine(self):
        """Attempts to initialize PaddleOCR or pytesseract if installed."""
        try:
            from paddleocr import PaddleOCR  # type: ignore
            self.paddle_engine = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
            self.engine_available = True
            logger.info("PaddleOCR engine initialized successfully.")
        except Exception:
            try:
                import pytesseract  # type: ignore
                self.pytesseract = pytesseract
                self.engine_available = True
                logger.info("pytesseract engine initialized successfully.")
            except Exception:
                self.engine_available = False
                logger.info("No external OCR engine installed. Standard text extraction will be prioritized.")

    def extract_text_from_image(self, image_bytes: bytes) -> str:
        """Extracts text from rasterized page image."""
        if not self.engine_available:
            raise OCRError(
                "OCR processing requested for scanned document, but neither PaddleOCR nor pytesseract is available in the current environment."
            )
        try:
            if hasattr(self, "paddle_engine"):
                result = self.paddle_engine.ocr(image_bytes, cls=True)
                lines = []
                for idx in range(len(result)):
                    res = result[idx]
                    if res:
                        for line in res:
                            lines.append(line[1][0])
                return "\n".join(lines)
            elif hasattr(self, "pytesseract"):
                import io
                from PIL import Image
                img = Image.open(io.BytesIO(image_bytes))
                return self.pytesseract.image_to_string(img)
            return ""
        except Exception as e:
            raise OCRError(f"OCR execution failed: {str(e)}") from e


ocr_processor = OCRProcessor()
