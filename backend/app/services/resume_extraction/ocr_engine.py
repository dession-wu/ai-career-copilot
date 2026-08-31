"""
OCR引擎封装
支持EasyOCR、Tesseract等多种OCR引擎
"""

import logging
from typing import List, Optional
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    Image = None

from .models import ParsedDocument, TextBlock, ImageBlock, PDFType, OCRResult
from .config import ocr_config
from .utils import clean_text

logger = logging.getLogger(__name__)


class OCREngine:
    """OCR引擎封装"""
    
    def __init__(self):
        self.config = ocr_config
        self._easyocr = None
        self._tesseract = None
    
    def _get_easyocr(self):
        """延迟加载EasyOCR"""
        if self._easyocr is None:
            try:
                import easyocr
                import os
                
                # 模型目录：优先读环境变量 EASYOCR_MODEL_DIR，否则用项目根目录下 models/easyocr
                model_dir = os.environ.get("EASYOCR_MODEL_DIR") or str(
                    Path(__file__).resolve().parents[4] / "models" / "easyocr"
                )
                try:
                    os.makedirs(model_dir, exist_ok=True)
                except OSError as e:
                    raise RuntimeError(
                        f"无法创建 EasyOCR 模型目录 {model_dir}：{e}。"
                        f"请检查目录权限，或通过环境变量 EASYOCR_MODEL_DIR 指定可写目录"
                    ) from e
                
                # 使用EasyOCR，支持中文和英文
                logger.info(f"初始化EasyOCR，模型目录: {model_dir}")
                self._easyocr = easyocr.Reader(
                    ['ch_sim', 'en'],
                    model_storage_directory=model_dir,
                    download_enabled=True
                )
                logger.info("EasyOCR初始化成功")
            except Exception as e:
                logger.error(f"EasyOCR初始化失败: {e}")
                import traceback
                logger.error(traceback.format_exc())
                raise
        return self._easyocr
    
    def parse_pdf(self, file_path: str) -> ParsedDocument:
        """
        解析扫描件PDF
        
        流程：
        1. PDF转图片
        2. 图片预处理
        3. OCR识别
        4. 结果合并
        """
        logger.info(f"使用OCR解析PDF: {file_path}")
        
        # PDF转图片
        images = self._pdf_to_images(file_path)
        
        if not images:
            logger.error("PDF转图片失败")
            return ParsedDocument(
                raw_text="",
                text_blocks=[],
                image_blocks=[],
                pdf_type=PDFType.SCANNED,
                page_count=0,
                metadata={"error": "PDF转图片失败"}
            )
        
        # OCR识别
        all_results = []
        for i, image in enumerate(images):
            logger.info(f"识别第 {i+1}/{len(images)} 页")
            
            # 预处理
            if self.config.enable_preprocessing:
                image = self._preprocess_image(image)
            
            # 识别
            results = self.recognize(image)
            all_results.extend(results)
        
        # 构建ParsedDocument
        return self._build_document(all_results, images, file_path)
    
    def recognize(self, image) -> List[OCRResult]:
        """
        识别图片中的文字
        
        Args:
            image: PIL.Image对象或图片路径
            
        Returns:
            List[OCRResult]: 识别结果列表
        """
        if self.config.engine == "easyocr":
            return self._recognize_with_easyocr(image)
        elif self.config.engine == "tesseract":
            return self._recognize_with_tesseract(image)
        else:
            # 默认使用EasyOCR
            return self._recognize_with_easyocr(image)
    
    def _recognize_with_easyocr(self, image) -> List[OCRResult]:
        """使用EasyOCR识别"""
        try:
            ocr = self._get_easyocr()
            
            # 处理输入图片
            if isinstance(image, Image.Image):
                # PIL Image直接转换为numpy数组
                import numpy as np
                img_array = np.array(image)
            elif isinstance(image, str):
                # 文件路径 - 使用PIL加载以支持中文路径
                from PIL import Image as PILImage
                import numpy as np
                pil_image = PILImage.open(image)
                img_array = np.array(pil_image)
            else:
                # 假设已经是numpy数组
                img_array = image
            
            # 识别
            result = ocr.readtext(img_array)
            
            # 解析结果
            ocr_results = []
            if result:
                for detection in result:
                    # EasyOCR返回格式: (bbox, text, confidence)
                    bbox = detection[0]
                    text = detection[1]
                    confidence = detection[2]
                    
                    # 计算边界框
                    x_coords = [p[0] for p in bbox]
                    y_coords = [p[1] for p in bbox]
                    x = min(x_coords)
                    y = min(y_coords)
                    width = max(x_coords) - x
                    height = max(y_coords) - y
                    
                    ocr_results.append(OCRResult(
                        text=text,
                        confidence=confidence,
                        bbox=(x, y, width, height),
                        page=1  # 单页识别时默认为1
                    ))
            
            return ocr_results
            
        except Exception as e:
            logger.error(f"EasyOCR识别失败: {e}")
            return []
    
    def _recognize_with_tesseract(self, image) -> List[OCRResult]:
        """使用Tesseract识别"""
        try:
            import pytesseract
            
            if isinstance(image, str):
                image = Image.open(image)
            
            # 获取详细数据
            data = pytesseract.image_to_data(
                image,
                lang="chi_sim+eng",
                output_type=pytesseract.Output.DICT
            )
            
            ocr_results = []
            n_boxes = len(data["text"])
            
            for i in range(n_boxes):
                text = data["text"][i].strip()
                conf = int(data["conf"][i])
                
                if text and conf > self.config.min_confidence * 100:
                    x = data["left"][i]
                    y = data["top"][i]
                    width = data["width"][i]
                    height = data["height"][i]
                    
                    ocr_results.append(OCRResult(
                        text=text,
                        confidence=conf / 100.0,
                        bbox=(x, y, width, height),
                        page=1
                    ))
            
            return ocr_results
            
        except Exception as e:
            logger.error(f"Tesseract识别失败: {e}")
            return []
    
    def _pdf_to_images(self, file_path: str) -> List:
        """PDF转图片"""
        try:
            import fitz  # PyMuPDF
            from PIL import Image
            import io
            
            doc = fitz.open(file_path)
            images = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # 渲染为图片
                mat = fitz.Matrix(2, 2)  # 2倍缩放以提高OCR质量
                pix = page.get_pixmap(matrix=mat)
                
                # 转换为PIL Image
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))
                
                images.append(image)
            
            doc.close()
            return images
            
        except Exception as e:
            logger.error(f"PDF转图片失败: {e}")
            return []
    
    def _preprocess_image(self, image) -> Image.Image:
        """图片预处理"""
        try:
            import cv2
            import numpy as np
            
            # PIL转OpenCV
            img_array = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # 自动旋转
            if self.config.auto_rotate:
                img_array = self._auto_rotate(img_array)
            
            # 去噪
            if self.config.denoise:
                img_array = cv2.fastNlMeansDenoisingColored(img_array, None, 10, 10, 7, 21)
            
            # 二值化
            if self.config.binarize:
                gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
                _, img_array = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)
            
            # OpenCV转PIL
            image = Image.fromarray(cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB))
            
            return image
            
        except Exception as e:
            logger.warning(f"图片预处理失败: {e}")
            return image
    
    def _auto_rotate(self, img_array) -> "numpy.ndarray":
        """自动旋转图片"""
        try:
            import cv2
            
            # 检测文字方向
            gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
            
            # 使用MSER检测文字区域
            mser = cv2.MSER_create()
            regions, _ = mser.detectRegions(gray)
            
            if len(regions) > 0:
                # 计算主要方向
                angles = []
                for region in regions[:10]:  # 只取前10个区域
                    if len(region) >= 5:
                        rect = cv2.minAreaRect(region)
                        angle = rect[2]
                        angles.append(angle)
                
                if angles:
                    median_angle = sorted(angles)[len(angles) // 2]
                    
                    # 如果角度较大，旋转图片
                    if abs(median_angle) > 5:
                        h, w = img_array.shape[:2]
                        center = (w // 2, h // 2)
                        M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                        rotated = cv2.warpAffine(img_array, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))
                        return rotated
            
            return img_array
            
        except Exception as e:
            logger.warning(f"自动旋转失败: {e}")
            return img_array
    
    def _build_document(self, ocr_results: List[OCRResult], images: List, file_path: str) -> ParsedDocument:
        """构建ParsedDocument"""
        # 按页分组
        page_results = {}
        for result in ocr_results:
            page = result.page
            if page not in page_results:
                page_results[page] = []
            page_results[page].append(result)
        
        # 创建TextBlock
        text_blocks = []
        all_text = []
        
        for page_num, results in page_results.items():
            # 按y坐标排序
            results = sorted(results, key=lambda r: (r.bbox[1], r.bbox[0]))
            
            for result in results:
                text_block = TextBlock(
                    text=result.text,
                    x=result.bbox[0],
                    y=result.bbox[1],
                    width=result.bbox[2],
                    height=result.bbox[3],
                    page=page_num,
                    confidence=result.confidence
                )
                text_blocks.append(text_block)
                all_text.append(result.text)
        
        # 创建ImageBlock
        image_blocks = []
        for i, image in enumerate(images):
            import io
            img_bytes = io.BytesIO()
            image.save(img_bytes, format="PNG")
            
            image_block = ImageBlock(
                image_data=img_bytes.getvalue(),
                x=0,
                y=0,
                width=image.width,
                height=image.height,
                page=i + 1,
                format="png"
            )
            image_blocks.append(image_block)
        
        raw_text = "\n".join(all_text)
        
        return ParsedDocument(
            raw_text=clean_text(raw_text),
            text_blocks=text_blocks,
            image_blocks=image_blocks,
            pdf_type=PDFType.SCANNED,
            page_count=len(images),
            metadata={
                "engine": "easyocr",
                "ocr_results_count": len(ocr_results)
            }
        )


# 单例模式
_ocr_engine = None

def get_ocr_engine() -> OCREngine:
    """获取OCR引擎单例"""
    global _ocr_engine
    if _ocr_engine is None:
        _ocr_engine = OCREngine()
    return _ocr_engine
