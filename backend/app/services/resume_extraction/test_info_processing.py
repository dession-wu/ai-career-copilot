"""
信息加工处理模块测试
验证技能识别、章节分类、项目经历、个人信息提取的修复效果
"""

import unittest
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# 使用绝对导入
from backend.app.services.resume_extraction.config import skill_config, layout_config
from backend.app.services.resume_extraction.utils import extract_email, extract_phone
from backend.app.services.resume_extraction.rule_engine import RuleEngine
from backend.app.services.resume_extraction.layout_analyzer import LayoutAnalyzer
from backend.app.services.resume_extraction.models import ParsedDocument, PDFType, Section, SectionType


class TestSkillRecognition(unittest.TestCase):
    """测试技能识别修复"""
    
    def setUp(self):
        self.rule_engine = RuleEngine()
    
    def test_skill_aliases(self):
        """测试技能别名映射"""
        # PS 应该映射到 Photoshop
        text = "熟练掌握 PS、PR、AI 等设计软件"
        skills = self.rule_engine._parse_skill_list(text)
        skill_names = [s.lower() for s in skills]
        self.assertIn('ps', skill_names)
    
    def test_multiple_separators(self):
        """测试多种分隔符"""
        # 中文顿号
        text1 = "Python、Java、C++"
        skills1 = self.rule_engine._parse_skill_list(text1)
        self.assertEqual(len(skills1), 3)
        
        # 英文逗号
        text2 = "Python, Java, C++"
        skills2 = self.rule_engine._parse_skill_list(text2)
        self.assertEqual(len(skills2), 3)
        
        # 混合分隔符
        text3 = "Python、Java, C++; SQL"
        skills3 = self.rule_engine._parse_skill_list(text3)
        self.assertGreaterEqual(len(skills3), 3)
    
    def test_skill_categories(self):
        """测试技能分类"""
        # 检查关键技能是否在词库中
        categories = skill_config.skill_categories
        
        # MATLAB
        prog_keywords = categories["programming_languages"]["keywords"]
        self.assertIn("MATLAB", prog_keywords)
        
        # Tableau
        data_keywords = categories["data_analysis"]["keywords"]
        self.assertIn("Tableau", data_keywords)
        
        # ArcGIS
        gis_keywords = categories["gis"]["keywords"]
        self.assertIn("ArcGIS", gis_keywords)
        
        # Microsoft Office
        office_keywords = categories["office"]["keywords"]
        self.assertIn("Microsoft Office", office_keywords)
    
    def test_skill_normalization(self):
        """测试技能名称标准化"""
        # 测试别名映射
        normalized = self.rule_engine._normalize_skill_name("ps")
        self.assertEqual(normalized, "Photoshop")
        
        normalized = self.rule_engine._normalize_skill_name("pr")
        self.assertEqual(normalized, "Premiere")
        
        normalized = self.rule_engine._normalize_skill_name("R语言")
        self.assertEqual(normalized, "R")


class TestSectionClassification(unittest.TestCase):
    """测试章节分类优化"""
    
    def setUp(self):
        self.layout_analyzer = LayoutAnalyzer()
    
    def test_section_keywords(self):
        """测试章节关键词识别"""
        keywords = layout_config.section_keywords
        
        # 教育背景关键词
        edu_keywords = keywords["education"]
        self.assertIn("教育背景", edu_keywords)
        self.assertIn("教 育 背 景", edu_keywords)  # 带空格版本
        
        # 工作经历关键词
        work_keywords = keywords["work_experience"]
        self.assertIn("工作实践", work_keywords)
        self.assertIn("工 作 实 践", work_keywords)
        
        # 项目经历关键词
        proj_keywords = keywords["projects"]
        self.assertIn("项目经历", proj_keywords)
        self.assertIn("项 目 经 历", proj_keywords)
    
    def test_section_validation(self):
        """测试章节内容验证"""
        # 测试教育经历验证
        edu_section = Section(
            section_type=SectionType.EDUCATION,
            title="教育背景",
            content="北京大学 本科 计算机科学",
            start_line=10,
            end_line=20
        )
        is_valid, suggested = self.layout_analyzer._validate_section_content(edu_section)
        self.assertTrue(is_valid)
        
        # 测试工作经历误入教育
        work_as_edu = Section(
            section_type=SectionType.EDUCATION,
            title="工作经历",
            content="阿里巴巴 工程师 2020-2024",
            start_line=10,
            end_line=20
        )
        is_valid, suggested = self.layout_analyzer._validate_section_content(work_as_edu)
        self.assertFalse(is_valid)
        self.assertEqual(suggested, SectionType.WORK_EXPERIENCE)


