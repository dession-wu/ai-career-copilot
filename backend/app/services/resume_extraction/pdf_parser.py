"""
多引擎PDF解析器
支持pdfplumber、pymupdf、marker等多种解析引擎
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from .models import (
    ParsedDocument, TextBlock, ImageBlock, PDFType, DocumentStructure
)
from .config import parser_config
from .utils import clean_text

logger = logging.getLogger(__name__)


class PDFParser:
    """多引擎PDF解析器"""
    
    def __init__(self):
        self.config = parser_config
    
    def parse(self, file_path: str) -> ParsedDocument:
        """
        智能解析PDF文件
        
        根据PDF类型自动选择最佳解析引擎：
        1. 文本型PDF -> pdfplumber (速度快)
        2. 复杂布局 -> marker (布局保留好)
        3. 扫描件 -> OCR (需要图像识别)
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            ParsedDocument: 解析后的文档对象
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {file_path}")
        
        # 检测PDF类型
        pdf_type = self._detect_pdf_type(str(file_path))
        logger.info(f"检测到PDF类型: {pdf_type.value}")
        
        # 根据类型选择解析引擎
        if pdf_type == PDFType.SCANNED:
            return self._parse_with_ocr(str(file_path))
        
        # 尝试多个引擎
        for engine in self.config.engine_priority:
            try:
                if engine == "pdfplumber":
                    return self._parse_with_pdfplumber(str(file_path), pdf_type)
                elif engine == "pymupdf":
                    return self._parse_with_pymupdf(str(file_path), pdf_type)
                elif engine == "marker":
                    return self._parse_with_marker(str(file_path), pdf_type)
            except Exception as e:
                logger.warning(f"引擎 {engine} 解析失败: {e}")
                continue
        
        # 所有引擎都失败，返回空文档
        logger.error("所有PDF解析引擎都失败")
        return ParsedDocument(
            raw_text="",
            text_blocks=[],
            image_blocks=[],
            pdf_type=pdf_type,
            page_count=0,
            metadata={"error": "所有解析引擎都失败"}
        )
    
    def _detect_pdf_type(self, file_path: str) -> PDFType:
        """
        检测PDF类型（文本型/扫描件/混合型）
        
        检测方法：
        1. 检查是否包含可提取的文本
        2. 检查图片密度
        3. 检查字体信息
        """
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(file_path)
            total_pages = len(doc)
            
            text_chars = 0
            image_count = 0
            has_fonts = False
            
            for page in doc:
                # 统计文本字符
                text = page.get_text()
                text_chars += len(text.strip())
                
                # 统计图片
                image_list = page.get_images()
                image_count += len(image_list)
                
                # 检查字体
                fonts = page.get_fonts()
                if fonts:
                    has_fonts = True
            
            doc.close()
            
            # 计算文本密度
            if total_pages > 0:
                avg_text_per_page = text_chars / total_pages
                image_density = image_count / total_pages
            else:
                avg_text_per_page = 0
                image_density = 0
            
            # 判断PDF类型
            if not has_fonts and image_density > self.config.scanned_pdf_threshold:
                return PDFType.SCANNED
            elif avg_text_per_page < 100 and image_density > 0.5:
                return PDFType.MIXED
            else:
                return PDFType.TEXT
                
        except Exception as e:
            logger.warning(f"PDF类型检测失败: {e}")
            return PDFType.UNKNOWN
    
    def _parse_with_pdfplumber(self, file_path: str, pdf_type: PDFType) -> ParsedDocument:
        """使用pdfplumber解析PDF"""
        import pdfplumber
        
        logger.info(f"使用pdfplumber解析: {file_path}")
        
        text_blocks = []
        image_blocks = []
        all_text = []
        
        with pdfplumber.open(file_path) as pdf:
            page_count = len(pdf.pages)
            
            for page_num, page in enumerate(pdf.pages, 1):
                # 提取文本块（保留布局信息）
                if self.config.extract_layout:
                    words = page.extract_words(
                        keep_blank_chars=True,
                        x_tolerance=3,
                        y_tolerance=3
                    )
                    
                    # 将words聚合成文本块
                    lines = self._cluster_words_to_lines(words)
                    for line in lines:
                        text_block = TextBlock(
                            text=line["text"],
                            x=line["x0"],
                            y=line["top"],
                            width=line["x1"] - line["x0"],
                            height=line["bottom"] - line["top"],
                            page=page_num,
                            font_name=line.get("fontname"),
                            font_size=line.get("size"),
                            is_bold="Bold" in str(line.get("fontname", "")),
                        )
                        text_blocks.append(text_block)
                        all_text.append(line["text"])
                else:
                    # 简单文本提取
                    text = page.extract_text() or ""
                    all_text.append(text)
                
                # 提取图片
                if self.config.extract_images:
                    # pdfplumber不直接支持图片提取，需要配合其他库
                    pass
                
                # 提取表格
                if self.config.extract_tables:
                    tables = page.extract_tables()
                    for table in tables:
                        # 将表格转换为文本
                        table_text = self._table_to_text(table)
                        all_text.append(table_text)
        
        raw_text = "\n".join(all_text)
        
        return ParsedDocument(
            raw_text=clean_text(raw_text),
            text_blocks=text_blocks,
            image_blocks=image_blocks,
            pdf_type=pdf_type,
            page_count=page_count,
            metadata={"engine": "pdfplumber"}
        )
    
    def _parse_with_pymupdf(self, file_path: str, pdf_type: PDFType) -> ParsedDocument:
        """使用PyMuPDF解析PDF"""
        import fitz
        
        logger.info(f"使用PyMuPDF解析: {file_path}")
        
        text_blocks = []
        image_blocks = []
        all_text = []
        
        doc = fitz.open(file_path)
        page_count = len(doc)
        
        for page_num in range(page_count):
            page = doc[page_num]
            
            # 提取文本块
            if self.config.extract_layout:
                blocks = page.get_text("dict")["blocks"]
                for block in blocks:
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                text_block = TextBlock(
                                    text=span["text"],
                                    x=span["bbox"][0],
                                    y=span["bbox"][1],
                                    width=span["bbox"][2] - span["bbox"][0],
                                    height=span["bbox"][3] - span["bbox"][1],
                                    page=page_num + 1,
                                    font_name=span.get("font"),
                                    font_size=span.get("size"),
                                    is_bold=span.get("flags", 0) & 2 ** 4 != 0,
                                )
                                text_blocks.append(text_block)
                                all_text.append(span["text"])
            else:
                text = page.get_text()
                all_text.append(text)
            
            # 提取图片
            if self.config.extract_images:
                image_list = page.get_images(full=True)
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    image_block = ImageBlock(
                        image_data=image_bytes,
                        x=0,  # 图片位置信息需要额外计算
                        y=0,
                        width=base_image.get("width", 0),
                        height=base_image.get("height", 0),
                        page=page_num + 1,
                        format=base_image["ext"],
                    )
                    image_blocks.append(image_block)
        
        doc.close()
        
        raw_text = "\n".join(all_text)
        
        return ParsedDocument(
            raw_text=clean_text(raw_text),
            text_blocks=text_blocks,
            image_blocks=image_blocks,
            pdf_type=pdf_type,
            page_count=page_count,
            metadata={"engine": "pymupdf"}
        )
    
    def _parse_with_marker(self, file_path: str, pdf_type: PDFType) -> ParsedDocument:
        """使用marker解析PDF（适用于复杂布局）"""
        try:
            from marker.convert import convert_single_pdf
            from marker.models import load_all_models
            
            logger.info(f"使用marker解析: {file_path}")
            
            # 加载模型（只需加载一次）
            # 注意：marker较重，实际使用时可以缓存模型
            model_lst = load_all_models()
            
            # 转换PDF
            full_text, images, out_meta = convert_single_pdf(file_path, model_lst)
            
            # 创建文本块
            text_blocks = []
            lines = full_text.split('\n')
            for i, line in enumerate(lines):
                if line.strip():
                    text_blocks.append(TextBlock(
                        text=line,
                        x=0,
                        y=i * 20,  # 估算位置
                        width=100,
                        height=20,
                        page=1,
                    ))
            
            # 创建图片块
            image_blocks = []
            for img_name, img_data in images.items():
                image_blocks.append(ImageBlock(
                    image_data=img_data,
                    x=0,
                    y=0,
                    width=0,
                    height=0,
                    page=1,
                ))
            
            return ParsedDocument(
                raw_text=clean_text(full_text),
                text_blocks=text_blocks,
                image_blocks=image_blocks,
                pdf_type=pdf_type,
                page_count=out_meta.get("page_count", 1),
                metadata={"engine": "marker", "meta": out_meta}
            )
            
        except ImportError:
            logger.warning("marker未安装，跳过")
            raise
        except Exception as e:
            logger.error(f"marker解析失败: {e}")
            raise
    
    def _parse_with_ocr(self, file_path: str) -> ParsedDocument:
        """使用OCR解析扫描件PDF"""
        logger.info(f"使用OCR解析扫描件: {file_path}")
        
        # 这里会调用OCR引擎，在ocr_engine.py中实现
        # 暂时返回占位符，实际使用时需要集成OCR
        from .ocr_engine import OCREngine
        
        ocr_engine = OCREngine()
        return ocr_engine.parse_pdf(file_path)
    
    def _cluster_words_to_lines(self, words: List[Dict]) -> List[Dict]:
        """将words聚合成行"""
        if not words:
            return []
        
        # 按y坐标排序
        words = sorted(words, key=lambda w: (round(w["top"], 1), w["x0"]))
        
        lines = []
        current_line = []
        current_y = None
        
        for word in words:
            y = round(word["top"], 1)
            
            if current_y is None or abs(y - current_y) < 3:
                current_line.append(word)
                current_y = y
            else:
                # 新行
                if current_line:
                    lines.append(self._merge_words_to_line(current_line))
                current_line = [word]
                current_y = y
        
        # 处理最后一行
        if current_line:
            lines.append(self._merge_words_to_line(current_line))
        
        return lines
    
    def _merge_words_to_line(self, words: List[Dict]) -> Dict:
        """将words合并成一行"""
        if not words:
            return {}
        
        words = sorted(words, key=lambda w: w["x0"])
        
        text = " ".join(w["text"] for w in words)
        x0 = words[0]["x0"]
        x1 = words[-1]["x1"]
        top = min(w["top"] for w in words)
        bottom = max(w["bottom"] for w in words)
        
        # 获取最常见的字体
        fontnames = [w.get("fontname", "") for w in words if w.get("fontname")]
        fontname = max(set(fontnames), key=fontnames.count) if fontnames else None
        
        sizes = [w.get("size", 0) for w in words if w.get("size")]
        size = sum(sizes) / len(sizes) if sizes else None
        
        return {
            "text": text,
            "x0": x0,
            "x1": x1,
            "top": top,
            "bottom": bottom,
            "fontname": fontname,
            "size": size,
        }
    
    def _table_to_text(self, table: List[List[str]]) -> str:
        """将表格转换为文本"""
        lines = []
        for row in table:
            line = " | ".join(str(cell or "") for cell in row)
            lines.append(line)
        return "\n".join(lines)


# 单例模式
_pdf_parser = None

def get_pdf_parser() -> PDFParser:
    """获取PDF解析器单例"""
    global _pdf_parser
    if _pdf_parser is None:
        _pdf_parser = PDFParser()
    return _pdf_parser
