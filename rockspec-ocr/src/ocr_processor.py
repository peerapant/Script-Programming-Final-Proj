import os
import re
import io
from typing import List, Tuple, Union
import cv2
import easyocr
import numpy as np
from PIL import Image

CROP_BOX = (453, 908, 514, 930)


class ImageOCRProcessor:
    def __init__(self, languages: List[str] = None):
        if languages is None:
            languages = ['en']
        self.reader = easyocr.Reader(languages)

    @staticmethod
    def preprocess_image(img_np_uint8: np.ndarray) -> np.ndarray:
        if img_np_uint8.ndim == 3:
            if img_np_uint8.shape[2] == 4:
                gray = cv2.cvtColor(img_np_uint8, cv2.COLOR_RGBA2GRAY)
            elif img_np_uint8.shape[2] == 3:
                gray = cv2.cvtColor(img_np_uint8, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_np_uint8
        else:
            gray = img_np_uint8

        resized_gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        _, binarized = cv2.threshold(resized_gray, 200, 255, cv2.THRESH_BINARY)
        kernel = np.ones((2, 2), np.uint8)
        return cv2.erode(binarized, kernel, iterations=1)

    def extract_magnification(
        self, 
        image_input: Union[str, io.BytesIO, Image.Image], 
        crop_box: Tuple[int, int, int, int] = CROP_BOX
    ) -> float:
        """อ่านค่ากำลังขยาย รองรับทั้ง File Path, BytesIO (Cloud), และ PIL Image"""
        try:
            if isinstance(image_input, (str, os.PathLike)):
                image = Image.open(image_input)
            elif isinstance(image_input, io.BytesIO):
                image = Image.open(image_input)
            elif isinstance(image_input, Image.Image):
                image = image_input
            else:
                raise ValueError("Unsupported image input type")

            cropped_img = image.crop(crop_box) if crop_box else image
            img_np = np.array(cropped_img).astype(np.uint8)
            processed_image = self.preprocess_image(img_np)

            results = self.reader.readtext(
                processed_image,
                allowlist='0123456789xX',
                text_threshold=0.3,
                detail=0
            )
            raw_text = "".join(results).lower().replace('x', '')
            match = re.search(r'(\d+(?:\.\d+)?)', raw_text)
            if match:
                return float(match.group(1))
        except Exception as e:
            print(f"[WARNING] เกิดข้อผิดพลาดในการอ่าน OCR: {e}")

        return 0.0