class TestProjectIntegration(unittest.TestCase):
    """测试项目经历整合"""
    
    def setUp(self):
        self.layout_analyzer = LayoutAnalyzer()
    
    def test_project_merge(self):
        """测试项目合并"""
        entries = [
            {"name": "电商平台", "start_date": "2020", "description": "负责前端开发"},
            {"name": "电商平台", "start_date": "2020", "description": "使用React技术栈"},
            {"name": "数据可视化", "start_date": "2021", "description": "负责数据分析"},
        ]
        
        merged = self.layout_analyzer._merge_related_projects(entries)
        # 前两个应该合并
        self.assertEqual(len(merged), 2)
        self.assertIn("负责前端开发", merged[0]["description"])
        self.assertIn("使用React技术栈", merged[0]["description"])
    
    def test_should_merge_projects(self):
        """测试项目合并判断"""
        # 相同名称应该合并
        entry1 = {"name": "测试项目", "start_date": "2020"}
        entry2 = {"name": "测试项目", "start_date": "2020"}
        self.assertTrue(self.layout_analyzer._should_merge_projects(entry1, entry2))
        
        # 不同名称不应该合并
        entry3 = {"name": "项目A", "start_date": "2020"}
        entry4 = {"name": "项目B", "start_date": "2021"}
        self.assertFalse(self.layout_analyzer._should_merge_projects(entry3, entry4))


class TestPersonalInfoExtraction(unittest.TestCase):
    """测试个人信息提取增强"""
    
    def test_email_with_separators(self):
        """测试带分隔符的邮箱提取"""
        # 标准格式
        text1 = "联系邮箱：test@example.com"
        self.assertEqual(extract_email(text1), "test@example.com")
        
        # 带特殊分隔符
        text2 = "手机：13800138000丨邮箱：test@example.com丨地址：北京"
        self.assertEqual(extract_email(text2), "test@example.com")
        
        # 带竖线分隔符
        text3 = "name@example.com | 13800138000"
        self.assertEqual(extract_email(text3), "name@example.com")
    
    def test_phone_extraction(self):
        """测试电话提取"""
        text = "联系电话：13800138000"
        self.assertEqual(extract_phone(text), "13800138000")
    
    def test_multi_line_info(self):
        """测试多行个人信息"""
        text = """吴烨
手机：18133004892丨邮箱：18133004892@163.com
北京科技大学"""
        
        email = extract_email(text)
        phone = extract_phone(text)
        
        self.assertEqual(email, "18133004892@163.com")
        self.assertEqual(phone, "18133004892")


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def setUp(self):
        self.rule_engine = RuleEngine()
        self.layout_analyzer = LayoutAnalyzer()
    
    def test_full_resume_text(self):
        """测试完整简历文本提取"""
        resume_text = """吴烨
手机：18133004892丨邮箱：18133004892@163.com

教育背景
2020.09-2024.07 北京科技大学（3.6/4.0） 环境工程（本科）

技能
熟练掌握MATLAB、Python、R语言、Tableau、Microsoft Office、PS/PR、ArcGIS、MySQL

项目经历
北京市生活垃圾管理项目
负责数据分析和可视化，使用Python和Tableau

中国水泥行业碳排放项目
负责数据收集和模型建立"""
        
        # 创建ParsedDocument
        document = ParsedDocument(
            raw_text=resume_text,
            text_blocks=[],
            image_blocks=[],
            pdf_type=PDFType.TEXT,
            page_count=1
        )
        
        # 版面分析
        structure = self.layout_analyzer.analyze(document)
        document.structure = structure
        
        # 信息提取
        extracted_data = self.rule_engine.extract(document, structure)
        
        # 验证个人信息
        personal_info = extracted_data["personal_info"]
        self.assertEqual(personal_info.name, "吴烨")
        self.assertEqual(personal_info.email, "18133004892@163.com")
        self.assertEqual(personal_info.phone, "18133004892")
        
        # 验证技能
        skills = extracted_data["skills"]
        skill_names = [s.name for s in skills]
        
        # 检查关键技能是否被识别
        expected_skills = ["MATLAB", "Python", "R", "Tableau", "ArcGIS", "MySQL"]
        for skill in expected_skills:
            found = any(skill.lower() in name.lower() for name in skill_names)
            self.assertTrue(found, f"技能 {skill} 应该被识别")
        
        # 验证章节分类
        section_types = [s.section_type for s in structure.sections]
        self.assertIn(SectionType.EDUCATION, section_types)
        self.assertIn(SectionType.PROJECTS, section_types)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestSkillRecognition))
    suite.addTests(loader.loadTestsFromTestCase(TestSectionClassification))
    suite.addTests(loader.loadTestsFromTestCase(TestProjectIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestPersonalInfoExtraction))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
