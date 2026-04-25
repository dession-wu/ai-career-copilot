"""
文件解析器
支持图片OCR和PDF解析
"""

import os

# 在导入easyocr之前设置模型目录环境变量 - 使用项目目录
EASYOCR_MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'models', 'easyocr')
os.environ['EASYOCR_MODULE_PATH'] = EASYOCR_MODEL_PATH
os.environ['MODULE_PATH'] = EASYOCR_MODEL_PATH

import tempfile
from typing import Optional, Tuple
from pathlib import Path


class FileParser:
    """文件解析基类"""
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
    
    def parse(self, file_path: str) -> Tuple[bool, str, Optional[str]]:
        """
        解析文件
        
        Returns:
            (success, text, error_message)
        """
        raise NotImplementedError


class ImageOCRParser(FileParser):
    """图片OCR解析器 - 使用EasyOCR"""
    
    def __init__(self):
        super().__init__()
        self._ocr_engine = None
    
    def _get_ocr_engine(self):
        """获取OCR引擎（懒加载）"""
        if self._ocr_engine is None:
            try:
                import easyocr
                import os
                from pathlib import Path
                
                # 模型目录已在文件顶部设置环境变量
                model_dir = r"D:\AI-Career-Co-pilot\models\easyocr"
                os.makedirs(model_dir, exist_ok=True)
                
                # 使用EasyOCR，支持中文和英文
                print(f"[OCR] 初始化EasyOCR，模型目录: {model_dir}")
                
                self._ocr_engine = easyocr.Reader(
                    ['ch_sim', 'en'],
                    download_enabled=True
                )
                print("[OCR] EasyOCR初始化成功")
            except Exception as e:
                print(f"[OCR] EasyOCR初始化失败: {e}")
                import traceback
                traceback.print_exc()
                self._ocr_engine = "fallback"
        return self._ocr_engine
    
    def parse(self, file_path: str) -> Tuple[bool, str, Optional[str]]:
        """
        解析图片文件，提取文字
        
        Returns:
            (success, extracted_text, error_message)
        """
        try:
            engine = self._get_ocr_engine()
            
            if engine == "fallback":
                return False, "", "OCR引擎初始化失败"
            
            # 使用PIL加载图片（支持中文路径），然后转换为numpy数组
            from PIL import Image
            import numpy as np
            
            pil_image = Image.open(file_path)
            img_array = np.array(pil_image)
            
            # 使用EasyOCR识别
            result = engine.readtext(img_array)
            
            # 提取文字
            text_lines = []
            if result:
                for detection in result:
                    # EasyOCR返回格式: (bbox, text, confidence)
                    text = detection[1]
                    text_lines.append(text)
            
            extracted_text = '\n'.join(text_lines)
            return True, extracted_text, None
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, "", f"OCR解析失败: {str(e)}"


class PDFParser(FileParser):
    """PDF解析器"""
    
    def parse(self, file_path: str) -> Tuple[bool, str, Optional[str]]:
        """
        解析PDF文件，提取文字
        
        Returns:
            (success, extracted_text, error_message)
        """
        try:
            # 尝试使用pdfplumber
            try:
                import pdfplumber
                return self._parse_with_pdfplumber(file_path)
            except ImportError:
                pass
            
            # 尝试使用PyMuPDF
            try:
                import fitz  # PyMuPDF
                return self._parse_with_pymupdf(file_path)
            except ImportError:
                pass
            
            # 如果都不可用，返回错误
            return False, "", "PDF解析库未安装，请安装pdfplumber或PyMuPDF"
            
        except Exception as e:
            return False, "", f"PDF解析失败: {str(e)}"
    
    def _parse_with_pdfplumber(self, file_path: str) -> Tuple[bool, str, Optional[str]]:
        """使用pdfplumber解析PDF"""
        import pdfplumber
        
        text_lines = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_lines.append(text)
        
        extracted_text = '\n\n'.join(text_lines)
        return True, extracted_text, None
    
    def _parse_with_pymupdf(self, file_path: str) -> Tuple[bool, str, Optional[str]]:
        """使用PyMuPDF解析PDF"""
        import fitz
        
        text_lines = []
        with fitz.open(file_path) as pdf:
            for page_num in range(len(pdf)):
                page = pdf[page_num]
                text = page.get_text()
                if text:
                    text_lines.append(text)
        
        extracted_text = '\n\n'.join(text_lines)
        return True, extracted_text, None


class TextExtractor:
    """文本提取器工厂"""
    
    @staticmethod
    def get_parser(file_path: str) -> Optional[FileParser]:
        """
        根据文件类型获取对应的解析器
        
        Args:
            file_path: 文件路径
            
        Returns:
            对应的解析器实例
        """
        ext = Path(file_path).suffix.lower()
        
        if ext in ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif']:
            return ImageOCRParser()
        elif ext == '.pdf':
            return PDFParser()
        else:
            return None
    
    @staticmethod
    def extract_text(file_path: str) -> Tuple[bool, str, Optional[str]]:
        """
        提取文件中的文本
        
        Args:
            file_path: 文件路径
            
        Returns:
            (success, extracted_text, error_message)
        """
        parser = TextExtractor.get_parser(file_path)
        
        if parser is None:
            return False, "", f"不支持的文件格式: {Path(file_path).suffix}"
        
        return parser.parse(file_path)


class FileValidator:
    """文件验证器"""
    
    @staticmethod
    def validate(file_path: str, max_size: int = 10 * 1024 * 1024) -> Tuple[bool, Optional[str]]:
        """
        验证文件
        
        Args:
            file_path: 文件路径
            max_size: 最大文件大小（字节）
            
        Returns:
            (is_valid, error_message)
        """
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return False, "文件不存在"
        
        # 检查文件大小
        file_size = os.path.getsize(file_path)
        if file_size > max_size:
            return False, f"文件大小超过限制（最大{max_size // 1024 // 1024}MB）"
        
        # 检查文件类型
        ext = Path(file_path).suffix.lower()
        allowed_extensions = ['.png', '.jpg', '.jpeg', '.webp', '.pdf', '.bmp', '.gif']
        
        if ext not in allowed_extensions:
            return False, f"不支持的文件格式: {ext}"
        
        return True, None
    
    @staticmethod
    def get_file_type(file_path: str) -> str:
        """获取文件类型"""
        ext = Path(file_path).suffix.lower()
        
        if ext in ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif']:
            return "image"
        elif ext == '.pdf':
            return "pdf"
        else:
            return "unknown"
