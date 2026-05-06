"""
PDF导出服务 - 将简历导出为专业PDF格式

支持：
1. Markdown转PDF
2. 多种专业模板
3. 自定义样式
"""

import os
import re
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class PDFService:
    """PDF导出服务"""
    
    # 预定义模板样式
    TEMPLATES = {
        "modern": {
            "name": "现代简约",
            "description": "简洁现代的简历模板，适合技术和创意行业",
            "colors": {
                "primary": "#2563eb",      # 主色调：蓝色
                "secondary": "#64748b",    # 次要色：灰色
                "text": "#1e293b",         # 文字色：深灰
                "light": "#f8fafc",        # 浅色背景
                "border": "#e2e8f0"        # 边框色
            },
            "fonts": {
                "heading": "Helvetica-Bold",
                "body": "Helvetica",
                "chinese": "SimHei"  # 中文字体
            }
        },
        "classic": {
            "name": "经典专业",
            "description": "传统专业简历模板，适合金融、咨询等行业",
            "colors": {
                "primary": "#1e293b",      # 主色调：深蓝黑
                "secondary": "#475569",    # 次要色：中灰
                "text": "#0f172a",         # 文字色：近黑
                "light": "#f1f5f9",        # 浅色背景
                "border": "#cbd5e1"        # 边框色
            },
            "fonts": {
                "heading": "Times-Bold",
                "body": "Times-Roman",
                "chinese": "SimSun"
            }
        },
        "creative": {
            "name": "创意设计",
            "description": "富有创意的简历模板，适合设计、艺术类职位",
            "colors": {
                "primary": "#7c3aed",      # 主色调：紫色
                "secondary": "#a78bfa",    # 次要色：浅紫
                "text": "#1e1b4b",         # 文字色：深紫
                "light": "#f5f3ff",        # 浅色背景
                "border": "#ddd6fe"        # 边框色
            },
            "fonts": {
                "heading": "Helvetica-Bold",
                "body": "Helvetica",
                "chinese": "SimHei"
            }
        }
    }
    
    def __init__(self):
        self.templates_dir = Path(__file__).parent.parent / "templates" / "pdf"
        self.templates_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_pdf(
        self,
        resume_content: str,
        template: str = "modern",
        output_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成PDF简历
        
        Args:
            resume_content: Markdown格式的简历内容
            template: 模板名称 (modern/classic/creative)
            output_path: 输出路径（可选）
            metadata: 元数据（可选）
            
        Returns:
            Dict: 包含PDF路径、文件名、生成时间等信息
        """
        try:
            # 尝试使用 WeasyPrint
            return self._generate_with_weasyprint(
                resume_content, template, output_path, metadata
            )
        except ImportError:
            logger.warning("WeasyPrint not available, trying Playwright")
            try:
                return self._generate_with_playwright(
                    resume_content, template, output_path, metadata
                )
            except ImportError:
                logger.error("No PDF generation library available")
                return self._generate_fallback(resume_content, output_path)
    
    def _generate_with_weasyprint(
        self,
        resume_content: str,
        template: str,
        output_path: Optional[str],
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """使用 WeasyPrint 生成 PDF"""
        from weasyprint import HTML, CSS
        import markdown
        
        # 获取模板配置
        template_config = self.TEMPLATES.get(template, self.TEMPLATES["modern"])
        
        # 转换 Markdown 为 HTML
        html_content = markdown.markdown(
            resume_content,
            extensions=['tables', 'fenced_code', 'toc']
        )
        
        # 构建完整 HTML
        full_html = self._build_html_with_style(
            html_content,
            template_config,
            metadata
        )
        
        # 生成输出路径
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"resume_{timestamp}.pdf"
            output_path = str(self.templates_dir / filename)
        
        # 生成 PDF
        HTML(string=full_html).write_pdf(output_path)
        
        return {
            "success": True,
            "file_path": output_path,
            "filename": os.path.basename(output_path),
            "template": template,
            "generated_at": datetime.utcnow().isoformat(),
            "method": "weasyprint"
        }
    
    def _generate_with_playwright(
        self,
        resume_content: str,
        template: str,
        output_path: Optional[str],
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """使用 Playwright 生成 PDF"""
        from playwright.sync_api import sync_playwright
        import markdown
        
        # 获取模板配置
        template_config = self.TEMPLATES.get(template, self.TEMPLATES["modern"])
        
        # 转换 Markdown 为 HTML
        html_content = markdown.markdown(
            resume_content,
            extensions=['tables', 'fenced_code', 'toc']
        )
        
        # 构建完整 HTML
        full_html = self._build_html_with_style(
            html_content,
            template_config,
            metadata
        )
        
        # 生成输出路径
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"resume_{timestamp}.pdf"
            output_path = str(self.templates_dir / filename)
        
        # 使用 Playwright 生成 PDF
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(full_html)
            page.pdf(
                path=output_path,
                format="A4",
                print_background=True,
                margin={
                    "top": "20mm",
                    "bottom": "20mm",
                    "left": "20mm",
                    "right": "20mm"
                }
            )
            browser.close()
        
        return {
            "success": True,
            "file_path": output_path,
            "filename": os.path.basename(output_path),
            "template": template,
            "generated_at": datetime.utcnow().isoformat(),
            "method": "playwright"
        }
    
    def _build_html_with_style(
        self,
        html_content: str,
        template_config: Dict[str, Any],
        metadata: Optional[Dict[str, Any]]
    ) -> str:
        """构建带样式的完整 HTML"""
        colors = template_config["colors"]
        
        # 提取标题（如果存在）
        title = "简历"
        if metadata and "name" in metadata:
            title = f"{metadata['name']} - 简历"
        
        html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        @page {{
            size: A4;
            margin: 20mm;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: {colors['text']};
            background: white;
        }}
        
        .resume-container {{
            max-width: 210mm;
            margin: 0 auto;
            padding: 0;
        }}
        
        /* 标题样式 */
        h1 {{
            font-size: 24pt;
            font-weight: bold;
            color: {colors['primary']};
            margin-bottom: 8pt;
            border-bottom: 2pt solid {colors['primary']};
            padding-bottom: 8pt;
        }}
        
        h2 {{
            font-size: 14pt;
            font-weight: bold;
            color: {colors['primary']};
            margin-top: 16pt;
            margin-bottom: 8pt;
            border-bottom: 1pt solid {colors['border']};
            padding-bottom: 4pt;
        }}
        
        h3 {{
            font-size: 12pt;
            font-weight: bold;
            color: {colors['text']};
            margin-top: 12pt;
            margin-bottom: 4pt;
        }}
        
        /* 段落和列表 */
        p {{
            margin-bottom: 8pt;
            text-align: justify;
        }}
        
        ul, ol {{
            margin-left: 20pt;
            margin-bottom: 8pt;
        }}
        
        li {{
            margin-bottom: 4pt;
        }}
        
        /* 强调文本 */
        strong {{
            color: {colors['primary']};
            font-weight: bold;
        }}
        
        em {{
            color: {colors['secondary']};
            font-style: italic;
        }}
        
        /* 代码和引用 */
        code {{
            background: {colors['light']};
            padding: 2pt 4pt;
            border-radius: 3pt;
            font-family: "Courier New", monospace;
            font-size: 10pt;
        }}
        
        blockquote {{
            border-left: 3pt solid {colors['primary']};
            padding-left: 12pt;
            margin: 12pt 0;
            color: {colors['secondary']};
            font-style: italic;
        }}
        
        /* 表格 */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 12pt 0;
        }}
        
        th, td {{
            border: 1pt solid {colors['border']};
            padding: 6pt;
            text-align: left;
        }}
        
        th {{
            background: {colors['light']};
            font-weight: bold;
            color: {colors['primary']};
        }}
        
        /* 链接 */
        a {{
            color: {colors['primary']};
            text-decoration: none;
        }}
        
        /* 分隔线 */
        hr {{
            border: none;
            border-top: 1pt solid {colors['border']};
            margin: 16pt 0;
        }}
        
        /* 打印优化 */
        @media print {{
            body {{
                print-color-adjust: exact;
                -webkit-print-color-adjust: exact;
            }}
        }}
    </style>
</head>
<body>
    <div class="resume-container">
        {html_content}
    </div>
</body>
</html>"""
        
        return html_template
    
    def _generate_fallback(
        self,
        resume_content: str,
        output_path: Optional[str]
    ) -> Dict[str, Any]:
        """降级方案：返回原始Markdown"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"resume_{timestamp}.md"
            output_path = str(self.templates_dir / filename)
        
        # 保存为 Markdown
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(resume_content)
        
        return {
            "success": False,
            "file_path": output_path,
            "filename": os.path.basename(output_path),
            "template": "raw_markdown",
            "generated_at": datetime.utcnow().isoformat(),
            "method": "fallback",
            "message": "PDF生成库未安装，已保存为Markdown格式。请安装weasyprint或playwright以生成PDF。"
        }
    
    def get_available_templates(self) -> List[Dict[str, str]]:
        """获取可用模板列表"""
        return [
            {
                "id": key,
                "name": config["name"],
                "description": config["description"]
            }
            for key, config in self.TEMPLATES.items()
        ]
    
    def preview_template(
        self,
        template: str,
        sample_content: Optional[str] = None
    ) -> str:
        """
        生成模板预览 HTML
        
        Returns:
            str: HTML字符串
        """
        template_config = self.TEMPLATES.get(template, self.TEMPLATES["modern"])
        
        if not sample_content:
            sample_content = """# 张三
**高级软件工程师** | zhangsan@example.com | 138-0000-0000

## 工作经历

### ABC科技有限公司 | 高级软件工程师
*2020年6月 - 至今*

- 负责微服务架构设计与实现，服务QPS提升300%
- 带领5人团队完成核心业务系统重构

## 技能

- Python, Java, Go
- Kubernetes, Docker
- MySQL, Redis, MongoDB
"""
        
        import markdown
        html_content = markdown.markdown(
            sample_content,
            extensions=['tables', 'fenced_code']
        )
        
        return self._build_html_with_style(html_content, template_config, {"name": "张三"})


# 单例模式
_pdf_service = None

def get_pdf_service() -> PDFService:
    """获取PDF服务单例"""
    global _pdf_service
    if _pdf_service is None:
        _pdf_service = PDFService()
    return _pdf_service
